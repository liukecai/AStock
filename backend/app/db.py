from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

from .config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS stocks (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT NOT NULL DEFAULT '未分类',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_prices (
    symbol TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    PRIMARY KEY (symbol, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_prices_symbol_date
ON daily_prices(symbol, trade_date DESC);

CREATE TABLE IF NOT EXISTS news (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    published_at TEXT NOT NULL,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT,
    sentiment REAL NOT NULL DEFAULT 0,
    keywords TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_news_symbol_date
ON news(symbol, published_at DESC);

CREATE TABLE IF NOT EXISTS signals (
    symbol TEXT NOT NULL,
    signal_date TEXT NOT NULL,
    trend_score REAL NOT NULL,
    sentiment_score REAL NOT NULL,
    volume_score REAL NOT NULL,
    total_score REAL NOT NULL,
    burst REAL NOT NULL,
    status TEXT NOT NULL,
    metrics TEXT NOT NULL,
    PRIMARY KEY (symbol, signal_date)
);

CREATE TABLE IF NOT EXISTS jobs (
    name TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    progress_current INTEGER NOT NULL DEFAULT 0,
    progress_total INTEGER NOT NULL DEFAULT 0,
    message TEXT NOT NULL DEFAULT '',
    details TEXT NOT NULL DEFAULT '{}'
);
"""


def _db_path() -> Path:
    path = settings.database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def upsert_stock(symbol: str, name: str, industry: str = "未分类") -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO stocks(symbol, name, industry, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
              name=excluded.name, industry=excluded.industry, updated_at=excluded.updated_at
            """,
            (symbol, name, industry, datetime.now().isoformat()),
        )


def upsert_prices(symbol: str, rows: list[dict[str, Any]]) -> None:
    with connect() as conn:
        conn.executemany(
            """
            INSERT INTO daily_prices(symbol, trade_date, open, high, low, close, volume)
            VALUES (:symbol, :trade_date, :open, :high, :low, :close, :volume)
            ON CONFLICT(symbol, trade_date) DO UPDATE SET
              open=excluded.open, high=excluded.high, low=excluded.low,
              close=excluded.close, volume=excluded.volume
            """,
            [{"symbol": symbol, **row} for row in rows],
        )


def upsert_news(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with connect() as conn:
        conn.executemany(
            """
            INSERT INTO news(id, symbol, published_at, title, source, url, sentiment, keywords)
            VALUES (:id, :symbol, :published_at, :title, :source, :url, :sentiment, :keywords)
            ON CONFLICT(id) DO UPDATE SET
              title=excluded.title, url=excluded.url, sentiment=excluded.sentiment,
              keywords=excluded.keywords
            """,
            rows,
        )


def save_signal(signal: dict[str, Any]) -> None:
    payload = {**signal, "metrics": json.dumps(signal["metrics"], ensure_ascii=False)}
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO signals(
              symbol, signal_date, trend_score, sentiment_score, volume_score,
              total_score, burst, status, metrics
            ) VALUES (
              :symbol, :signal_date, :trend_score, :sentiment_score, :volume_score,
              :total_score, :burst, :status, :metrics
            )
            ON CONFLICT(symbol, signal_date) DO UPDATE SET
              trend_score=excluded.trend_score,
              sentiment_score=excluded.sentiment_score,
              volume_score=excluded.volume_score,
              total_score=excluded.total_score,
              burst=excluded.burst,
              status=excluded.status,
              metrics=excluded.metrics
            """,
            payload,
        )


def update_job(
    name: str,
    status: str,
    *,
    current: int = 0,
    total: int = 0,
    message: str = "",
    details: dict[str, Any] | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO jobs(
              name, status, started_at, finished_at, progress_current,
              progress_total, message, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
              status=excluded.status,
              started_at=COALESCE(excluded.started_at, jobs.started_at),
              finished_at=excluded.finished_at,
              progress_current=excluded.progress_current,
              progress_total=excluded.progress_total,
              message=excluded.message,
              details=excluded.details
            """,
            (
                name,
                status,
                started_at,
                finished_at,
                current,
                total,
                message,
                json.dumps(details or {}, ensure_ascii=False),
            ),
        )


def rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def row(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    result = rows(query, params)
    return result[0] if result else None


def latest_trade_date() -> str | None:
    item = row("SELECT MAX(trade_date) AS value FROM daily_prices")
    return item["value"] if item else None


def today_iso() -> str:
    return date.today().isoformat()
