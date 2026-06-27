from fastapi import APIRouter, Query, HTTPException
from typing import Annotated, Optional
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
        SELECT e.*, s.event_score 
        FROM event_stock_scores s 
        JOIN events e ON s.event_id = e.id 
        WHERE s.symbol=? 
        ORDER BY e.published_at DESC LIMIT 50
    """, (stock_code,))
    return wrap_response(data=events)

@router.get("/{stock_code}/explain")
def explain_stock(stock_code: str, event_id: str = Query(...)):
    score = db.row("SELECT * FROM event_stock_scores WHERE symbol=? AND event_id=?", (stock_code, event_id))
    if not score:
        return wrap_response(error={"code": "RELATION_NOT_FOUND", "message": "Stock not impacted by this event"})
        
    import json
    res = dict(score)
    res["causal_chain"] = json.loads(res["causal_chain"]) if res.get("causal_chain") else {}
    res["evidence"] = json.loads(res["evidence"]) if res.get("evidence") else []
    
    return wrap_response(data=res)
