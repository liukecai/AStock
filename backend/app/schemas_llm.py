from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ExtractedEntity(BaseModel):
    name: str = Field(..., description="The name of the entity")
    type: Literal["Product", "Material", "Industry", "Company"] = Field(..., description="The type of the entity")
    aliases: List[str] = Field(default_factory=list, description="Aliases or alternative names")

class ExtractedRelation(BaseModel):
    source: str = Field(..., description="The source entity name")
    relation: Literal["produces", "uses", "used_in", "supplies", "competitor"] = Field(..., description="The relation type")
    target: str = Field(..., description="The target entity name")
    evidence_text: str = Field(..., description="The exact text fragment used as evidence")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")

class CompanyProfileExtraction(BaseModel):
    entities: List[ExtractedEntity] = Field(default_factory=list)
    relations: List[ExtractedRelation] = Field(default_factory=list)

class EventExtraction(BaseModel):
    event_type: Literal["supply_shortage", "supply_increase", "demand_weakness", "oversupply", "policy_support", "supply_disruption", "geo_conflict"] = Field(..., description="Type of the event")
    target_entity: str = Field(..., description="The entity affected by the event")
    intensity: Literal["high", "medium", "low"] = Field(..., description="Intensity of the event")
    direction: Literal["positive", "negative"] = Field(..., description="Impact direction on the target entity")
    evidence_text: str = Field(..., description="The exact text fragment used as evidence")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
