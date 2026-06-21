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
    amount REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (symbol, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_prices_symbol_date
ON daily_prices(symbol, trade_date DESC);

CREATE TABLE IF NOT EXISTS news_items (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'zh',
    region TEXT NOT NULL DEFAULT 'CN',
    published_at TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    url TEXT,
    sentiment REAL NOT NULL DEFAULT 0,
    model_version TEXT NOT NULL DEFAULT 'rule-keywords-v1',
    score_source TEXT NOT NULL DEFAULT 'rule'
        CHECK (score_source IN ('model', 'rule')),
    model_raw_output TEXT NOT NULL DEFAULT '{}',
    event_type TEXT NOT NULL DEFAULT 'general',
    keywords TEXT NOT NULL DEFAULT '[]',
    raw_payload TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_news_items_date
ON news_items(published_at DESC);

CREATE TABLE IF NOT EXISTS news_stock_links (
    news_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1,
    match_type TEXT NOT NULL DEFAULT 'symbol',
    PRIMARY KEY (news_id, symbol),
    FOREIGN KEY (news_id) REFERENCES news_items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_news_links_symbol
ON news_stock_links(symbol, news_id);

CREATE TABLE IF NOT EXISTS stock_aliases (
    alias TEXT NOT NULL,
    symbol TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'zh',
    confidence REAL NOT NULL DEFAULT 0.9,
    PRIMARY KEY (alias, symbol)
);

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

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    news_id TEXT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    event_type TEXT NOT NULL,
    subtype TEXT NOT NULL DEFAULT '',
    intensity REAL NOT NULL DEFAULT 0.0,
    direction TEXT NOT NULL CHECK (direction IN ('benefit', 'harm')),
    confidence REAL NOT NULL DEFAULT 1.0,
    published_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(news_id) REFERENCES news_items(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_events_published_at ON events(published_at DESC);

CREATE TABLE IF NOT EXISTS commodity_impacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    commodity TEXT NOT NULL,
    impact_type TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('benefit', 'harm')),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS commodity_sector_mappings (
    commodity TEXT NOT NULL,
    sector TEXT NOT NULL,
    relationship TEXT NOT NULL,
    coefficient REAL NOT NULL DEFAULT 1.0,
    PRIMARY KEY (commodity, sector)
);

CREATE TABLE IF NOT EXISTS sector_stock_exposures (
    sector TEXT NOT NULL,
    symbol TEXT NOT NULL,
    exposure REAL NOT NULL DEFAULT 100.0,
    PRIMARY KEY (sector, symbol)
);

CREATE TABLE IF NOT EXISTS event_stock_scores (
    event_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    event_score REAL NOT NULL,
    event_impact REAL NOT NULL,
    sector_exposure REAL NOT NULL,
    trend_strength REAL NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('benefit', 'harm')),
    causal_chain TEXT NOT NULL,
    evidence TEXT NOT NULL,
    PRIMARY KEY (event_id, symbol),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(symbol) REFERENCES stocks(symbol) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_event_stock_scores_score ON event_stock_scores(event_score DESC);
"""



def _db_path() -> Path:
    path = settings.database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        price_columns = {
            item["name"] for item in conn.execute("PRAGMA table_info(daily_prices)")
        }
        if "amount" not in price_columns:
            conn.execute(
                "ALTER TABLE daily_prices ADD COLUMN amount REAL NOT NULL DEFAULT 0"
            )
        news_columns = {
            item["name"] for item in conn.execute("PRAGMA table_info(news_items)")
        }
        if "event_type" not in news_columns:
            conn.execute(
                "ALTER TABLE news_items ADD COLUMN event_type TEXT NOT NULL DEFAULT 'general'"
            )
        if "model_version" not in news_columns:
            conn.execute(
                "ALTER TABLE news_items ADD COLUMN model_version TEXT NOT NULL "
                "DEFAULT 'rule-keywords-v1'"
            )
        if "score_source" not in news_columns:
            conn.execute(
                "ALTER TABLE news_items ADD COLUMN score_source TEXT NOT NULL "
                "DEFAULT 'rule'"
            )
        if "model_raw_output" not in news_columns:
            conn.execute(
                "ALTER TABLE news_items ADD COLUMN model_raw_output TEXT NOT NULL "
                "DEFAULT '{}'"
            )
        # Migration from the old news table to the unified news data layer if it exists
        old_table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='news'"
        ).fetchone()
        if old_table_exists:
            conn.execute(
                """
                INSERT OR IGNORE INTO news_items(
                  id, source, source_type, language, region, published_at, title,
                  summary, url, sentiment, keywords, raw_payload, created_at
                )
                SELECT id, source,
                  CASE WHEN source='巨潮资讯' THEN 'announcement' ELSE 'legacy' END,
                  'zh', 'CN', published_at, title, '', url, sentiment, keywords,
                  '{}', datetime('now')
                FROM news
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO news_stock_links(news_id, symbol, confidence, match_type)
                SELECT id, symbol, 1, 'legacy' FROM news
                """
            )
            conn.execute("DROP TABLE IF EXISTS news")
            conn.execute("DROP INDEX IF EXISTS idx_news_symbol_date")

        # Seeding static mappings and exposures for events
        default_mappings = [
            ("tungsten", "有色金属", "upstream", 1.0),
            ("tungsten", "小金属", "upstream", 1.0),
            ("tungsten", "硬质合金", "downstream", -0.8),
            ("WF6", "电子化学品", "upstream", 1.0),
            ("WF6", "特种气体", "upstream", 1.0),
            ("WF6", "化学制品", "upstream", 1.0),
            ("WF6", "半导体", "downstream", -0.6),
            ("oil", "石油石化", "upstream", 1.0),
            ("oil", "采掘服务", "upstream", 1.0),
            ("oil", "化工", "downstream", -0.7),
            ("oil", "航空机场", "downstream", -0.9),
            ("copper", "有色金属", "upstream", 1.0),
            ("copper", "铜", "upstream", 1.0),
            ("copper", "电力设备", "downstream", -0.5),
            ("gold", "贵金属", "upstream", 1.0),
            ("gold", "黄金", "upstream", 1.0),
            ("lithium", "能源金属", "upstream", 1.0),
            ("lithium", "电池材料", "upstream", 1.0),
            ("lithium", "锂电池", "downstream", -0.8),
            ("lithium", "汽车", "downstream", -0.6),
        ]
        conn.executemany(
            """
            INSERT OR IGNORE INTO commodity_sector_mappings(
              commodity, sector, relationship, coefficient
            ) VALUES (?, ?, ?, ?)
            """,
            default_mappings,
        )

        default_exposures = [
            ("有色金属", "000657", 100.0),
            ("有色金属", "600549", 100.0),
            ("有色金属", "603993", 100.0),
            ("电子化学品", "688146", 100.0),
            ("石油石化", "601857", 100.0),
            ("石油石化", "600028", 100.0),
            ("采掘服务", "601808", 100.0),
            ("有色金属", "600362", 100.0),
            ("有色金属", "601899", 100.0),
            ("有色金属", "000878", 100.0),
            ("贵金属", "600547", 100.0),
            ("贵金属", "600489", 100.0),
            ("贵金属", "600988", 100.0),
            ("能源金属", "002466", 100.0),
            ("能源金属", "002460", 100.0),
            ("能源金属", "000792", 100.0),
        ]
        conn.executemany(
            """
            INSERT OR IGNORE INTO sector_stock_exposures(
              sector, symbol, exposure
            ) VALUES (?, ?, ?)
            """,
            default_exposures,
        )



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
            INSERT INTO daily_prices(
              symbol, trade_date, open, high, low, close, volume, amount
            )
            VALUES (
              :symbol, :trade_date, :open, :high, :low, :close, :volume, :amount
            )
            ON CONFLICT(symbol, trade_date) DO UPDATE SET
              open=excluded.open, high=excluded.high, low=excluded.low,
              close=excluded.close, volume=excluded.volume, amount=excluded.amount
            """,
            [{"symbol": symbol, "amount": 0, **row} for row in rows],
        )


def upsert_news_items(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    now = datetime.now().replace(microsecond=0).isoformat()
    with connect() as conn:
        conn.executemany(
            """
            INSERT INTO news_items(
              id, source, source_type, language, region, published_at, title,
              summary, url, sentiment, model_version, score_source,
              model_raw_output, event_type, keywords, raw_payload, created_at
            ) VALUES (
              :id, :source, :source_type, :language, :region, :published_at, :title,
              :summary, :url, :sentiment, :model_version, :score_source,
              :model_raw_output, :event_type, :keywords, :raw_payload, :created_at
            )
            ON CONFLICT(id) DO UPDATE SET
              source=excluded.source, published_at=excluded.published_at,
              title=excluded.title, summary=excluded.summary, url=excluded.url,
              sentiment=excluded.sentiment, event_type=excluded.event_type,
              model_version=excluded.model_version,
              score_source=excluded.score_source,
              model_raw_output=excluded.model_raw_output,
              keywords=excluded.keywords,
              raw_payload=excluded.raw_payload
            """,
            [
                {
                    **item,
                    "model_version": item.get(
                        "model_version", "rule-keywords-v1"
                    ),
                    "score_source": item.get("score_source", "rule"),
                    "model_raw_output": item.get("model_raw_output", "{}"),
                    "event_type": item.get("event_type", "general"),
                    "created_at": item.get("created_at", now),
                }
                for item in rows
            ],
        )


def upsert_news_links(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with connect() as conn:
        conn.executemany(
            """
            INSERT INTO news_stock_links(news_id, symbol, confidence, match_type)
            VALUES (:news_id, :symbol, :confidence, :match_type)
            ON CONFLICT(news_id, symbol) DO UPDATE SET
              confidence=MAX(news_stock_links.confidence, excluded.confidence),
              match_type=excluded.match_type
            """,
            rows,
        )


def replace_news_links(news_ids: list[str], rows: list[dict[str, Any]]) -> None:
    if not news_ids:
        return
    with connect() as conn:
        placeholders = ",".join("?" for _ in news_ids)
        conn.execute(
            f"DELETE FROM news_stock_links WHERE news_id IN ({placeholders})",
            tuple(news_ids),
        )
        if rows:
            conn.executemany(
                """
                INSERT INTO news_stock_links(news_id, symbol, confidence, match_type)
                VALUES (:news_id, :symbol, :confidence, :match_type)
                ON CONFLICT(news_id, symbol) DO UPDATE SET
                  confidence=excluded.confidence, match_type=excluded.match_type
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
    if status == "failed":
        try:
            from .services.notifications import send_failure_notification
            send_failure_notification(name, message)
        except Exception as e:
            import sys
            print(f"Failed to trigger failure notification inside update_job: {e}", file=sys.stderr)


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
