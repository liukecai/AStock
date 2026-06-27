import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import pipeline
import httpx
import json
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model-service")

# Global dict to store pipelines
models = {}
MODEL_IDS = {
    "zh": "yiyanghkust/finbert-tone-chinese",
    "en": "ProsusAI/finbert",
}

# LLM Config
LLM_ENABLED = os.getenv("LLM_ENABLED", "false").lower() == "true"
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    hf_endpoint = os.getenv("HF_ENDPOINT", "https://huggingface.co")
    logger.info(f"Using HuggingFace endpoint: {hf_endpoint}")
    
    # Detect GPU availability
    device = 0 if torch.cuda.is_available() else -1
    logger.info(f"Using device: {'GPU (cuda)' if device == 0 else 'CPU'}")
    
    # Pre-load models on startup
    logger.info("Initializing Chinese financial sentiment model (yiyanghkust/finbert-tone-chinese)...")
    try:
        models["zh"] = pipeline(
            "sentiment-analysis", 
            model=MODEL_IDS["zh"],
            device=device,
            top_k=None
        )
        logger.info("Successfully loaded Chinese model.")
    except Exception as e:
        logger.error(f"Failed to load Chinese model: {e}")
        
    logger.info("Initializing English financial sentiment model (ProsusAI/finbert)...")
    try:
        models["en"] = pipeline(
            "sentiment-analysis", 
            model=MODEL_IDS["en"],
            device=device,
            top_k=None
        )
        logger.info("Successfully loaded English model.")
    except Exception as e:
        logger.error(f"Failed to load English model: {e}")

    yield
    # Clean up model pipelines
    models.clear()
    logger.info("Pipelines cleared.")

app = FastAPI(
    title="A-Quant Model Service",
    description="Dedicated NLP service for Financial Sentiment Analysis (FinBERT)",
    version="0.1.0",
    lifespan=lifespan
)

class AnalyzeRequest(BaseModel):
    text: str
    lang: str = "zh"

class AnalyzeResponse(BaseModel):
    sentiment: float
    confidence: float
    label: str
    probabilities: dict[str, float]
    model_version: str

def calculate_continuous_score(predictions, pos_label: str, neg_label: str) -> tuple[float, float, str, dict[str, float]]:
    # Map predictions to lowercase dict for robust matching
    probs = {}
    for pred in predictions:
        label = pred["label"]
        score = pred["score"]
        probs[label.lower()] = score
    
    pos_val = probs.get(pos_label.lower(), 0.0)
    neg_val = probs.get(neg_label.lower(), 0.0)
    
    # Calculate score as difference between positive and negative probabilities
    # Range is [-1.0, 1.0]
    sentiment_score = pos_val - neg_val
    
    # Find the top label and its confidence
    top_pred = max(predictions, key=lambda x: x["score"])
    
    # Original keys for probabilities return
    orig_probs = {pred["label"]: pred["score"] for pred in predictions}
    
    return round(sentiment_score, 4), round(top_pred["score"], 4), top_pred["label"], orig_probs

@app.get("/health")
def health():
    # Service is healthy if at least one model is initialized
    available = list(models.keys())
    if not available:
        raise HTTPException(status_code=503, detail="No models loaded.")
    return {"status": "healthy", "available_models": available}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    lang = req.lang.lower() if req.lang else "zh"
    # Fallback to 'zh' if 'en' is requested but not loaded, or vice versa
    if lang not in models:
        # Try to use any available model
        if models:
            lang = list(models.keys())[0]
            logger.warning(f"Requested language '{req.lang}' not available. Fallback to '{lang}' model.")
        else:
            raise HTTPException(status_code=503, detail="Sentiment analysis models not available.")
            
    pipe = models[lang]
    if not req.text or not req.text.strip():
        return AnalyzeResponse(
            sentiment=0.0,
            confidence=1.0,
            label="Neutral" if lang == "zh" else "neutral",
            probabilities={},
            model_version=MODEL_IDS[lang],
        )

    try:
        # Run inference
        results = pipe(req.text[:512]) # Truncate to standard BERT limit of 512 tokens to be safe
        predictions = results[0] # top_k=None returns list of lists, get first item's list of scores
        
        if lang == "zh":
            sentiment_score, confidence, label, probs = calculate_continuous_score(
                predictions, pos_label="Positive", neg_label="Negative"
            )
        else:
            sentiment_score, confidence, label, probs = calculate_continuous_score(
                predictions, pos_label="positive", neg_label="negative"
            )
            
        return AnalyzeResponse(
            sentiment=sentiment_score,
            confidence=confidence,
            label=label,
            probabilities=probs,
            model_version=MODEL_IDS[lang],
        )
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

# --- LLM Extraction Endpoints ---

class ExtractProfileRequest(BaseModel):
    text: str

class ExtractEventRequest(BaseModel):
    text: str

def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\\n".join(lines).strip()
    return text

async def call_llm(system_prompt: str, user_prompt: str, mock_data: dict) -> dict:
    if not LLM_ENABLED or not LLM_API_KEY or LLM_API_KEY == "mock":
        return mock_data
    
    url = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0
    }
    
    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            resp_data = response.json()
            
        content = resp_data["choices"][0]["message"]["content"]
        cleaned = clean_json_text(content)
        return json.loads(cleaned)
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API HTTP Error: {e.response.text}")
        raise HTTPException(status_code=502, detail=f"LLM API Error: {e.response.text}")
    except json.JSONDecodeError as e:
        logger.error(f"LLM parsing error: {e}\\nContent: {content}")
        raise HTTPException(status_code=500, detail="Failed to parse LLM response as JSON")
    except Exception as e:
        logger.error(f"LLM unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract/company_profile")
async def extract_company_profile(req: ExtractProfileRequest):
    system_prompt = (
        "You are an expert financial analyst extracting supply chain and product information.\\n"
        "You must return ONLY a valid JSON object. No markdown wrappers.\\n"
        "Schema:\\n"
        "{\\n"
        '  "entities": [{"name": "string", "type": "Product|Material|Industry|Company", "aliases": ["string"]}],\\n'
        '  "relations": [{"source": "string", "relation": "produces|uses|used_in|supplies|competitor", "target": "string", "evidence_text": "string", "confidence": float}]\\n'
        "}"
    )
    mock_data = {
        "entities": [{"name": "Mock Product", "type": "Product", "aliases": []}],
        "relations": [{"source": "Mock Company", "relation": "produces", "target": "Mock Product", "evidence_text": "Mock text", "confidence": 0.9}]
    }
    return await call_llm(system_prompt, req.text, mock_data)

@app.post("/extract/event")
async def extract_event(req: ExtractEventRequest):
    system_prompt = (
        "You are an expert financial analyst extracting event impact information.\\n"
        "You must return ONLY a valid JSON object. No markdown wrappers.\\n"
        "Schema:\\n"
        "{\\n"
        '  "event_type": "supply_shortage|supply_increase|demand_weakness|oversupply|policy_support|supply_disruption|geo_conflict",\\n'
        '  "target_entity": "string",\\n'
        '  "intensity": "high|medium|low",\\n'
        '  "direction": "positive|negative",\\n'
        '  "evidence_text": "string",\\n'
        '  "confidence": float\\n'
        "}"
    )
    mock_data = {
        "event_type": "supply_shortage",
        "target_entity": "六氟化钨",
        "intensity": "high",
        "direction": "negative",
        "evidence_text": "市场传出供应紧张的消息",
        "confidence": 0.9
    }
    return await call_llm(system_prompt, req.text, mock_data)
