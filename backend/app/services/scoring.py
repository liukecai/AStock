from __future__ import annotations

import numpy as np


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
    if total_score < 60:
        return 0
    if total_score < 70:
        weight = 2
    elif total_score < 80:
        weight = 4
    elif total_score < 90:
        weight = 6
    else:
        weight = 8
    if int(news.get("event_counts", {}).get("risk", 0)) > 0:
        weight = min(weight, 2)
    return weight


def build_signal(symbol: str, signal_date: str, trend: dict, news: dict) -> dict:
    sentiment_100 = float(np.clip((float(news["sentiment"]) + 1) * 50, 0, 100))
    volume_score = float(np.clip(float(trend["volume_ratio"]) / 2 * 100, 0, 100))
    total = (
        0.5 * float(trend["trend_score"])
        + 0.3 * sentiment_100
        + 0.2 * volume_score
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
        },
    }
