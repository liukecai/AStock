from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FACTOR_COLUMNS = ("trend_score", "sentiment_score", "volume_score", "total_score")


@dataclass(frozen=True)
class BacktestConfig:
    holding_period: int = 5
    min_cross_section: int = 5
    max_exit_delay: int = 5
    transaction_cost_bps: float = 0.0


def _limit_ratio(symbol: str, trade_date: pd.Timestamp) -> float:
    symbol = str(symbol).zfill(6)
    if symbol.startswith(("4", "8", "92")):
        return 0.30
    if symbol.startswith("688"):
        return 0.20
    if symbol.startswith(("300", "301")) and trade_date >= pd.Timestamp("2020-08-24"):
        return 0.20
    return 0.10


def _prepare_prices(prices: pd.DataFrame) -> pd.DataFrame:
    aliases = {"code": "symbol", "date": "trade_date"}
    frame = prices.rename(columns=aliases).copy()
    required = {"symbol", "trade_date", "open", "high", "low", "close", "volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"daily_prices 缺少字段: {sorted(missing)}")
    frame["symbol"] = frame["symbol"].astype(str).str.zfill(6)
    frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    frame = frame.sort_values(["symbol", "trade_date"]).drop_duplicates(
        ["symbol", "trade_date"], keep="last"
    )
    frame["prev_close"] = frame.groupby("symbol", sort=False)["close"].shift(1)
    ratios = [
        _limit_ratio(symbol, trade_date)
        for symbol, trade_date in zip(frame["symbol"], frame["trade_date"])
    ]
    frame["limit_ratio"] = ratios
    frame["limit_up"] = frame["prev_close"] * (1 + frame["limit_ratio"])
    frame["limit_down"] = frame["prev_close"] * (1 - frame["limit_ratio"])
    tolerance = 1e-4
    active = frame["volume"].fillna(0).gt(0)
    frame["can_buy"] = (
        active
        & frame["prev_close"].notna()
        & frame["low"].lt(frame["limit_up"] * (1 - tolerance))
    )
    frame["can_sell"] = (
        active
        & frame["prev_close"].notna()
        & frame["high"].gt(frame["limit_down"] * (1 + tolerance))
    )
    return frame


def _prepare_signals(signals: pd.DataFrame) -> pd.DataFrame:
    frame = signals.copy()
    required = {"symbol", "signal_date", *FACTOR_COLUMNS}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"signals 缺少字段: {sorted(missing)}")
    frame["symbol"] = frame["symbol"].astype(str).str.zfill(6)
    frame["signal_date"] = pd.to_datetime(frame["signal_date"])
    return frame.sort_values(["signal_date", "symbol"]).drop_duplicates(
        ["signal_date", "symbol"], keep="last"
    )


def build_trade_panel(
    signals: pd.DataFrame,
    prices: pd.DataFrame,
    config: BacktestConfig | None = None,
) -> pd.DataFrame:
    """Align close-of-day signals to executable long trades without look-ahead."""

    config = config or BacktestConfig()
    if config.holding_period < 1:
        raise ValueError("holding_period 必须大于等于 1")
    signal_frame = _prepare_signals(signals)
    price_frame = _prepare_prices(prices)
    prices_by_symbol = {
        symbol: group.reset_index(drop=True)
        for symbol, group in price_frame.groupby("symbol", sort=False)
    }
    records: list[dict[str, Any]] = []
    for signal in signal_frame.to_dict("records"):
        symbol_prices = prices_by_symbol.get(signal["symbol"])
        if symbol_prices is None:
            continue
        entry_candidates = symbol_prices.index[
            symbol_prices["trade_date"].gt(signal["signal_date"])
        ]
        if len(entry_candidates) == 0:
            continue
        entry_index = int(entry_candidates[0])
        entry = symbol_prices.iloc[entry_index]
        record = {
            **signal,
            "entry_date": entry["trade_date"],
            "entry_price": float(entry["open"]),
            "entry_tradable": bool(entry["can_buy"]),
            "excluded_reason": "",
        }
        if not record["entry_tradable"]:
            record["excluded_reason"] = (
                "suspended" if float(entry["volume"]) <= 0 else "limit_up"
            )
            records.append(record)
            continue
        planned_exit_index = entry_index + config.holding_period - 1
        if planned_exit_index >= len(symbol_prices):
            continue
        exit_index = planned_exit_index
        last_exit_index = min(
            len(symbol_prices) - 1,
            planned_exit_index + config.max_exit_delay,
        )
        while (
            exit_index <= last_exit_index
            and not bool(symbol_prices.iloc[exit_index]["can_sell"])
        ):
            exit_index += 1
        if exit_index > last_exit_index:
            record["excluded_reason"] = "no_sell_window"
            records.append(record)
            continue
        exit_bar = symbol_prices.iloc[exit_index]
        gross_return = float(exit_bar["close"]) / record["entry_price"] - 1
        cost = config.transaction_cost_bps * 2 / 10_000
        record.update(
            {
                "exit_date": exit_bar["trade_date"],
                "exit_price": float(exit_bar["close"]),
                "exit_delay": exit_index - planned_exit_index,
                "forward_return": gross_return - cost,
            }
        )
        records.append(record)
    return pd.DataFrame.from_records(records)


