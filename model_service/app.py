import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model-service")

# Global dict to store pipelines
models = {}
MODEL_IDS = {
    "zh": "yiyanghkust/finbert-tone-chinese",
    "en": "ProsusAI/finbert",
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    hf_endpoint = os.getenv("HF_ENDPOINT", "https://huggingface.co")
    logger.info(f"Using HuggingFace endpoint: {hf_endpoint}")
    
    # Pre-load models on startup
    logger.info("Initializing Chinese financial sentiment model (yiyanghkust/finbert-tone-chinese)...")
    try:
        models["zh"] = pipeline(
            "sentiment-analysis", 
            model=MODEL_IDS["zh"],
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
