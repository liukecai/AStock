from __future__ import annotations

import numpy as np

from ..config import settings
from .calibration import load_calibration


def classify(bullish: bool, sentiment: float, burst: float) -> str:
    if bullish and sentiment >= 0.35 and burst >= 3:
        return "主升浪信号"
    if bullish:
        return "趋势股"
    if burst >= 3:
        return "风险博弈"
    if sentiment <= -0.35:
        return "回避"
    return "观察"


def research_weight(total_score: float, status: str, news: dict) -> int:
    """Return a capped research allocation weight, not a trading instruction."""

    if status == "回避" or float(news["sentiment"]) <= -0.35:
        return 0
    thresholds = load_calibration(settings.calibration_path)[
        "research_weight_thresholds"
    ]
    if total_score < thresholds[0]:
        return 0
    if total_score < thresholds[1]:
        weight = 2
    elif total_score < thresholds[2]:
        weight = 4
    elif total_score < thresholds[3]:
        weight = 6
    else:
        weight = 8
    if int(news.get("event_counts", {}).get("risk", 0)) > 0:
        weight = min(weight, 2)
    return weight


def build_signal(symbol: str, signal_date: str, trend: dict, news: dict) -> dict:
    calibration = load_calibration(settings.calibration_path)
    factor_weights = calibration["factor_weights"]
    sentiment_100 = float(np.clip((float(news["sentiment"]) + 1) * 50, 0, 100))
    volume_score = float(np.clip(float(trend["volume_ratio"]) / 2 * 100, 0, 100))
    total = (
        factor_weights["trend_score"] * float(trend["trend_score"])
        + factor_weights["sentiment_score"] * sentiment_100
        + factor_weights["volume_score"] * volume_score
    )
    status = classify(
        bool(trend["bullish"]), float(news["sentiment"]), float(news["burst"])
    )
    weight = research_weight(total, status, news)
    return {
        "symbol": symbol,
        "signal_date": signal_date,
        "trend_score": round(float(trend["trend_score"]), 2),
        "sentiment_score": round(sentiment_100, 2),
        "volume_score": round(volume_score, 2),
        "total_score": round(total, 2),
        "burst": float(news["burst"]),
        "status": status,
        "metrics": {
            **trend,
            **news,
            "research_weight_pct": weight,
            "research_weight_note": "研究权重上限，不构成交易或投资建议",
            "calibration_source": calibration["source"],
            "factor_weights": factor_weights,
            "research_weight_thresholds": calibration[
                "research_weight_thresholds"
            ],
        },
    }
