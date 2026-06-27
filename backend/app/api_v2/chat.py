import httpx
import json
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from ..config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatQueryRequest(BaseModel):
    query: str

def fallback_intent_parsing(query: str) -> dict:
    # A simple regex/keyword fallback if external LLM fails
    event_type = "general"
    if "短缺" in query or "不足" in query:
        event_type = "supply_shortage"
    elif "政策" in query:
        event_type = "policy_change"
    
    # Try to extract potential entities
    entities = []
    known_commodities = ["六氟化钨", "钨", "铜", "金", "锂", "石油", "半导体"]
    for kc in known_commodities:
        if kc in query:
            entities.append(kc)
            
    return {
        "event_type": event_type,
        "entity_names": entities,
        "direction": "benefit" if "利好" in query else "harm" if "利空" in query else None
    }

async def parse_nl2graph(query: str) -> dict:
    if not settings.event_llm_api_key or settings.event_llm_api_key == "mock":
        return fallback_intent_parsing(query)
        
    system_prompt = (
        "You are an intent parser for a financial knowledge graph.\\n"
        "Convert the user's natural language query into a JSON object with these fields:\\n"
        "- event_type: (e.g. supply_shortage, policy_change, geo_conflict, general)\\n"
        "- entity_names: [list of entity names mentioned]\\n"
        "- direction: 'benefit' or 'harm' or null\\n"
        "Return ONLY valid JSON."
    )
    
    url = f"{settings.event_llm_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.event_llm_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": settings.event_llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        "temperature": 0.0
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"]
            
            # clean json
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\\n")
                content = "\\n".join(lines[1:-1]).strip()
                
            return json.loads(content)
    except Exception as e:
        logger.error(f"LLM parsing failed: {e}, falling back to rule-based.")
        return fallback_intent_parsing(query)

@router.post("/query")
async def chat_query(req: ChatQueryRequest):
    intent = await parse_nl2graph(req.query)
    
    # We could theoretically query the graph here, but for now we just return the parsed intent 
    # so the frontend can redirect to the SupplyChainExplorer or EventDashboard with filters.
    
    return {
        "success": True,
        "data": {
            "intent": intent
        }
    }
