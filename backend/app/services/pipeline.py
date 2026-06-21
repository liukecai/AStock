from __future__ import annotations

import json
from datetime import date, datetime

import pandas as pd

from .. import db
from .scoring import build_signal
from .sentiment import aggregate_news
from .trend import calculate_trend


def run_signal_pipeline() -> dict[str, int | str]:
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

    for item in symbols:
        symbol = item["symbol"]
        price_rows = db.rows(
            """
            SELECT trade_date, open, high, low, close, volume
            FROM daily_prices WHERE symbol=? ORDER BY trade_date DESC LIMIT 160
            """,
            (symbol,),
        )
        try:
            trend = calculate_trend(pd.DataFrame(price_rows))
            news_rows = db.rows(
                """
                SELECT n.published_at, n.title, n.source, n.source_type, n.url,
                       n.sentiment, n.keywords, l.confidence
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
                news_rows, reference_date=date.fromisoformat(signal_date)
            )
            db.save_signal(build_signal(symbol, signal_date, trend, sentiment))
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
    return result
