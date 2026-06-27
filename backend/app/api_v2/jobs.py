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
def get_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None
):
    where = "WHERE 1=1"
    params = []
    if status:
        where += " AND status = ?"
        params.append(status)
        
    total = db.row(f"SELECT COUNT(*) as count FROM jobs {where}", tuple(params))["count"]
    
    offset = (page - 1) * page_size
    query = f"SELECT * FROM jobs {where} ORDER BY started_at DESC LIMIT ? OFFSET ?"
    jobs = db.rows(query, tuple(params + [page_size, offset]))
    
    for job in jobs:
        job["details"] = json.loads(job["details"]) if job.get("details") else {}
        
    return wrap_response(
        data=jobs,
        meta={"page": page, "page_size": page_size, "total": total, "has_next": (offset + page_size) < total}
    )

@router.get("/latest")
def get_latest_jobs():
    jobs = db.rows("SELECT * FROM jobs")
    for job in jobs:
        job["details"] = json.loads(job["details"]) if job.get("details") else {}
    return wrap_response(data=jobs)

@router.get("/{job_id}")
def get_job(job_id: str):
    job = db.row("SELECT * FROM jobs WHERE name=?", (job_id,))
    if not job:
        return wrap_response(error={"code": "JOB_NOT_FOUND", "message": "Job not found"})
    job = dict(job)
    job["details"] = json.loads(job["details"]) if job.get("details") else {}
    return wrap_response(data=job)
