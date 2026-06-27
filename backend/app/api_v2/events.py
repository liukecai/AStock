from fastapi import APIRouter, Query, HTTPException
from typing import Annotated, Optional
from .. import db
import json

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
        
    total = db.row(f"SELECT COUNT(*) as count FROM events {where}", tuple(params))["count"]
    
    offset = (page - 1) * page_size
    query = f"SELECT * FROM events {where} ORDER BY published_at DESC LIMIT ? OFFSET ?"
    events = db.rows(query, tuple(params + [page_size, offset]))
    
    return wrap_response(
        data=events,
        meta={"page": page, "page_size": page_size, "total": total, "has_next": (offset + page_size) < total}
    )

@router.get("/{event_id}")
def get_event(event_id: str):
    event = db.row("SELECT * FROM events WHERE id=?", (event_id,))
    if not event:
        return wrap_response(error={"code": "EVENT_NOT_FOUND", "message": "Event not found"})
    return wrap_response(data=dict(event))

@router.get("/{event_id}/impacts")
def get_event_impacts(event_id: str):
    impacts = db.rows("SELECT * FROM commodity_impacts WHERE event_id=?", (event_id,))
    return wrap_response(data=impacts)

@router.get("/{event_id}/paths")
def get_event_paths(event_id: str):
    # This requires traversing from event impacted commodities to stocks
    return wrap_response(data=[])

@router.get("/{event_id}/stocks")
def get_event_stocks(event_id: str):
    stocks = db.rows("SELECT * FROM event_stock_scores WHERE event_id=? ORDER BY event_score DESC", (event_id,))
    for stock in stocks:
        stock["causal_chain"] = json.loads(stock["causal_chain"]) if stock.get("causal_chain") else {}
        stock["evidence"] = json.loads(stock["evidence"]) if stock.get("evidence") else []
    return wrap_response(data=stocks)
