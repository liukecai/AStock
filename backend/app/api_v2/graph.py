from fastapi import APIRouter, Query, HTTPException
from typing import Annotated, Optional
from pydantic import BaseModel
from .. import db

router = APIRouter()

def wrap_response(data=None, error=None, meta=None):
    return {
        "success": error is None,
        "data": data,
        "error": error,
        "meta": meta or {}
    }

@router.get("/entities/search")
def search_entities(q: str = Query(..., min_length=1), entity_type: Optional[str] = None):
    # Support basic fuzzy matching
    query = "SELECT * FROM kg_entities WHERE name LIKE ?"
    params = [f"%{q}%"]
    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)
    query += " LIMIT 50"
    
    entities = db.rows(query, tuple(params))
    return wrap_response(data=entities)

@router.get("/entities/{entity_id}")
def get_entity(entity_id: str):
    entity = db.row("SELECT * FROM kg_entities WHERE entity_id=?", (entity_id,))
    if not entity:
        return wrap_response(error={"code": "ENTITY_NOT_FOUND", "message": "Entity not found"})
    return wrap_response(data=dict(entity))

@router.get("/entities/{entity_id}/neighbors")
def get_entity_neighbors(entity_id: str, relation_type: Optional[str] = None):
    # Neighbors where this entity is source or target
    query = """
        SELECT r.*, e.name as neighbor_name, e.entity_type as neighbor_type,
               CASE WHEN r.source_entity_id = ? THEN 'outgoing' ELSE 'incoming' END as direction,
               CASE WHEN r.source_entity_id = ? THEN r.target_entity_id ELSE r.source_entity_id END as neighbor_id
        FROM kg_relations r
        JOIN kg_entities e ON (CASE WHEN r.source_entity_id = ? THEN r.target_entity_id ELSE r.source_entity_id END) = e.entity_id
        WHERE (r.source_entity_id = ? OR r.target_entity_id = ?)
    """
    params = [entity_id, entity_id, entity_id, entity_id, entity_id]
    if relation_type:
        query += " AND r.relation_type = ?"
        params.append(relation_type)
        
    neighbors = db.rows(query, tuple(params))
    return wrap_response(data=neighbors)



@router.get("/paths")
def get_paths(source: str, target: str, max_depth: int = Query(4, le=4)):
    # This requires some graph traversal. We can use graph_querier.py logic if it fits.
    # For now, return a placeholder structure.
    return wrap_response(data=[])

@router.get("/relations/{relation_id}")
def get_relation(relation_id: str):
    rel = db.row("SELECT * FROM kg_relations WHERE relation_id=?", (relation_id,))
    if not rel:
        return wrap_response(error={"code": "RELATION_NOT_FOUND", "message": "Relation not found"})
    return wrap_response(data=dict(rel))

@router.get("/relations/{relation_id}/evidence")
def get_relation_evidence(relation_id: str):
    evidences = db.rows("SELECT * FROM relation_evidence WHERE relation_id=?", (relation_id,))
    return wrap_response(data=evidences)

class FeedbackRequest(BaseModel):
    action: str # "downvote", "report_error", "add_evidence"
    details: Optional[str] = None

@router.post("/relations/{relation_id}/feedback")
def submit_feedback(relation_id: str, req: FeedbackRequest):
    # In a full implementation, this would write to an audit log and modify confidence
    # For MVP, we just adjust confidence if downvote
    if req.action == "downvote":
        with db.connect() as conn:
            db._exec(conn, "UPDATE kg_relations SET confidence = confidence - 0.1 WHERE relation_id=?", (relation_id,))
            
    return wrap_response(data={"message": "Feedback submitted successfully"})
