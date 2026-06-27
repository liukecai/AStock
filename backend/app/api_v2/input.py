import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from ..config import settings
from .. import db
import uuid
import datetime
from ..services.event_extractor import identify_commodity_from_db
from ..models.v2_kg import CandidateEntity

router = APIRouter()


def _normalize_direction(raw_direction: str | None) -> str:
    mapping = {
        "benefit": "benefit",
        "positive": "benefit",
        "up": "benefit",
        "harm": "harm",
        "negative": "harm",
        "down": "harm",
    }
    return mapping.get((raw_direction or "").strip().lower(), "benefit")


def _normalize_intensity(raw_intensity) -> float:
    if isinstance(raw_intensity, (int, float)):
        return float(raw_intensity)
    if isinstance(raw_intensity, str):
        mapping = {"high": 0.8, "medium": 0.6, "low": 0.3}
        normalized = mapping.get(raw_intensity.strip().lower())
        if normalized is not None:
            return normalized
        try:
            return float(raw_intensity)
        except ValueError:
            pass
    return 0.5

class UploadTextRequest(BaseModel):
    text: str
    source_name: str = "user_private"


def _find_active_commodity(target_name: str | None, text: str) -> dict | None:
    commodity_data = identify_commodity_from_db(text, db)
    if commodity_data or not target_name:
        return commodity_data
    return db.row(
        """
        SELECT entity_id, name
        FROM kg_entities
        WHERE status='active'
          AND entity_type IN ('Commodity', 'Product', 'Material')
          AND LOWER(name)=LOWER(?)
        LIMIT 1
        """,
        (target_name,),
    )


def _get_or_create_candidate_entity(req: UploadTextRequest, extracted: dict) -> CandidateEntity:
    target_name = (extracted.get("target_entity") or "未知实体").strip() or "未知实体"
    now = datetime.datetime.now(datetime.timezone.utc)
    with db.session_scope() as session:
        candidate = (
            session.query(CandidateEntity)
            .filter(
                CandidateEntity.status == "candidate",
                CandidateEntity.entity_type == "Commodity",
                CandidateEntity.name.ilike(target_name),
            )
            .order_by(CandidateEntity.created_at.desc())
            .first()
        )
        if candidate:
            return candidate

        candidate = CandidateEntity(
            entity_id=f"cand_ent_{uuid.uuid4().hex[:12]}",
            entity_type="Commodity",
            name=target_name,
            canonical_name=target_name,
            aliases_json=[],
            description=f"由用户私有输入触发，待审核的商品候选实体：{target_name}",
            metadata_json={
                "source_name": req.source_name,
                "raw_text": req.text[:500],
                "model_output": extracted,
            },
            status="candidate",
            extractor_type="user_private_input",
            created_at=now,
            updated_at=now,
        )
        session.add(candidate)
        session.flush()
        session.expunge(candidate)
        return candidate

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

    commodity_data = _find_active_commodity(extracted.get("target_entity"), req.text)
    if not commodity_data:
        candidate = _get_or_create_candidate_entity(req, extracted)
        return {
            "success": True,
            "data": {
                "candidate_entity_id": candidate.entity_id,
                "candidate_status": candidate.status,
                "requires_review": True,
                "extracted": extracted,
                "message": "未匹配到已入图实体，已自动写入候选实体等待审核。",
            },
        }

    event_id = f"evt_private_{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.now()
    
    event = {
        "event_id": event_id,
        "event_type": extracted["event_type"],
        "subtype": extracted.get("subtype", "user_input"),
        "title": f"Private Input: {commodity_data['name']}",
        "description": req.text[:500],
        "entities_json": json.dumps(
            [{"entity_id": commodity_data["entity_id"], "name": commodity_data["name"]}],
            ensure_ascii=False,
        ),
        "intensity": _normalize_intensity(extracted.get("intensity")),
        "direction": _normalize_direction(extracted.get("direction")),
        "occurred_at": now.isoformat(),
        "created_at": now.isoformat(),
    }
    impact = {
        "impact_id": f"imp_private_{uuid.uuid4().hex[:8]}",
        "event_id": event_id,
        "entity_id": commodity_data["entity_id"],
        "impact_type": extracted.get("impact_type", "direct"),
        "impact_score": event["intensity"],
    }
    extraction_payload = {
        "source_name": req.source_name,
        "text": req.text,
        "model_output": extracted,
    }

    with db.connect() as conn:
        db._execmany(
            conn,
            """
            INSERT INTO event_instances (
                event_id, event_type, subtype, title, description,
                entities_json, intensity, direction, occurred_at, created_at
            ) VALUES (
                :event_id, :event_type, :subtype, :title, :description,
                :entities_json, :intensity, :direction, :occurred_at, :created_at
            )
            """,
            [event],
        )
        db._execmany(
            conn,
            """
            INSERT INTO event_impacts (
                impact_id, event_id, entity_id, impact_type, impact_score
            ) VALUES (
                :impact_id, :event_id, :entity_id, :impact_type, :impact_score
            )
            """,
            [impact],
        )

    return {
        "success": True,
        "data": {
            "event_id": event_id,
            "extracted": {
                **extracted,
                "entity_id": commodity_data["entity_id"],
                "target_entity": commodity_data["name"],
                "direction": event["direction"],
            },
            "event": {
                "id": event_id,
                "title": event["title"],
                "event_type": event["event_type"],
                "direction": event["direction"],
                "occurred_at": event["occurred_at"],
                "raw_input": extraction_payload,
            },
            "message": "Text processed and private V2 event created.",
        }
    }
