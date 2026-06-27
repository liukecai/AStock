from typing import Dict, Any, List

def calculate_stock_score(
    exposure_score: float, # 0.0 to 1.0
    exposure_confidence: float, # 0.0 to 1.0
    event_type: str,
    event_intensity: float, # 0.0 to 1.0
    event_confidence: float, # 0.0 to 1.0
    trend_strength: float, # 0 to 100
    sentiment_score: float = 50.0, # 0 to 100
    volume_score: float = 50.0 # 0 to 100
) -> Dict[str, Any]:
    """
    Calculate final score combining exposure, event intensity, and market trend.
    Returns a dict containing the final score and a breakdown.
    """
    # 1. Event Impact (0 to 100)
    base_impact = {
        "geo_conflict": 90.0,
        "supply_shock": 80.0,
        "policy_change": 75.0,
        "disruption": 70.0
    }.get(event_type, 60.0)
    
    event_impact_raw = min(max(base_impact + (event_intensity - 0.5) * 20.0, 0.0), 100.0)
    event_impact = round(event_impact_raw * event_confidence, 2)
    
    # 2. Exposure Component (0 to 100)
    sector_exposure = exposure_score * 100.0
    
    # 3. Final Score
    # Event Score = 0.5 * Event Impact + 0.3 * Sector Exposure + 0.2 * Trend Strength
    final_score = 0.5 * event_impact + 0.3 * sector_exposure + 0.2 * trend_strength
    final_score = round(min(max(final_score, 0.0), 100.0), 2)
    
    # Confidence is a product of event confidence and path confidence
    overall_confidence = round(event_confidence * exposure_confidence, 2)
    
    label = "High" if final_score >= 80 else ("Medium" if final_score >= 60 else "Low")
    
    return {
        "final_score": final_score,
        "confidence": overall_confidence,
        "label": label,
        "score_breakdown": {
            "event_impact": event_impact,
            "sector_exposure": round(sector_exposure, 2),
            "trend_strength": round(trend_strength, 2),
            "sentiment_score": sentiment_score,
            "volume_score": volume_score
        }
    }

def rank_stocks(scored_stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort stocks by direction and final_score, and assign a rank.
    """
    # First sort by direction (benefit first), then by score descending
    # Benefit comes before Harm (alphabetically 'benefit' < 'harm')
    scored_stocks.sort(key=lambda x: (x.get("direction", "benefit") == "harm", -x["final_score"]))
    
    for i, item in enumerate(scored_stocks):
        item["rank"] = i + 1
        
    return scored_stocks
