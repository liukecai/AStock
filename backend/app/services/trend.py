from __future__ import annotations

import numpy as np
import pandas as pd


def _normalized_slope(values: pd.Series) -> float:
    clean = values.dropna().astype(float)
    if len(clean) < 2 or clean.mean() == 0:
        return 0.0
    x = np.arange(len(clean), dtype=float)
    return float(np.polyfit(x, clean.to_numpy(), 1)[0] / clean.mean())


def calculate_trend(prices: pd.DataFrame) -> dict[str, float | bool]:
    if len(prices) < 60:
        raise ValueError("至少需要 60 个交易日数据")

    frame = prices.sort_values("trade_date").copy()
    close = frame["close"].astype(float)
    volume = frame["volume"].astype(float)
    ma5 = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1]
    last_close = close.iloc[-1]
    price_slope20 = _normalized_slope(close.tail(20))
    ma60_series = close.rolling(60).mean().dropna()
    ma60_slope = _normalized_slope(ma60_series.tail(20))
    volume_ratio = float(volume.iloc[-1] / max(volume.tail(20).mean(), 1))
    momentum20 = float(last_close / close.iloc[-20] - 1)
    bullish = bool(ma5 > ma20 > ma60 and price_slope20 > 0 and last_close > ma60)

    structure = 1.0 if ma5 > ma20 > ma60 else 0.0
    slope_component = float(np.clip(price_slope20 * 120, 0, 1))
    volume_component = float(np.clip(volume_ratio / 2, 0, 1))
    trend_score = 100 * (
        0.40 * structure + 0.30 * slope_component + 0.30 * volume_component
    )

    return {
        "close": round(float(last_close), 3),
        "ma5": round(float(ma5), 3),
        "ma20": round(float(ma20), 3),
        "ma60": round(float(ma60), 3),
        "price_slope20": round(price_slope20, 6),
        "ma60_slope": round(ma60_slope, 6),
        "momentum20": round(momentum20, 4),
        "volume_ratio": round(volume_ratio, 3),
        "ma_structure_component": round(structure * 100, 2),
        "slope_component": round(slope_component * 100, 2),
        "trend_volume_component": round(volume_component * 100, 2),
        "bullish": bullish,
        "trend_score": round(float(np.clip(trend_score, 0, 100)), 2),
    }
