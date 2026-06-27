from fastapi import APIRouter, Query
from typing import Optional
from .. import db
import json
from ..services.event_engine import get_event_detail_by_id

router = APIRouter()

def wrap_response(data=None, error=None, meta=None):
    return {
        "success": error is None,
        "data": data,
        "error": error,
        "meta": meta or {}
    }

@router.get("")
def get_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = None
):
    where = "WHERE 1=1"
    params = []
    if event_type:
        where += " AND event_type = ?"
        params.append(event_type)
        
    total = db.row(f"SELECT COUNT(*) as count FROM event_instances {where}", tuple(params))["count"]
    
    offset = (page - 1) * page_size
    query = (
        f"SELECT *, event_id AS id FROM event_instances {where} "
        "ORDER BY occurred_at DESC LIMIT ? OFFSET ?"
    )
    events = []
    for event in db.rows(query, tuple(params + [page_size, offset])):
        event_dict = dict(event)
        impacts = db.rows(
            """
            SELECT i.*, k.name AS commodity
            FROM event_impacts i
            JOIN kg_entities k ON k.entity_id = i.entity_id
            WHERE i.event_id=?
            """,
            (event_dict["id"],),
        )
        event_dict["commodity_impacts"] = [dict(impact) for impact in impacts]
        if isinstance(event_dict.get("entities_json"), str):
            event_dict["entities_json"] = json.loads(event_dict["entities_json"])
        events.append(event_dict)
    
    return wrap_response(
        data=events,
        meta={"page": page, "page_size": page_size, "total": total, "has_next": (offset + page_size) < total}
    )

@router.get("/{event_id}")
def get_event(event_id: str):
    event = get_event_detail_by_id(event_id)
    if not event:
        return wrap_response(error={"code": "EVENT_NOT_FOUND", "message": "Event not found"})
    return wrap_response(data=event)

@router.get("/{event_id}/impacts")
def get_event_impacts(event_id: str):
    impacts = db.rows(
        """
        SELECT i.*, k.name AS commodity
        FROM event_impacts i
        JOIN kg_entities k ON k.entity_id = i.entity_id
        WHERE i.event_id=?
        """,
        (event_id,),
    )
    return wrap_response(data=[dict(impact) for impact in impacts])

@router.get("/{event_id}/paths")
def get_event_paths(event_id: str):
    # This requires traversing from event impacted commodities to stocks
    return wrap_response(data=[])

@router.get("/{event_id}/stocks")
def get_event_stocks(event_id: str):
    stocks = db.rows(
        """
        SELECT s.*, st.name, st.industry, r.nodes_json, r.edges_json
        FROM stock_event_scores s
        LEFT JOIN stocks st ON st.symbol = s.stock_code
        LEFT JOIN reasoning_paths r
          ON r.event_id = s.event_id AND r.stock_code = s.stock_code
        WHERE s.event_id=?
        ORDER BY s.rank ASC, s.final_score DESC
        """,
        (event_id,),
    )
    for stock in stocks:
        stock["score_breakdown_json"] = (
            json.loads(stock["score_breakdown_json"])
            if isinstance(stock.get("score_breakdown_json"), str)
            else (stock.get("score_breakdown_json") or {})
        )
        stock["nodes_json"] = (
            json.loads(stock["nodes_json"])
            if isinstance(stock.get("nodes_json"), str)
            else (stock.get("nodes_json") or [])
        )
        stock["edges_json"] = (
            json.loads(stock["edges_json"])
            if isinstance(stock.get("edges_json"), str)
            else (stock.get("edges_json") or [])
        )
        stock["direction"] = stock["score_breakdown_json"].get("direction", "benefit")
        stock["event_score"] = stock.get("final_score", 0.0)
    return wrap_response(data=[dict(stock) for stock in stocks])
