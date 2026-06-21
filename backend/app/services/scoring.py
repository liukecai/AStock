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


def build_signal(symbol: str, signal_date: str, trend: dict, news: dict) -> dict:
    sentiment_100 = float(np.clip((float(news["sentiment"]) + 1) * 50, 0, 100))
    volume_score = float(np.clip(float(trend["volume_ratio"]) / 2 * 100, 0, 100))
    total = (
        0.5 * float(trend["trend_score"])
        + 0.3 * sentiment_100
        + 0.2 * volume_score
    )
    return {
        "symbol": symbol,
        "signal_date": signal_date,
        "trend_score": round(float(trend["trend_score"]), 2),
        "sentiment_score": round(sentiment_100, 2),
        "volume_score": round(volume_score, 2),
        "total_score": round(total, 2),
        "burst": float(news["burst"]),
        "status": classify(
            bool(trend["bullish"]), float(news["sentiment"]), float(news["burst"])
        ),
        "metrics": {**trend, **news},
    }

