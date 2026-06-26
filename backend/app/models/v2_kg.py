from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base

class KGEntity(Base):
    __tablename__ = 'kg_entities'
    entity_id = Column(String, primary_key=True)
    entity_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    canonical_name = Column(String, nullable=False)
    aliases_json = Column(JSONB, nullable=False, default=[])
    description = Column(String, nullable=False, default='')
    metadata_json = Column(JSONB, nullable=False, default={})
    status = Column(String, nullable=False, default='active')
    merged_into_id = Column(String)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

class KGRelation(Base):
    __tablename__ = 'kg_relations'
    relation_id = Column(String, primary_key=True)
    source_entity_id = Column(String, ForeignKey('kg_entities.entity_id'), nullable=False)
    target_entity_id = Column(String, ForeignKey('kg_entities.entity_id'), nullable=False)
    relation_type = Column(String, nullable=False)
    direction = Column(String, nullable=False, default='directed')
    weight = Column(Float, nullable=False, default=1.0)
    confidence = Column(Float, nullable=False, default=1.0)
    source_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default='active')
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

class Evidence(Base):
    __tablename__ = 'evidence'
    evidence_id = Column(String, primary_key=True)
    source_type = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    source_url = Column(String)
    title = Column(String, nullable=False)
    raw_text = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    collected_at = Column(DateTime, nullable=False)
    related_company = Column(String)
    related_stock_code = Column(String)
    source_confidence = Column(Float, nullable=False, default=1.0)
    content_hash = Column(String, unique=True, nullable=False)
    status = Column(String, nullable=False, default='active')

class RelationEvidence(Base):
    __tablename__ = 'relation_evidence'
    relation_id = Column(String, ForeignKey('kg_relations.relation_id'), primary_key=True)
    evidence_id = Column(String, ForeignKey('evidence.evidence_id'), primary_key=True)
    support_type = Column(String, nullable=False, default='direct')
    extracted_text = Column(String, nullable=False)
    confidence_delta = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False)

class CandidateEntity(Base):
    __tablename__ = 'candidate_entities'
    entity_id = Column(String, primary_key=True)
    entity_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    canonical_name = Column(String, nullable=False)
    aliases_json = Column(JSONB, nullable=False, default=[])
    description = Column(String, nullable=False, default='')
    metadata_json = Column(JSONB, nullable=False, default={})
    status = Column(String, nullable=False, default='candidate')
    merged_into_id = Column(String)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    extractor_type = Column(String, nullable=False)
    prompt_version = Column(String)
    review_status = Column(String, nullable=False, default='pending')
    reviewer = Column(String)
    reviewed_at = Column(DateTime)

class CandidateRelation(Base):
    __tablename__ = 'candidate_relations'
    relation_id = Column(String, primary_key=True)
    source_entity_id = Column(String, nullable=False)
    target_entity_id = Column(String, nullable=False)
    relation_type = Column(String, nullable=False)
    direction = Column(String, nullable=False, default='directed')
    weight = Column(Float, nullable=False, default=1.0)
    confidence = Column(Float, nullable=False, default=1.0)
    source_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default='candidate')
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    extractor_type = Column(String, nullable=False)
    prompt_version = Column(String)
    review_status = Column(String, nullable=False, default='pending')
    reviewer = Column(String)
    reviewed_at = Column(DateTime)

class EventValidationResult(Base):
    __tablename__ = 'event_validation_results'
    validation_id = Column(String, primary_key=True)
    event_id = Column(String, nullable=False)
    stock_code = Column(String, nullable=False)
    path_id = Column(String)
    window = Column(String, nullable=False)
    t0_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    absolute_return = Column(Float)
    benchmark_return = Column(Float)
    industry_return = Column(Float)
    excess_return_index = Column(Float)
    excess_return_industry = Column(Float)
    max_gain = Column(Float)
    max_drawdown = Column(Float)
    hit = Column(Boolean)
    status = Column(String, nullable=False, default='pending')
    calculated_at = Column(DateTime)

class ValidationSummary(Base):
    __tablename__ = 'validation_summary'
    summary_id = Column(String, primary_key=True)
    summary_type = Column(String, nullable=False)
    summary_key = Column(String, nullable=False)
    window = Column(String, nullable=False)
    sample_count = Column(Integer, nullable=False, default=0)
    hit_rate = Column(Float, nullable=False, default=0.0)
    avg_excess_return = Column(Float, nullable=False, default=0.0)
    weight_adjustment = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, nullable=False)

class KGChangeLog(Base):
    __tablename__ = 'kg_change_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(String, nullable=False)
    entity_id = Column(String)
    relation_id = Column(String)
    old_value = Column(String)
    new_value = Column(String)
    reason = Column(String)
    operator = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
