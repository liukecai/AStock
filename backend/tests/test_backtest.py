from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.backtest import BacktestConfig, build_trade_panel, run_backtest


def _prices(symbols: list[str], periods: int = 10) -> pd.DataFrame:
    rows = []
    dates = pd.bdate_range("2026-01-01", periods=periods)
    for offset, symbol in enumerate(symbols):
        closes = 10 + offset + np.arange(periods) * (0.1 + offset * 0.1)
        for index, (trade_date, close) in enumerate(zip(dates, closes)):
            previous = closes[max(index - 1, 0)]
            rows.append(
                {
                    "code": symbol,
                    "date": trade_date,
                    "open": previous,
                    "high": max(previous, close) * 1.01,
                    "low": min(previous, close) * 0.99,
                    "close": close,
                    "volume": 1000,
                }
            )
    return pd.DataFrame(rows)


def _signals(symbols: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": symbol,
                "signal_date": "2026-01-02",
                "trend_score": rank,
                "sentiment_score": rank,
                "volume_score": rank,
                "total_score": rank,
            }
            for rank, symbol in enumerate(symbols, start=1)
        ]
    )


def test_entry_limit_up_is_excluded_and_limit_down_exit_is_delayed():
    symbols = ["000001", "000002"]
    prices = _prices(symbols)
    dates = sorted(prices["date"].unique())
    entry_date = dates[2]
    previous_close = prices.loc[
        (prices["code"] == "000001") & (prices["date"] == dates[1]), "close"
    ].iloc[0]
    limit_up = previous_close * 1.1
    prices.loc[
        (prices["code"] == "000001") & (prices["date"] == entry_date),
        ["open", "high", "low", "close"],
    ] = limit_up

    planned_exit = dates[3]
    previous_close = prices.loc[
        (prices["code"] == "000002") & (prices["date"] == entry_date), "close"
    ].iloc[0]
    limit_down = previous_close * 0.9
    prices.loc[
        (prices["code"] == "000002") & (prices["date"] == planned_exit),
        ["open", "high", "low", "close"],
    ] = limit_down

    panel = build_trade_panel(
        _signals(symbols),
        prices,
        BacktestConfig(holding_period=2),
    ).set_index("symbol")
    assert panel.loc["000001", "excluded_reason"] == "limit_up"
    assert panel.loc["000002", "exit_delay"] == 1


def test_backtest_calculates_ic_quintiles_and_performance():
    symbols = [f"{index:06d}" for index in range(1, 11)]
    summary, frames = run_backtest(
        _signals(symbols),
        _prices(symbols),
        BacktestConfig(holding_period=2, min_cross_section=5),
    )
    trend_ic = next(item for item in summary["ic"] if item["factor"] == "trend_score")
    assert trend_ic["mean_ic"] > 0.99
    assert summary["executable_signals"] == 10
    assert set(frames["quintile_returns"]["portfolio"]) >= {"Q1", "Q5", "Q5-Q1"}
    long_short = frames["performance"].query(
        "factor == 'trend_score' and portfolio == 'Q5-Q1'"
    ).iloc[0]
    assert long_short["mean_return"] > 0
