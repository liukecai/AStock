import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from ..config import settings
from .. import db
import uuid
import datetime

router = APIRouter()

class UploadTextRequest(BaseModel):
    text: str
    source_name: str = "user_private"

@router.post("/upload")
async def process_custom_text(req: UploadTextRequest):
    """
    On-the-fly extraction of events/relations from uploaded text.
    """
    # 1. We would call model_service/app.py to extract events/relations from text
    # Since this is an MVP of proactive input, we simulate the LLM call or do a simple fetch
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{settings.model_service_url}/extract/event",
                json={"text": req.text}
            )
            resp.raise_for_status()
            extracted = resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Extraction failed: {str(e)}")
        
    # 2. Convert to an event
    if "event_type" not in extracted:
         raise HTTPException(status_code=422, detail="No event found in text")
         
    event_id = f"evt_private_{uuid.uuid4().hex[:8]}"
    now_str = datetime.datetime.now().isoformat()
    
    event = {
        "id": event_id,
        "news_id": None,
        "title": f"Private Input: {extracted.get('target_entity', 'Unknown')}",
        "summary": req.text[:200],
        "event_type": extracted["event_type"],
        "intensity": 0.8 if extracted.get("intensity") == "high" else 0.5,
        "direction": extracted.get("direction", "benefit"),
        "confidence": extracted.get("confidence", 0.9),
        "published_at": now_str,
        "created_at": now_str,
        "extraction_source": "user_private",
        "extraction_raw_output": json.dumps(extracted, ensure_ascii=False)
    }
    
    with db.connect() as conn:
        db._execmany(
            conn,
            """
            INSERT INTO events (id, news_id, title, summary, event_type, intensity, direction, confidence, published_at, created_at, extraction_source, extraction_raw_output)
            VALUES (:id, :news_id, :title, :summary, :event_type, :intensity, :direction, :confidence, :published_at, :created_at, :extraction_source, :extraction_raw_output)
            """,
            [event]
        )
        
        # Insert impact
        impact = {
            "event_id": event_id,
            "commodity": extracted.get("target_entity", "未知"),
            "impact_type": "direct",
            "direction": event["direction"]
        }
        db._execmany(
            conn,
            "INSERT INTO commodity_impacts (event_id, commodity, impact_type, direction) VALUES (:event_id, :commodity, :impact_type, :direction)",
            [impact]
        )
        
    # 3. We could trigger reasoning here, but for MVP returning the event is enough.
    # The dashboard can immediately query this event ID.
    
    return {
        "success": True,
        "data": {
            "event_id": event_id,
            "extracted": extracted,
            "message": "Text processed and private event created."
        }
    }
