from datetime import datetime, timezone
import httpx
import uuid
from typing import Any
from sqlalchemy.orm import Session
from ..config import settings
from ..schemas_llm import CompanyProfileExtraction, EventExtraction
from ..models.v2_kg import CandidateEntity, CandidateRelation

class LLMExtractorService:
    def __init__(self):
        self.model_service_url = settings.model_service_url

    def _call_model_service(self, endpoint: str, text: str) -> dict[str, Any]:
        url = f"{self.model_service_url.rstrip('/')}/{endpoint}"
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json={"text": text})
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to communicate with model-service: {e}")

    def extract_company_profile(self, text: str, source_evidence_id: str, db: Session):
        raw_result = self._call_model_service("extract/company_profile", text)
        parsed = CompanyProfileExtraction(**raw_result)
        
        now = datetime.now(timezone.utc)
        
        # Insert CandidateEntities
        for entity in parsed.entities:
            cand_ent = CandidateEntity(
                entity_id=f"cand_ent_{uuid.uuid4().hex[:12]}",
                entity_type=entity.type,
                name=entity.name,
                canonical_name=entity.name,
                aliases_json=entity.aliases,
                status="candidate",
                extractor_type="llm",
                created_at=now,
                updated_at=now,
            )
            db.add(cand_ent)
            
        # Insert CandidateRelations
        for rel in parsed.relations:
            cand_rel = CandidateRelation(
                relation_id=f"cand_rel_{uuid.uuid4().hex[:12]}",
                source_entity_id=rel.source, # We might need to resolve this to actual IDs later in review
                target_entity_id=rel.target, # Storing names temporarily in relation is tricky if schema strictly requires IDs. We should store IDs if known, but for candidates, we can use the names as a temporary ID or lookup.
                relation_type=rel.relation,
                confidence=rel.confidence,
                source_type="llm_extraction",
                status="candidate",
                extractor_type="llm",
                created_at=now,
                updated_at=now,
                # In a full implementation, evidence_text would link to RelationEvidence table.
                # For simplicity here we just use it as part of candidate generation.
            )
            db.add(cand_rel)
            
        db.commit()
        return parsed
        
    def extract_event(self, text: str, source_evidence_id: str, db: Session):
        raw_result = self._call_model_service("extract/event", text)
        parsed = EventExtraction(**raw_result)
        # Event extraction usually ties to EventInstance rather than kg_relations directly,
        # but the prompt asks to save to candidate relations if needed, or we just return it.
        # Following Phase 4 requirements, it says:
        # "将 LLM JSON 提取结果校验并写入 candidate_relations 表"
        
        now = datetime.now(timezone.utc)
        
        cand_rel = CandidateRelation(
            relation_id=f"cand_rel_{uuid.uuid4().hex[:12]}",
            source_entity_id="EVENT", # Placeholder
            target_entity_id=parsed.target_entity,
            relation_type=parsed.event_type,
            confidence=parsed.confidence,
            source_type="news",
            status="candidate",
            extractor_type="llm",
            created_at=now,
            updated_at=now,
        )
        db.add(cand_rel)
        db.commit()
        return parsed
