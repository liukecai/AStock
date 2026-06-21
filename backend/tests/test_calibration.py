from __future__ import annotations

import pandas as pd
import pytest

from app.config import settings
from app.services.calibration import calibrate_from_backtest, save_calibration
from app.services.scoring import build_signal


def _summary(periods: int = 30) -> dict:
    return {
        "ic": [
            {
                "factor": "trend_score",
                "mean_ic": 0.12,
                "positive_rate": 0.7,
                "periods": periods,
            },
            {
                "factor": "sentiment_score",
                "mean_ic": 0.06,
                "positive_rate": 0.6,
                "periods": periods,
            },
            {
                "factor": "volume_score",
                "mean_ic": 0.02,
                "positive_rate": 0.55,
                "periods": periods,
            },
        ]
    }


def _trades(size: int = 200) -> pd.DataFrame:
    scores = [value / (size - 1) * 100 for value in range(size)]
    return pd.DataFrame(
        {
            "trend_score": scores,
            "sentiment_score": [value * 0.8 for value in scores],
            "volume_score": [value * 0.6 for value in scores],
            "forward_return": [value / 10_000 for value in range(size)],
            "excluded_reason": [""] * size,
        }
    )


def test_calibration_uses_positive_ic_and_updates_scoring(tmp_path):
    calibration = calibrate_from_backtest(_summary(), _trades())
    weights = calibration["factor_weights"]
    assert weights["trend_score"] > weights["sentiment_score"] > weights["volume_score"]
    assert abs(sum(weights.values()) - 1) < 1e-9

    path = tmp_path / "calibration.json"
    save_calibration(calibration, path)
    original_path = settings.calibration_path
    object.__setattr__(settings, "calibration_path", path)
    try:
        signal = build_signal(
            "000001",
            "2026-01-01",
            {"trend_score": 80, "volume_ratio": 1.0, "bullish": True},
            {
                "sentiment": 0.5,
                "burst": 0,
                "event_counts": {},
            },
        )
        assert signal["metrics"]["calibration_source"] == "historical_backtest_ic"
        assert signal["metrics"]["factor_weights"] == weights
    finally:
        object.__setattr__(settings, "calibration_path", original_path)


def test_calibration_rejects_insufficient_ic_history():
    with pytest.raises(ValueError, match="IC 样本期不足"):
        calibrate_from_backtest(_summary(periods=1), _trades())
