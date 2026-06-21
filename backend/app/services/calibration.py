from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


CALIBRATION_VERSION = 1
BASE_FACTORS = ("trend_score", "sentiment_score", "volume_score")
DEFAULT_WEIGHTS = {
    "trend_score": 0.5,
    "sentiment_score": 0.3,
    "volume_score": 0.2,
}
DEFAULT_THRESHOLDS = [60.0, 70.0, 80.0, 90.0]


def default_calibration() -> dict[str, Any]:
    return {
        "version": CALIBRATION_VERSION,
        "source": "default",
        "factor_weights": DEFAULT_WEIGHTS.copy(),
        "research_weight_thresholds": DEFAULT_THRESHOLDS.copy(),
    }


def _validate(payload: dict[str, Any]) -> dict[str, Any]:
    weights = payload.get("factor_weights", {})
    if set(weights) != set(BASE_FACTORS):
        raise ValueError("factor_weights 必须包含趋势、情绪、量能三个因子")
    values = np.array([float(weights[name]) for name in BASE_FACTORS])
    if not np.isfinite(values).all() or (values < 0).any() or values.sum() <= 0:
        raise ValueError("factor_weights 必须是非负有限数且总和大于 0")
    values = values / values.sum()
    thresholds = [float(value) for value in payload["research_weight_thresholds"]]
    if len(thresholds) != 4 or thresholds != sorted(thresholds):
        raise ValueError("research_weight_thresholds 必须是四个升序阈值")
    if len(set(thresholds)) != 4 or thresholds[0] < 0 or thresholds[-1] > 100:
        raise ValueError("研究权重阈值必须在 0–100 内严格递增")
    return {
        **payload,
        "version": int(payload.get("version", CALIBRATION_VERSION)),
        "factor_weights": dict(zip(BASE_FACTORS, values.tolist())),
        "research_weight_thresholds": thresholds,
    }


def load_calibration(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_calibration()
    return _validate(json.loads(path.read_text(encoding="utf-8")))


def calibrate_from_backtest(
    summary: dict[str, Any],
    trades: pd.DataFrame,
    *,
    min_ic_periods: int = 20,
    min_trades: int = 100,
) -> dict[str, Any]:
    ic_by_factor = {item["factor"]: item for item in summary.get("ic", [])}
    insufficient = {
        factor: int(ic_by_factor.get(factor, {}).get("periods", 0))
        for factor in BASE_FACTORS
        if int(ic_by_factor.get(factor, {}).get("periods", 0)) < min_ic_periods
    }
    executable = trades.loc[
        trades["excluded_reason"].fillna("").eq("")
        & trades["forward_return"].notna()
    ].copy()
    if insufficient:
        raise ValueError(
            f"IC 样本期不足，至少需要 {min_ic_periods} 期: {insufficient}"
        )
    if len(executable) < min_trades:
        raise ValueError(
            f"可执行交易样本不足，至少需要 {min_trades} 条，当前 {len(executable)} 条"
        )

    strengths = []
    for factor in BASE_FACTORS:
        item = ic_by_factor[factor]
        mean_ic = max(float(item["mean_ic"]), 0.0)
        positive_rate = max(float(item.get("positive_rate", 0.0)), 0.0)
        periods = int(item["periods"])
        shrinkage = periods / (periods + min_ic_periods)
        strengths.append(mean_ic * positive_rate * shrinkage)
    if sum(strengths) <= 0:
        raise ValueError("三个基础因子的样本外平均 IC 均不为正，拒绝生成新权重")
    weights = np.array(strengths) / sum(strengths)
    weight_map = dict(zip(BASE_FACTORS, weights.tolist()))
    executable["calibrated_score"] = sum(
        executable[factor].astype(float) * weight_map[factor]
        for factor in BASE_FACTORS
    )
    quantiles = executable["calibrated_score"].quantile([0.4, 0.6, 0.8, 0.9])
    thresholds = [round(float(value), 2) for value in quantiles]
    if len(set(thresholds)) != 4:
        raise ValueError("综合分分布过于集中，无法生成四个严格递增的研究权重阈值")
    calibration = {
        "version": CALIBRATION_VERSION,
        "source": "historical_backtest_ic",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "factor_weights": weight_map,
        "research_weight_thresholds": thresholds,
        "evidence": {
            "min_ic_periods": min_ic_periods,
            "ic": {factor: ic_by_factor[factor] for factor in BASE_FACTORS},
            "executable_trades": int(len(executable)),
            "score_quantiles": {
                str(index): float(value) for index, value in quantiles.items()
            },
        },
    }
    return _validate(calibration)


def save_calibration(payload: dict[str, Any], path: Path) -> None:
    validated = _validate(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.json")
    temporary.write_text(
        json.dumps(validated, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)
