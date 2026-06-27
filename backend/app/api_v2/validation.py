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

@router.get("/events/{event_id}")
def get_validation_event(event_id: str):
    results = db.rows(
        "SELECT * FROM event_validation_results WHERE event_id=? ORDER BY window, stock_code",
        (event_id,),
    )
    return wrap_response(data=results)

@router.get("/events/{event_id}/stocks/{stock_code}")
def get_validation_event_stock(event_id: str, stock_code: str):
    result = db.row(
        """
        SELECT * FROM event_validation_results
        WHERE event_id=? AND stock_code=?
        ORDER BY window
        LIMIT 1
        """,
        (event_id, stock_code),
    )
    if not result:
        return wrap_response(error={"code": "NOT_FOUND", "message": "Validation result not found"})
    return wrap_response(data=dict(result))

@router.get("/summary")
def get_validation_summary(summary_type: str = Query(...), key: Optional[str] = None):
    where = "summary_type = ?"
    params = [summary_type]
    if key:
        where += " AND summary_key = ?"
        params.append(key)
        
    summaries = db.rows(
        f"SELECT * FROM validation_summary WHERE {where} ORDER BY updated_at DESC",
        tuple(params),
    )
    return wrap_response(data=summaries)
