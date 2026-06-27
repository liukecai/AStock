import json

from fastapi import APIRouter, Query
from .. import db

router = APIRouter()

def wrap_response(data=None, error=None, meta=None):
    return {
        "success": error is None,
        "data": data,
        "error": error,
        "meta": meta or {}
    }

@router.get("/{stock_code}/knowledge")
def get_stock_knowledge(stock_code: str):
    stock = db.row("SELECT * FROM stocks WHERE symbol=?", (stock_code,))
    if not stock:
        return wrap_response(error={"code": "STOCK_NOT_FOUND", "message": "Stock not found"})
        
    profiles = db.rows("SELECT * FROM company_commodity_profiles WHERE symbol=?", (stock_code,))
    return wrap_response(data={
        "stock": dict(stock),
        "profiles": profiles
    })

@router.get("/{stock_code}/events")
def get_stock_events(stock_code: str):
    events = db.rows("""
        SELECT
            e.*,
            e.event_id AS id,
            s.final_score,
            s.rank,
            s.confidence,
            s.score_breakdown_json
        FROM stock_event_scores s
        JOIN event_instances e ON s.event_id = e.event_id
        WHERE s.stock_code=?
        ORDER BY e.occurred_at DESC, s.rank ASC
        LIMIT 50
    """, (stock_code,))
    for event in events:
        if isinstance(event.get("entities_json"), str):
            event["entities_json"] = json.loads(event["entities_json"])
        if isinstance(event.get("score_breakdown_json"), str):
            event["score_breakdown_json"] = json.loads(event["score_breakdown_json"])
    return wrap_response(data=events)

@router.get("/{stock_code}/explain")
def explain_stock(stock_code: str, event_id: str = Query(...)):
    score = db.row(
        """
        SELECT s.*, r.nodes_json, r.edges_json
        FROM stock_event_scores s
        LEFT JOIN reasoning_paths r
          ON r.event_id = s.event_id AND r.stock_code = s.stock_code
        WHERE s.stock_code=? AND s.event_id=?
        """,
        (stock_code, event_id),
    )
    if not score:
        return wrap_response(error={"code": "RELATION_NOT_FOUND", "message": "Stock not impacted by this event"})
        
    res = dict(score)
    res["score_breakdown_json"] = (
        json.loads(res["score_breakdown_json"])
        if isinstance(res.get("score_breakdown_json"), str)
        else (res.get("score_breakdown_json") or {})
    )
    res["nodes_json"] = (
        json.loads(res["nodes_json"])
        if isinstance(res.get("nodes_json"), str)
        else (res.get("nodes_json") or [])
    )
    res["edges_json"] = (
        json.loads(res["edges_json"])
        if isinstance(res.get("edges_json"), str)
        else (res.get("edges_json") or [])
    )
    res["direction"] = res["score_breakdown_json"].get("direction", "benefit")
    
    return wrap_response(data=res)
