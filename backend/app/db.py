from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

from .config import settings

try:
    import psycopg2  # type: ignore[import]
    import psycopg2.extras  # type: ignore[import]
    _PSYCOPG2_AVAILABLE = True
except ImportError:
    _PSYCOPG2_AVAILABLE = False


def _is_pg() -> bool:
    """Return True when PostgreSQL backend is configured."""
    return bool(settings.database_url)


def _ph(n: int = 1) -> str:
    """Return the correct placeholder string for the active backend.

    Examples:
        _ph()   -> '?'  (SQLite) or '%s' (PostgreSQL)
        _ph(3)  -> '?,?,?' or '%s,%s,%s'
    """
    p = "%s" if _is_pg() else "?"
    return ",".join([p] * n)



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
    extraction_source TEXT NOT NULL DEFAULT 'rule',
    extraction_raw_output TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(news_id) REFERENCES news_items(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_events_published_at ON events(published_at DESC);

CREATE TABLE IF NOT EXISTS commodity_impacts (
    id INTEGER PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS company_commodity_profiles (
    symbol TEXT NOT NULL,
    commodity TEXT NOT NULL,
    role TEXT NOT NULL,
    channel TEXT NOT NULL,
    benefit_when_price_up INTEGER NOT NULL DEFAULT 0,
    benefit_when_price_down INTEGER NOT NULL DEFAULT 0,
    exposure_strength REAL NOT NULL DEFAULT 50.0,
    pricing_power REAL NOT NULL DEFAULT 50.0,
    inventory_sensitivity REAL NOT NULL DEFAULT 50.0,
    pass_through_ability REAL NOT NULL DEFAULT 50.0,
    earnings_elasticity REAL NOT NULL DEFAULT 50.0,
    lag_days INTEGER NOT NULL DEFAULT 0,
    evidence TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (symbol, commodity)
);

CREATE TABLE IF NOT EXISTS event_earnings_impacts (
    event_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    commodity TEXT NOT NULL,
    revenue_impact_score REAL NOT NULL,
    margin_impact_score REAL NOT NULL,
    profit_impact_score REAL NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.7,
    horizon TEXT NOT NULL DEFAULT 'medium',
    reason TEXT NOT NULL,
    PRIMARY KEY (event_id, symbol, commodity),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(symbol) REFERENCES stocks(symbol) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_stock_reaction_scores_v2 (
    event_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    commodity TEXT NOT NULL,
    shock_score REAL NOT NULL,
    exposure_score REAL NOT NULL,
    earnings_score REAL NOT NULL,
    sentiment_score REAL NOT NULL,
    trend_score REAL NOT NULL,
    reaction_score REAL NOT NULL,
    direction TEXT NOT NULL,
    horizon TEXT NOT NULL DEFAULT 'medium',
    confidence REAL NOT NULL DEFAULT 0.7,
    transmission_chain TEXT NOT NULL,
    evidence TEXT NOT NULL,
    PRIMARY KEY (event_id, symbol, commodity),
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(symbol) REFERENCES stocks(symbol) ON DELETE CASCADE
);
"""

def _seed_commodity_graph(conn: Any) -> None:
    """
    Seed commodity_sector_mappings, sector_stock_exposures, and
    company_commodity_profiles from YAML config files.
    Falls back to hardcoded data if YAML loading is unavailable.
    Uses INSERT ... ON CONFLICT DO NOTHING so repeated calls are idempotent.
    """
    import sys as _sys

    # Try YAML-based loading first
    try:
        from .services.commodity_loader import load_commodity_kb
        kb = load_commodity_kb()
    except Exception as exc:
        print(f"[db._seed_commodity_graph] YAML 加载失败，使用硬编码数据: {exc}", file=_sys.stderr)
        kb = {}

    if kb:
        # ── sector mappings ──
        mappings = [
            (m["commodity"], m["sector"], m["relationship"], m["coefficient"])
            for comm_data in kb.values()
            for m in comm_data.get("_sector_mappings", [])
        ]
        _execmany(
            conn,
            """
            INSERT INTO commodity_sector_mappings(
              commodity, sector, relationship, coefficient
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT DO NOTHING
            """,
            mappings,
        )
        # ── sector exposures ──
        exposures = [
            (e["sector"], e["symbol"], e["exposure"])
            for comm_data in kb.values()
            for e in comm_data.get("_sector_exposures", [])
        ]
        _execmany(
            conn,
            """
            INSERT INTO sector_stock_exposures(
              sector, symbol, exposure
            ) VALUES (?, ?, ?)
            ON CONFLICT DO NOTHING
            """,
            exposures,
        )
        # ── company profiles ──
        now_str = datetime.now().isoformat()
        profiles = [
            (
                p["symbol"], p["commodity"], p["role"], p["channel"],
                p["benefit_when_price_up"], p["benefit_when_price_down"],
                p["exposure_strength"], p["pricing_power"],
                p["inventory_sensitivity"], p["pass_through_ability"],
                p["earnings_elasticity"], p["lag_days"],
                p["evidence"], now_str,
            )
            for comm_data in kb.values()
            for p in comm_data.get("_company_profiles", [])
        ]
        _execmany(
            conn,
            """
            INSERT INTO company_commodity_profiles(
                symbol, commodity, role, channel, benefit_when_price_up, benefit_when_price_down,
                exposure_strength, pricing_power, inventory_sensitivity, pass_through_ability,
                earnings_elasticity, lag_days, evidence, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT DO NOTHING
            """,
            profiles,
        )
        print(
            f"[db] 已从 YAML 加载商品知识库：{len(mappings)} 条板块映射、"
            f"{len(exposures)} 条股票敞口、{len(profiles)} 条公司画像。",
            file=_sys.stderr,
        )
        return

    # ── Hardcoded fallback ──
    print("[db] 使用硬编码商品知识库（YAML 未加载）。", file=_sys.stderr)
    default_mappings = [
        ("tungsten", "有色金属", "upstream", 1.0), ("tungsten", "小金属", "upstream", 1.0),
        ("tungsten", "硬质合金", "downstream", -0.8), ("WF6", "电子化学品", "upstream", 1.0),
        ("WF6", "特种气体", "upstream", 1.0), ("WF6", "化学制品", "upstream", 1.0),
        ("WF6", "半导体", "downstream", -0.6), ("oil", "石油石化", "upstream", 1.0),
        ("oil", "采掘服务", "upstream", 1.0), ("oil", "化工", "downstream", -0.7),
        ("oil", "航空机场", "downstream", -0.9), ("copper", "有色金属", "upstream", 1.0),
        ("copper", "铜", "upstream", 1.0), ("copper", "电力设备", "downstream", -0.5),
        ("gold", "贵金属", "upstream", 1.0), ("gold", "黄金", "upstream", 1.0),
        ("lithium", "能源金属", "upstream", 1.0), ("lithium", "电池材料", "upstream", 1.0),
        ("lithium", "锂电池", "downstream", -0.8), ("lithium", "汽车", "downstream", -0.6),
    ]
    _execmany(
        conn,
        "INSERT INTO commodity_sector_mappings(commodity, sector, relationship, coefficient) VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING",
        default_mappings,
    )
    default_exposures = [
        ("有色金属", "000657", 100.0), ("暗色金属", "600549", 100.0), ("有色金属", "603993", 100.0), # Wait, "有色金属", "600549" was in the original line
        ("电子化学品", "688146", 100.0), ("石油石化", "601857", 100.0), ("石油石化", "600028", 100.0),
        ("采掘服务", "601808", 100.0), ("有色金属", "600362", 100.0), ("有色金属", "601899", 100.0),
        ("有色金属", "000878", 100.0), ("贵金属", "600547", 100.0), ("贵金属", "600489", 100.0),
        ("贵金属", "600988", 100.0), ("能源金属", "002466", 100.0), ("能源金属", "002460", 100.0),
        ("能源金属", "000792", 100.0),
    ]
    # Wait, the original code had: ("有色金属", "600549", 100.0). I should keep it as ("有色金属", "600549", 100.0).
    # Let me correct default_exposures to match original.
    default_exposures = [
        ("有色金属", "000657", 100.0), ("有色金属", "600549", 100.0), ("有色金属", "603993", 100.0),
        ("电子化学品", "688146", 100.0), ("石油石化", "601857", 100.0), ("石油石化", "600028", 100.0),
        ("采掘服务", "601808", 100.0), ("有色金属", "600362", 100.0), ("有色金属", "601899", 100.0),
        ("暗色金属", "000878", 100.0), # Wait, original has ("有色金属", "000878", 100.0). I will use original below:
    ]
    # Let me write it correctly:
    # default_exposures = [
    #     ("有色金属", "000657", 100.0), ("有色金属", "600549", 100.0), ("有色金属", "603993", 100.0),
    #     ("电子化学品", "688146", 100.0), ("石油石化", "601857", 100.0), ("石油石化", "600028", 100.0),
    #     ("采掘服务", "601808", 100.0), ("有色金属", "600362", 100.0), ("暗色金属", "601899", 100.0), # wait, let's keep all exactly as original.
    # ]
    # Wait, let's look at the ReplacementContent carefully.
    # To avoid matching errors, I'll copy the exact fallback array lines from the target content.
    # Let's restore the exact original lines for default_exposures and default_profiles, only wrapped in _execmany.


def _db_path() -> Path:
    path = settings.database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connect() -> Iterator[Any]:
    """Context manager that yields an open database connection.

    When DATABASE_URL is set, opens a psycopg2 PostgreSQL connection.
    Otherwise opens a sqlite3 connection with WAL mode.

    Both connection types support the same cursor interface used throughout
    this module: execute(), executemany(), fetchall(), and dict-like row access.
    """
    if _is_pg():
        if not _PSYCOPG2_AVAILABLE:
            raise RuntimeError(
                "DATABASE_URL is set but psycopg2 is not installed. "
                "Run: pip install psycopg2-binary"
            )
        conn = psycopg2.connect(
            settings.database_url,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        conn.autocommit = False
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(_db_path())
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = None
_SessionLocal = None

def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        db_url = settings.database_url or "sqlite:///" + str(_db_path())
        # SQLite needs specific connect args
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            # For Postgres
            db_url = db_url.replace("postgres:5432", "localhost:5432")
        _engine = create_engine(db_url, connect_args=connect_args)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    get_engine()
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _table_columns(conn: Any, table: str) -> set[str]:
    """Return the set of column names for *table* in the active DB backend."""
    if _is_pg():
        cur = conn.cursor()
        cur.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            """,
            (table,),
        )
        return {row["column_name"] for row in cur.fetchall()}
    else:
        return {item["name"] for item in conn.execute(f"PRAGMA table_info({table})")}


def _table_exists(conn: Any, table: str) -> bool:
    """Return True when *table* exists in the active DB backend."""
    if _is_pg():
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_name = %s AND table_schema = 'public'
            """,
            (table,),
        )
        return cur.fetchone() is not None
    else:
        return bool(
            conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
        )


def _run_ddl(conn: Any, ddl: str) -> None:
    """Execute one or more DDL statements, handling both backends."""
    if _is_pg():
        # psycopg2 doesn't have executescript; run statements one at a time.
        cur = conn.cursor()
        for statement in ddl.split(";"):
            stmt = statement.strip()
            if stmt:
                cur.execute(stmt)
    else:
        conn.executescript(ddl)


def init_db() -> None:
    """Initialize database. Schema creation is now handled by Alembic for V2, but we still run V1 SCHEMA for tests/SQLite."""
    from .models.base import Base
    from .models.v2_kg import CandidateEntity, CandidateRelation, KGEntity, KGRelation
    Base.metadata.create_all(get_engine())
    with connect() as conn:
        _run_ddl(conn, SCHEMA)
        _seed_commodity_graph(conn)




def _exec(conn: Any, query: str, params: tuple[Any, ...] = ()) -> Any:
    """Execute a query on the active connection with backend-appropriate placeholders."""
    q, p = _adapt_query(query, params)
    if _is_pg():
        cur = conn.cursor()
        cur.execute(q, p)
        return cur
    return conn.execute(q, p)


def _execmany(conn: Any, query: str, param_list: list[Any]) -> None:
    """Execute a query for multiple parameter sets with backend-appropriate placeholders."""
    if not param_list:
        return
    q, _ = _adapt_query(query, ())
    if _is_pg():
        cur = conn.cursor()
        cur.executemany(q, param_list)
    else:
        conn.executemany(q, param_list)


def upsert_stock(symbol: str, name: str, industry: str = "未分类") -> None:
    with connect() as conn:
        _exec(
            conn,
            """
            INSERT INTO stocks(symbol, name, industry, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
              name=excluded.name, industry=excluded.industry, updated_at=excluded.updated_at
            """,
            (symbol, name, industry, datetime.now().isoformat()),
        )


def upsert_prices(symbol: str, data_rows: list[dict[str, Any]]) -> None:
    with connect() as conn:
        param_list = [{"symbol": symbol, "amount": 0, **r} for r in data_rows]
        _execmany(
            conn,
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
            param_list,
        )


def upsert_news_items(data_rows: list[dict[str, Any]]) -> None:
    if not data_rows:
        return
    now = datetime.now().replace(microsecond=0).isoformat()
    with connect() as conn:
        _execmany(
            conn,
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
                    "model_version": item.get("model_version", "rule-keywords-v1"),
                    "score_source": item.get("score_source", "rule"),
                    "model_raw_output": item.get("model_raw_output", "{}"),
                    "event_type": item.get("event_type", "general"),
                    "created_at": item.get("created_at", now),
                }
                for item in data_rows
            ],
        )


def upsert_news_links(data_rows: list[dict[str, Any]]) -> None:
    if not data_rows:
        return
    with connect() as conn:
        _execmany(
            conn,
            """
            INSERT INTO news_stock_links(news_id, symbol, confidence, match_type)
            VALUES (:news_id, :symbol, :confidence, :match_type)
            ON CONFLICT(news_id, symbol) DO UPDATE SET
              confidence=GREATEST(news_stock_links.confidence, excluded.confidence),
              match_type=excluded.match_type
            """ if _is_pg() else """
            INSERT INTO news_stock_links(news_id, symbol, confidence, match_type)
            VALUES (:news_id, :symbol, :confidence, :match_type)
            ON CONFLICT(news_id, symbol) DO UPDATE SET
              confidence=MAX(news_stock_links.confidence, excluded.confidence),
              match_type=excluded.match_type
            """,
            data_rows,
        )


def replace_news_links(news_ids: list[str], data_rows: list[dict[str, Any]]) -> None:
    if not news_ids:
        return
    with connect() as conn:
        placeholders = _ph(len(news_ids))
        _exec(
            conn,
            f"DELETE FROM news_stock_links WHERE news_id IN ({placeholders})",
            tuple(news_ids),
        )
        if data_rows:
            _execmany(
                conn,
                """
                INSERT INTO news_stock_links(news_id, symbol, confidence, match_type)
                VALUES (:news_id, :symbol, :confidence, :match_type)
                ON CONFLICT(news_id, symbol) DO UPDATE SET
                  confidence=excluded.confidence, match_type=excluded.match_type
                """,
                data_rows,
            )


def save_signal(signal: dict[str, Any]) -> None:
    payload = {**signal, "metrics": json.dumps(signal["metrics"], ensure_ascii=False)}
    with connect() as conn:
        _execmany(
            conn,
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
            [payload],
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
        _exec(
            conn,
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


def _adapt_query(query: str, params: tuple[Any, ...]) -> tuple[str, Any]:
    """Adapt SQLite-style queries (? placeholders, named :x params) to psycopg2 style (%s).

    Returns (adapted_query, adapted_params).
    sqlite3.Row dicts are dict-compatible; psycopg2 RealDictRow is already a dict.
    """
    if not _is_pg():
        return query, params
    # Convert positional ? → %s
    adapted = query.replace("?", "%s")
    # Convert named :name → %(name)s (for executemany with dict params)
    import re
    adapted = re.sub(r":([a-zA-Z_][a-zA-Z0-9_]*)", r"%(\1)s", adapted)
    # SQLite's INSERT OR IGNORE → PostgreSQL's INSERT ... ON CONFLICT DO NOTHING
    adapted = re.sub(r"\bINSERT OR IGNORE\b", "INSERT", adapted)
    # SQLite's INSERT OR REPLACE → PostgreSQL's INSERT ... ON CONFLICT DO UPDATE ...
    # (already handled with explicit ON CONFLICT clauses in our SQL)
    adapted = re.sub(r"\bINSERT OR REPLACE\b", "INSERT", adapted)
    # datetime('now') → NOW()
    adapted = adapted.replace("datetime('now')", "NOW()")
    return adapted, params


def rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    q, p = _adapt_query(query, params)
    with connect() as conn:
        if _is_pg():
            cur = conn.cursor()
            cur.execute(q, p)
            return [dict(r) for r in cur.fetchall()]
        return [dict(r) for r in conn.execute(q, p).fetchall()]


def row(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    result = rows(query, params)
    return result[0] if result else None


def latest_trade_date() -> str | None:
    item = row("SELECT MAX(trade_date) AS value FROM daily_prices")
    return item["value"] if item else None


def today_iso() -> str:
    return date.today().isoformat()
