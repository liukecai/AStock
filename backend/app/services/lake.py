from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from ..config import settings


SNAPSHOTS = {
    "market/daily_prices.parquet": """
        SELECT symbol AS code, trade_date AS date, open, high, low, close,
               volume, amount
        FROM daily_prices ORDER BY symbol, trade_date
    """,
    "news/news_events.parquet": """
        SELECT id, source, source_type, language, region,
               published_at AS time, title, summary, url, sentiment,
               event_type, keywords
        FROM news_items ORDER BY published_at
    """,
    "news/news_stock_links.parquet": """
        SELECT news_id, symbol AS code, confidence, match_type
        FROM news_stock_links ORDER BY news_id, symbol
    """,
    "factors/signals.parquet": """
        SELECT * FROM signals ORDER BY signal_date, symbol
    """,
}


def export_parquet_snapshots(names: tuple[str, ...] | None = None) -> dict[str, int]:
    """Export canonical SQLite tables as portable Parquet snapshots."""

    if not settings.enable_parquet_snapshots:
        return {}
    selected = names or tuple(SNAPSHOTS)
    root = Path(settings.data_dir) / "parquet"
    root.mkdir(parents=True, exist_ok=True)
    result: dict[str, int] = {}
    with sqlite3.connect(settings.database_path) as conn:
        for name in selected:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            frame = pd.read_sql_query(SNAPSHOTS[name], conn)
            temporary = target.with_suffix(".tmp.parquet")
            frame.to_parquet(temporary, index=False)
            temporary.replace(target)
            result[name] = len(frame)
    return result

