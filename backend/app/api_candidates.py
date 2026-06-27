from typing import Annotated, Any
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy.orm import Session
from . import db
from .config import settings
from .models.v2_kg import CandidateEntity, CandidateRelation, KGEntity, KGRelation

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

def _require_admin(x_admin_secret: Annotated[str | None, Header()] = None) -> None:
    if not settings.admin_secret:
        return
    if not x_admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="当前操作需要管理授权")

@router.get("/pending")
def list_pending_candidates(
    type: str = Query("all", description="Type of candidates to fetch: 'entity', 'relation', or 'all'"),
    limit: int = 50,
    offset: int = 0
) -> dict:
    with db.session_scope() as session:
        result = {}
        if type in ("entity", "all"):
            entities = session.query(CandidateEntity).filter(CandidateEntity.status == 'candidate').limit(limit).offset(offset).all()
            result["entities"] = [{"id": e.entity_id, "name": e.name, "type": e.entity_type} for e in entities]
            
        if type in ("relation", "all"):
            relations = session.query(CandidateRelation).filter(CandidateRelation.status == 'candidate').limit(limit).offset(offset).all()
            result["relations"] = [{"id": r.relation_id, "source": r.source_entity_id, "target": r.target_entity_id, "relation_type": r.relation_type, "confidence": r.confidence} for r in relations]
            
        return result

@router.post("/entities/{entity_id}/approve")
def approve_entity(
    entity_id: str,
    x_admin_secret: Annotated[str | None, Header()] = None
) -> dict:
    _require_admin(x_admin_secret)
    with db.session_scope() as session:
        cand = session.query(CandidateEntity).filter(CandidateEntity.entity_id == entity_id, CandidateEntity.status == 'candidate').first()
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate entity not found or already processed")
            
        now = datetime.now(timezone.utc)
        
        kg_ent = KGEntity(
            entity_id=cand.entity_id.replace("cand_", "kg_"),
            entity_type=cand.entity_type,
            name=cand.name,
            canonical_name=cand.canonical_name,
            aliases_json=cand.aliases_json,
            description=cand.description,
            metadata_json=cand.metadata_json,
            status='active',
            created_at=now,
            updated_at=now
        )
        session.add(kg_ent)
        
        cand.status = 'approved'
        cand.review_status = 'approved'
        cand.reviewed_at = now
        session.commit()
        return {"status": "ok", "new_entity_id": kg_ent.entity_id}

@router.post("/relations/{relation_id}/approve")
def approve_relation(
    relation_id: str,
    x_admin_secret: Annotated[str | None, Header()] = None
) -> dict:
    _require_admin(x_admin_secret)
    with db.session_scope() as session:
        cand = session.query(CandidateRelation).filter(CandidateRelation.relation_id == relation_id, CandidateRelation.status == 'candidate').first()
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate relation not found or already processed")
            
        now = datetime.now(timezone.utc)
        
        kg_rel = KGRelation(
            relation_id=cand.relation_id.replace("cand_", "kg_"),
            source_entity_id=cand.source_entity_id,
            target_entity_id=cand.target_entity_id,
            relation_type=cand.relation_type,
            direction=cand.direction,
            weight=cand.weight,
            confidence=cand.confidence,
            source_type=cand.source_type,
            status='active',
            valid_from=cand.valid_from,
            valid_to=cand.valid_to,
            created_at=now,
            updated_at=now
        )
        session.add(kg_rel)
        
        cand.status = 'approved'
        cand.review_status = 'approved'
        cand.reviewed_at = now
        session.commit()
        return {"status": "ok", "new_relation_id": kg_rel.relation_id}

@router.post("/entities/{entity_id}/reject")
def reject_entity(
    entity_id: str,
    x_admin_secret: Annotated[str | None, Header()] = None
) -> dict:
    _require_admin(x_admin_secret)
    with db.session_scope() as session:
        cand = session.query(CandidateEntity).filter(CandidateEntity.entity_id == entity_id, CandidateEntity.status == 'candidate').first()
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate entity not found or already processed")
            
        cand.status = 'rejected'
        cand.review_status = 'rejected'
        cand.reviewed_at = datetime.now(timezone.utc)
        session.commit()
        return {"status": "ok"}

@router.post("/relations/{relation_id}/reject")
def reject_relation(
    relation_id: str,
    x_admin_secret: Annotated[str | None, Header()] = None
) -> dict:
    _require_admin(x_admin_secret)
    with db.session_scope() as session:
        cand = session.query(CandidateRelation).filter(CandidateRelation.relation_id == relation_id, CandidateRelation.status == 'candidate').first()
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate relation not found or already processed")
            
        cand.status = 'rejected'
        cand.review_status = 'rejected'
        cand.reviewed_at = datetime.now(timezone.utc)
        session.commit()
        return {"status": "ok"}
