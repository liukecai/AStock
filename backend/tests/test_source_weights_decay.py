from __future__ import annotations

from datetime import date
import math

from app.services.sentiment import aggregate_news


def test_source_weights_and_time_decay():
    # 1. Official announcements (巨潮资讯) have weight 1.5, Bloomberg has 1.2
    # 2. Today's news has age = 0 (decay = 1.0)
    # 3. News from 4 days ago has decay = exp(-0.25 * 4) = exp(-1) = 0.367879
    # Test case:
    news = [
        {
            "published_at": "2026-06-21T12:00:00",
            "source": "巨潮资讯",
            "sentiment": 0.8,
            "confidence": 1.0,
            "keywords": ["预增"],
        },
        {
            "published_at": "2026-06-21T10:00:00",
            "source": "Bloomberg Markets",
            "sentiment": 0.4,
            "confidence": 1.0,
            "keywords": ["growth"],
        },
    ]

    # Calculate weighted average manually:
    # W1 = 1.5 * exp(-0.25 * ~0) * 1.0 = 1.5
    # W2 = 1.2 * exp(-0.25 * ~0) * 1.0 = 1.2
    # Sum(W * S) = 0.8 * 1.5 + 0.4 * 1.2 = 1.2 + 0.48 = 1.68
    # Sum(W) = 1.5 + 1.2 = 2.7
    # Expected Sentiment = 1.68 / 2.7 = 0.62222... (rounds to 0.622)

    result = aggregate_news(news, reference_date=date(2026, 6, 21))
    assert abs(result["sentiment"] - 0.622) < 0.005


def test_exponential_decay_over_days():
    # News from 4 days ago vs today
    news = [
        {
            "published_at": "2026-06-21T12:00:00",  # today
            "source": "36氪快讯",                  # weight 1.0
            "sentiment": 1.0,
            "confidence": 1.0,
        },
        {
            "published_at": "2026-06-17T12:00:00",  # 4 days ago (relative to end of 2026-06-21, i.e. 2026-06-21T23:59:59)
            "source": "36氪快讯",                  # weight 1.0
            "sentiment": 0.0,
            "confidence": 1.0,
        },
    ]

    # ref_datetime is 2026-06-22 23:59:59
    # age1 = (2026-06-22 23:59:59 - 2026-06-21 12:00:00) = 35.99 hours = 1.5 days
    # w1 = 1.0 * exp(-0.25 * 1.5) = exp(-0.375) = 0.687289
    # age2 = (2026-06-22 23:59:59 - 2026-06-17 12:00:00) = 5.5 days
    # w2 = 1.0 * exp(-0.25 * 5.5) = exp(-1.375) = 0.252848
    # Expected Sentiment = (1.0 * w1 + 0.0 * w2) / (w1 + w2) = w1 / (w1 + w2) = 0.6873 / (0.6873 + 0.2528) = 0.6873 / 0.9401 = 0.731
    result = aggregate_news(news, reference_date=date(2026, 6, 22))
    assert abs(result["sentiment"] - 0.731) < 0.005
