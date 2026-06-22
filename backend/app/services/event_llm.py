from __future__ import annotations

import json
from typing import Any
import httpx

from ..config import settings

def validate_llm_result(data: dict[str, Any]) -> bool:
    if not isinstance(data, dict):
        return False
    if "is_relevant" not in data or not isinstance(data["is_relevant"], bool):
        return False
    if not data["is_relevant"]:
        return True

    # Validate commodity
    allowed_commodities = {"tungsten", "WF6", "oil", "copper", "gold", "lithium"}
    if data.get("commodity") not in allowed_commodities:
        return False

    # Validate event_type
    allowed_event_types = {"geo_conflict", "supply_shock", "policy_change", "disruption"}
    if data.get("event_type") not in allowed_event_types:
        return False

    # Validate impact_type
    allowed_impact_types = {
        "supply_increase",
        "demand_weakness",
        "oversupply",
        "policy_support",
        "supply_disruption",
        "supply_shortage"
    }
    if data.get("impact_type") not in allowed_impact_types:
        return False

    # Validate direction
    if data.get("direction") not in {"benefit", "harm"}:
        return False

    # Validate intensity
    try:
        intensity = float(data.get("intensity", 0.0))
        if not (0.0 <= intensity <= 1.0):
            return False
    except (ValueError, TypeError):
        return False

    # Validate confidence
    try:
        confidence = float(data.get("confidence", 0.0))
        if not (0.0 <= confidence <= 1.0):
            return False
    except (ValueError, TypeError):
        return False

    # Validate subtype and rationale as strings
    if not isinstance(data.get("subtype"), str):
        return False
    if not isinstance(data.get("rationale"), str):
        return False

    return True

def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        # Strip code block formatting
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def extract_event_llm(title: str, summary: str) -> dict[str, Any] | None:
    """
    Extract event using LLM with OpenAI-compatible API.
    Returns None if LLM is not enabled or api_key is not configured.
    Raises exceptions (httpx errors, parsing errors, validation errors) on failure.
    """
    if not settings.event_llm_enabled or not settings.event_llm_api_key:
        return None

    url = f"{settings.event_llm_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.event_llm_api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are an expert financial analyst. Your task is to analyze a news event and extract structured commodity event information.\n"
        "You must return a JSON object, and only a valid JSON object. Do not include any markdown formatting wrappers (like ```json ... ```) or conversational filler; output only raw JSON.\n\n"
        "The JSON schema must be:\n"
        "{\n"
        '  "is_relevant": bool, // true if relevant to one of the target commodities, false otherwise.\n'
        '  "commodity": "tungsten" | "WF6" | "oil" | "copper" | "gold" | "lithium" | null,\n'
        '  "event_type": "geo_conflict" | "supply_shock" | "policy_change" | "disruption" | null,\n'
        '  "subtype": string | null,\n'
        '  "impact_type": "supply_increase" | "demand_weakness" | "oversupply" | "policy_support" | "supply_disruption" | "supply_shortage" | null,\n'
        '  "direction": "benefit" | "harm" | null, // direction at the commodity price/industry level: benefit means positive, harm means negative\n'
        '  "intensity": float, // 0.0 to 1.0\n'
        '  "confidence": float, // 0.0 to 1.0\n'
        '  "rationale": string\n'
        "}\n\n"
        "Allowed values for fields must be strictly followed. If the event is irrelevant, set is_relevant to false and other fields to null."
    )

    user_prompt = f"Analyze this news:\nTitle: {title}\nSummary: {summary}"

    payload = {
        "model": settings.event_llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0
    }

    timeout = settings.event_llm_timeout_seconds

    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        resp_data = response.json()

    content = resp_data["choices"][0]["message"]["content"]
    cleaned = clean_json_text(content)
    result = json.loads(cleaned)

    # Coerce fields if necessary
    if not validate_llm_result(result):
        raise ValueError("LLM response failed schema validation")

    return result
