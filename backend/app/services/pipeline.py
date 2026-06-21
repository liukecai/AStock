from __future__ import annotations

import json
from datetime import date, datetime

import pandas as pd

from .. import db
from .scoring import build_signal
from .sentiment import aggregate_news
from .trend import calculate_trend
from .lake import export_parquet_snapshots


def run_signal_pipeline() -> dict[str, int | str]:
    db.init_db()
    symbols = db.rows("SELECT symbol FROM stocks ORDER BY symbol")
    started_at = datetime.now().replace(microsecond=0).isoformat()
    db.update_job(
        "signal_pipeline",
        "running",
        total=len(symbols),
        message="正在计算趋势与综合评分",
        started_at=started_at,
    )
    processed = 0
    failed = 0
    signal_date = db.latest_trade_date() or date.today().isoformat()

    # Load industries for neutralization
    stock_industries = {
        row["symbol"]: row["industry"] for row in db.rows("SELECT symbol, industry FROM stocks")
    }

    raw_signals = []

    try:
        for item in symbols:
            symbol = item["symbol"]
            price_rows = db.rows(
                """
                SELECT trade_date, open, high, low, close, volume, amount
                FROM daily_prices WHERE symbol=? ORDER BY trade_date DESC LIMIT 160
                """,
                (symbol,),
            )
            try:
                # Extract previous 5 trading dates for trading-day sequence Burst calculation
                trade_dates = [r["trade_date"] for r in price_rows]
                if trade_dates and trade_dates[0] == signal_date:
                    prev_trade_dates = trade_dates[1:6]
                else:
                    prev_trade_dates = trade_dates[:5]

                trend = calculate_trend(pd.DataFrame(price_rows))
                news_rows = db.rows(
                    """
                    SELECT n.published_at, n.title, n.source, n.source_type, n.url,
                           n.sentiment, n.event_type, n.keywords, l.confidence
                    FROM news_items n
                    JOIN news_stock_links l ON l.news_id=n.id
                    WHERE l.symbol=?
                    ORDER BY n.published_at DESC LIMIT 200
                    """,
                    (symbol,),
                )
                for news in news_rows:
                    news["keywords"] = json.loads(news["keywords"])

                sentiment = aggregate_news(
                    news_rows,
                    reference_date=date.fromisoformat(signal_date),
                    prev_trade_dates=prev_trade_dates
                )

                sig = build_signal(symbol, signal_date, trend, sentiment)
                raw_signals.append(sig)
                processed += 1
            except (ValueError, KeyError):
                failed += 1
            current = processed + failed
            if current % 50 == 0 or current == len(symbols):
                db.update_job(
                    "signal_pipeline",
                    "running",
                    current=current,
                    total=len(symbols),
                    message=f"已计算 {current}/{len(symbols)}",
                    started_at=started_at,
                )

        # Calculate industry means and apply neutralization
        from collections import defaultdict
        import numpy as np

        industry_scores = defaultdict(lambda: {
            "trend": [], "sentiment": [], "volume": [], "total": []
        })
        for sig in raw_signals:
            sym = sig["symbol"]
            ind = stock_industries.get(sym, "未分类")
            industry_scores[ind]["trend"].append(sig["trend_score"])
            industry_scores[ind]["sentiment"].append(sig["sentiment_score"])
            industry_scores[ind]["volume"].append(sig["volume_score"])
            industry_scores[ind]["total"].append(sig["total_score"])

        industry_means = {}
        for ind, score_dict in industry_scores.items():
            industry_means[ind] = {
                "trend": np.mean(score_dict["trend"]) if score_dict["trend"] else 0.0,
                "sentiment": np.mean(score_dict["sentiment"]) if score_dict["sentiment"] else 0.0,
                "volume": np.mean(score_dict["volume"]) if score_dict["volume"] else 0.0,
                "total": np.mean(score_dict["total"]) if score_dict["total"] else 0.0,
            }

        for sig in raw_signals:
            sym = sig["symbol"]
            ind = stock_industries.get(sym, "未分类")
            means = industry_means[ind]
            sig["metrics"]["trend_score_neutral"] = round(sig["trend_score"] - means["trend"], 2)
            sig["metrics"]["sentiment_score_neutral"] = round(sig["sentiment_score"] - means["sentiment"], 2)
            sig["metrics"]["volume_score_neutral"] = round(sig["volume_score"] - means["volume"], 2)
            sig["metrics"]["total_score_neutral"] = round(sig["total_score"] - means["total"], 2)
            db.save_signal(sig)

    except Exception as exc:
        db.update_job(
            "signal_pipeline",
            "failed",
            message=str(exc),
            details={"error": repr(exc)},
            started_at=started_at,
            finished_at=datetime.now().replace(microsecond=0).isoformat(),
        )
        raise

    result = {"signal_date": signal_date, "processed": processed, "failed": failed}
    db.update_job(
        "signal_pipeline",
        "completed",
        current=processed + failed,
        total=len(symbols),
        message=f"信号计算完成：成功 {processed}，跳过 {failed}",
        details=result,
        started_at=started_at,
        finished_at=datetime.now().replace(microsecond=0).isoformat(),
    )
    result["parquet"] = export_parquet_snapshots(
        ("factors/signals.parquet",)
    )
    return result
