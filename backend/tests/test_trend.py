from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.services.scoring import build_signal, classify
from app.services.sentiment import aggregate_news, classify_event, score_text
from app.services.trend import calculate_trend


def test_rising_series_is_bullish():
    closes = np.linspace(10, 20, 100)
    frame = pd.DataFrame(
        {
            "trade_date": [(date.today() - timedelta(days=i)).isoformat() for i in range(100)][::-1],
            "close": closes,
            "volume": np.full(100, 1_000_000),
        }
    )
    result = calculate_trend(frame)
    assert result["bullish"] is True
    assert result["trend_score"] > 70


def test_keyword_sentiment_is_deterministic():
    score, words = score_text("公司业绩预增并推出股份回购计划")
    assert score > 0.5
    assert set(words) == {"预增", "回购"}


def test_announcement_negation_and_buyback_cancellation_are_neutral():
    score, words = score_text("公司最近五年未被监管部门处罚情况的公告")
    assert score == 0
    assert words == []
    score, words = score_text("关于回购注销部分限制性股票的公告")
    assert score == 0
    assert words == []


def test_signal_weights_are_applied():
    trend = {"trend_score": 80, "volume_ratio": 1.0, "bullish": True}
    news = {"sentiment": 0.5, "burst": 3.5, "mentions_today": 4, "keywords": []}
    signal = build_signal("000001", "2026-01-01", trend, news)
    assert signal["total_score"] == 72.5
    assert classify(True, 0.5, 3.5) == "主升浪信号"


def test_news_burst_uses_signal_date():
    news = [
        {
            "published_at": "2026-06-18T10:00:00",
            "sentiment": 0.5,
            "keywords": ["增长"],
        },
        {
            "published_at": "2026-06-18T11:00:00",
            "sentiment": 0.3,
            "keywords": ["中标"],
        },
        {
            "published_at": "2026-06-17T10:00:00",
            "sentiment": 0.0,
            "keywords": [],
        },
    ]
    result = aggregate_news(news, reference_date=date(2026, 6, 18))
    assert result["mentions_today"] == 2
    assert result["burst"] == 1.8


def test_event_classification_supports_policy_performance_and_risk():
    assert classify_event("央行宣布降准支持实体经济")[0] == "policy"
    assert classify_event("公司发布年报，净利润增长")[0] == "performance"
    assert classify_event("公司收到行政处罚事先告知书")[0] == "risk"