def _spearman(group: pd.DataFrame, factor: str, min_size: int) -> float:
    valid = group[[factor, "forward_return"]].dropna()
    if len(valid) < min_size or valid[factor].nunique() < 2:
        return math.nan
    return float(valid[factor].rank().corr(valid["forward_return"].rank()))


def _max_drawdown(returns: pd.Series) -> float:
    wealth = (1 + returns.fillna(0)).cumprod()
    drawdown = wealth / wealth.cummax() - 1
    return float(drawdown.min()) if len(drawdown) else 0.0


def _performance(returns: pd.Series, holding_period: int) -> dict[str, float]:
    clean = returns.dropna()
    if clean.empty:
        return {"mean_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0}
    volatility = float(clean.std(ddof=1))
    periods_per_year = 252 / holding_period
    sharpe = (
        float(clean.mean()) / volatility * math.sqrt(periods_per_year)
        if volatility > 0
        else 0.0
    )
    return {
        "mean_return": float(clean.mean()),
        "sharpe": sharpe,
        "max_drawdown": _max_drawdown(clean),
    }


def run_backtest(
    signals: pd.DataFrame,
    prices: pd.DataFrame,
    config: BacktestConfig | None = None,
) -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    config = config or BacktestConfig()
    panel = build_trade_panel(signals, prices, config)
    if panel.empty:
        raise ValueError("signals 与 daily_prices 没有可对齐的后续交易日")
    excluded = panel["excluded_reason"].fillna("").ne("")
    executable = panel.loc[~excluded & panel["forward_return"].notna()].copy()
    if executable.empty:
        raise ValueError("没有满足涨跌停/停牌约束的可执行信号")

    ic_rows: list[dict[str, Any]] = []
    for signal_date, group in executable.groupby("signal_date", sort=True):
        for factor in FACTOR_COLUMNS:
            ic_rows.append(
                {
                    "signal_date": signal_date,
                    "factor": factor,
                    "ic": _spearman(group, factor, config.min_cross_section),
                    "sample_size": len(group),
                }
            )
    ic = pd.DataFrame(ic_rows)
    ic_summary = []
    for factor, group in ic.groupby("factor", sort=False):
        values = group["ic"].dropna()
        std = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        ic_summary.append(
            {
                "factor": factor,
                "mean_ic": float(values.mean()) if len(values) else 0.0,
                "ic_ir": float(values.mean() / std) if std > 0 else 0.0,
                "positive_rate": float(values.gt(0).mean()) if len(values) else 0.0,
                "periods": int(len(values)),
            }
        )

    quintile_rows: list[dict[str, Any]] = []
    for signal_date, group in executable.groupby("signal_date", sort=True):
        for factor_name in FACTOR_COLUMNS:
            ranked = group[[factor_name, "forward_return"]].dropna().copy()
            if len(ranked) < 5 or ranked[factor_name].nunique() < 2:
                continue
            bins = min(5, len(ranked))
            ranked["quintile"] = (
                pd.qcut(
                    ranked[factor_name].rank(method="first"),
                    q=bins,
                    labels=False,
                )
                + 1
            )
            returns = ranked.groupby("quintile")["forward_return"].mean()
            for quintile, value in returns.items():
                quintile_rows.append(
                    {
                        "signal_date": signal_date,
                        "factor": factor_name,
                        "portfolio": f"Q{int(quintile)}",
                        "return": float(value),
                    }
                )
            if 1 in returns.index and bins in returns.index:
                quintile_rows.append(
                    {
                        "signal_date": signal_date,
                        "factor": factor_name,
                        "portfolio": "Q5-Q1",
                        "return": float(returns.loc[bins] - returns.loc[1]),
                    }
                )
    quintile_returns = pd.DataFrame(quintile_rows)
    performance_rows = []
    if not quintile_returns.empty:
        for (factor, portfolio), group in quintile_returns.groupby(
            ["factor", "portfolio"], sort=False
        ):
            performance_rows.append(
                {
                    "factor": factor,
                    "portfolio": portfolio,
                    **_performance(group.sort_values("signal_date")["return"], config.holding_period),
                    "periods": len(group),
                }
            )
    performance = pd.DataFrame(performance_rows)
    reason_counts = (
        panel.loc[excluded, "excluded_reason"].value_counts().astype(int).to_dict()
    )
    summary = {
        "config": asdict(config),
        "signals": int(len(panel)),
        "executable_signals": int(len(executable)),
        "excluded_signals": int(excluded.sum()),
        "excluded_reasons": reason_counts,
        "ic": ic_summary,
        "performance": performance.to_dict("records"),
    }
    return summary, {
        "trades": panel,
        "ic": ic,
        "quintile_returns": quintile_returns,
        "performance": performance,
    }


def run_backtest_from_parquet(
    signals_path: Path,
    prices_path: Path,
    output_dir: Path,
    config: BacktestConfig | None = None,
) -> dict[str, Any]:
    signals = pd.read_parquet(signals_path)
    prices = pd.read_parquet(prices_path)
    summary, frames = run_backtest(signals, prices, config)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_parquet(output_dir / f"{name}.parquet", index=False)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return summary
