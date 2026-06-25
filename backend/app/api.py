from __future__ import annotations

import secrets
import json
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from . import db
from .config import settings
from .services.pipeline import run_signal_pipeline

router = APIRouter(prefix="/api")

# Board filter SQL fragments — use SIMILAR TO for PostgreSQL, GLOB for SQLite.
# These are embedded directly in SQL so must not contain user input.
_GLOB_OR_LIKE = {
    # (sqlite_glob_pattern, pg_similar_to_pattern)
    "沪A": ("60[0135]*", "60[0135]%"),
    "深A": ("00[0123]*", "00[0123]%"),
    "创业板": ("30[01]*", "30[01]%"),
    "科创板": ("68[89]*", "68[89]%"),
}


def _board_clause(board: str) -> str | None:
    """Return the WHERE sub-clause for the given board name."""
    from . import db as _db
    mapping = _GLOB_OR_LIKE.get(board)
    if not mapping:
        return None
    sqlite_pat, pg_pat = mapping
    if _db._is_pg():
        return f"s.symbol LIKE '{pg_pat}'"
    return f"s.symbol GLOB '{sqlite_pat}'"


MARKET_BOARD_SQL = {
    "沪A": "沪A",
    "深A": "深A",
    "创业板": "创业板",
    "科创板": "科创板",
}


def _market_board(symbol: str) -> str:
    if symbol.startswith(("688", "689")):
        return "科创板"
    if symbol.startswith(("300", "301")):
        return "创业板"
    if symbol.startswith(("000", "001", "002", "003")):
        return "深A"
    if symbol.startswith(("600", "601", "603", "605")):
        return "沪A"
    return "其他"


def _decode_signal(item: dict) -> dict:
    item["metrics"] = json.loads(item["metrics"])
    item["research_weight_pct"] = item["metrics"].get("research_weight_pct", 0)
    item["market_board"] = _market_board(item["symbol"])
    return item


def _require_admin(x_admin_secret: Annotated[str | None, Header()] = None) -> None:
    if not settings.admin_secret:
        return
    if not x_admin_secret or not secrets.compare_digest(
        x_admin_secret, settings.admin_secret
    ):
        raise HTTPException(status_code=403, detail="当前操作需要管理授权")


@router.get("/admin/auth-status")
def admin_auth_status() -> dict:
    return {"required": bool(settings.admin_secret)}


@router.post("/admin/authorize")
def authorize_admin(
    x_admin_secret: Annotated[str | None, Header()] = None,
) -> dict:
    _require_admin(x_admin_secret)
    return {"status": "ok"}


@router.get("/health")
def health() -> dict:
    job = db.row("SELECT * FROM jobs WHERE name='market_update'")
    if job:
        job["details"] = json.loads(job["details"])

    # Event statistics
    event_count = db.row("SELECT COUNT(*) AS count FROM events")["count"]
    score_count = db.row("SELECT COUNT(*) AS count FROM event_stock_scores")["count"]
    comm_stats_raw = db.rows("SELECT commodity, COUNT(*) AS count FROM commodity_impacts GROUP BY commodity")
    commodity_stats = {row["commodity"]: row["count"] for row in comm_stats_raw}

    return {
        "status": "ok",
        "provider": "akshare",
        "news_provider": "cninfo+rsshub",
        "latest_trade_date": db.latest_trade_date(),
        "stock_count": db.row("SELECT COUNT(*) AS count FROM stocks")["count"],
        "news_count": db.row("SELECT COUNT(*) AS count FROM news_items")["count"],
        "news_link_count": db.row(
            "SELECT COUNT(*) AS count FROM news_stock_links"
        )["count"],
        "market_job": job,
        "event_stats": {
            "event_count": event_count,
            "stock_score_count": score_count,
            "by_commodity": commodity_stats
        }
    }


@router.get("/dashboard")
def dashboard(
    status: Annotated[str | None, Query()] = None,
    board: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=10000)] = 100,
) -> dict:
    latest = db.row("SELECT MAX(signal_date) AS value FROM signals")
    signal_date = latest["value"] if latest else None
    if not signal_date:
        return {
            "signal_date": None,
            "signals": [],
            "summary": {},
            "pagination": {"page": page, "limit": limit, "total": 0, "total_pages": 0},
        }

    # Macro statistics for the day based on all signals for the signal_date
    all_signals = db.rows(
        "SELECT total_score, burst, metrics FROM signals WHERE signal_date=?",
        (signal_date,),
    )
    total_universe = len(all_signals)
    bullish_count = 0
    hot_count = 0
    total_score_sum = 0.0
    for s in all_signals:
        total_score_sum += s["total_score"]
        if s["burst"] >= 3:
            hot_count += 1
        metrics = json.loads(s["metrics"])
        if metrics.get("bullish"):
            bullish_count += 1
    average_score = round(total_score_sum / max(total_universe, 1), 2)

    # Filtering logic
    where_clause = "WHERE s.signal_date=?"
    params = [signal_date]
    if status and status != "全部":
        where_clause += " AND s.status=?"
        params.append(status)
    if board and board != "全部":
        board_clause = _board_clause(board)
        if not board_clause:
            raise HTTPException(status_code=422, detail="不支持的板块筛选")
        where_clause += f" AND {board_clause}"

    total_filtered = db.row(
        f"""
        SELECT COUNT(*) AS count
        FROM signals s
        {where_clause}
        """,
        tuple(params),
    )["count"]

    offset = (page - 1) * limit
    items = db.rows(
        f"""
        SELECT s.*, st.name, st.industry
        FROM signals s JOIN stocks st USING(symbol)
        {where_clause}
        ORDER BY s.total_score DESC LIMIT ? OFFSET ?
        """,
        (*params, limit, offset),
    )
    decoded = [_decode_signal(item) for item in items]

    return {
        "signal_date": signal_date,
        "signals": decoded,
        "summary": {
            "stock_count": total_universe,
            "bullish_count": bullish_count,
            "hot_count": hot_count,
            "average_score": average_score,
        },
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_filtered,
            "total_pages": (total_filtered + limit - 1) // limit if total_filtered > 0 else 0,
        },
    }


@router.get("/stocks/today")
def stocks_today(
    top_n: Annotated[int, Query(ge=1, le=10000)] = 100
) -> dict:
    """Compatibility endpoint for today's ranked Top N research list."""

    return dashboard(limit=top_n)


@router.get("/signal")
def signal(
    symbol: Annotated[str | None, Query(min_length=6, max_length=6)] = None,
    limit: Annotated[int, Query(ge=1, le=10000)] = 100,
) -> dict:
    if symbol:
        item = db.row(
            """
            SELECT s.*, st.name, st.industry
            FROM signals s JOIN stocks st USING(symbol)
            WHERE s.symbol=? ORDER BY s.signal_date DESC LIMIT 1
            """,
            (symbol,),
        )
        if not item:
            raise HTTPException(status_code=404, detail="暂无该股票信号")
        return _decode_signal(item)
    return dashboard(limit=limit)


@router.get("/stocks/{symbol}")
def stock_detail(symbol: str) -> dict:
    stock = db.row("SELECT * FROM stocks WHERE symbol=?", (symbol,))
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")
    prices = db.rows(
        """
        SELECT trade_date, open, high, low, close, volume, amount
        FROM daily_prices WHERE symbol=? ORDER BY trade_date DESC LIMIT 120
        """,
        (symbol,),
    )
    prices.reverse()
    news = db.rows(
        """
        SELECT n.published_at, n.title, n.summary, n.source, n.source_type,
               n.language, n.region, n.url, n.sentiment, n.event_type, n.keywords,
               l.confidence, l.match_type
        FROM news_items n
        JOIN news_stock_links l ON l.news_id=n.id
        WHERE l.symbol=?
        ORDER BY n.published_at DESC LIMIT 50
        """,
        (symbol,),
    )
    for item in news:
        item["keywords"] = json.loads(item["keywords"])
    signal = db.row(
        "SELECT * FROM signals WHERE symbol=? ORDER BY signal_date DESC LIMIT 1",
        (symbol,),
    )
    return {
        "stock": stock,
        "prices": prices,
        "news": news,
        "signal": _decode_signal(signal) if signal else None,
    }


@router.post("/pipeline/run")
def run_pipeline(
    x_admin_secret: Annotated[str | None, Header()] = None,
) -> dict:
    _require_admin(x_admin_secret)
    return run_signal_pipeline()


class CreateLinkRequest(BaseModel):
    news_id: str
    symbol: str
    confidence: float = 1.0
    match_type: str = "manual"


@router.get("/news-links")
def get_news_links(
    symbol: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> dict:
    where_clauses = []
    params = []
    if symbol:
        where_clauses.append("l.symbol = ?")
        params.append(symbol)

    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    offset = (page - 1) * limit

    query = f"""
        SELECT l.news_id, l.symbol, l.confidence, l.match_type,
               n.title, n.source, n.published_at
        FROM news_stock_links l
        JOIN news_items n ON l.news_id = n.id
        {where_str}
        ORDER BY n.published_at DESC
        LIMIT ? OFFSET ?
    """
    rows = db.rows(query, (*params, limit, offset))

    total_query = f"""
        SELECT COUNT(*) as count
        FROM news_stock_links l
        {where_str}
    """
    total = db.row(total_query, tuple(params))["count"]

    return {
        "links": rows,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0
        }
    }


@router.post("/news-links")
def create_news_link(
    req: CreateLinkRequest,
    x_admin_secret: Annotated[str | None, Header()] = None,
) -> dict:
    _require_admin(x_admin_secret)
    stock = db.row("SELECT symbol FROM stocks WHERE symbol=?", (req.symbol,))
    if not stock:
        raise HTTPException(status_code=404, detail="该股票不存在于股票池中")

    news = db.row("SELECT id FROM news_items WHERE id=?", (req.news_id,))
    if not news:
        raise HTTPException(status_code=404, detail="新闻条目不存在")

    db.upsert_news_links([{
        "news_id": req.news_id,
        "symbol": req.symbol,
        "confidence": req.confidence,
        "match_type": req.match_type
    }])
    return {"status": "ok"}


@router.delete("/news-links")
def delete_news_link(
    news_id: Annotated[str, Query()],
    symbol: Annotated[str, Query()],
    x_admin_secret: Annotated[str | None, Header()] = None,
) -> dict:
    _require_admin(x_admin_secret)
    with db.connect() as conn:
        conn.execute(
            "DELETE FROM news_stock_links WHERE news_id=? AND symbol=?",
            (news_id, symbol)
        )
    return {"status": "ok"}


@router.get("/news")
def get_recent_news(
    limit: Annotated[int, Query(ge=1, le=100)] = 50
) -> list[dict]:
    return db.rows(
        "SELECT * FROM news_items ORDER BY published_at DESC LIMIT ?",
        (limit,)
    )


@router.get("/jobs")
def jobs() -> list[dict]:
    items = db.rows("SELECT * FROM jobs ORDER BY name")
    # Try to enrich with next_run_time from APScheduler
    next_run_map: dict[str, str | None] = {}
    try:
        from .main import scheduler
        _JOB_ID_MAP = {
            "market_update": "daily-market-update",
            "signal_pipeline": "daily-signals",
            "rss_news_update": "hourly-rss-news",
            "cninfo_update": "daily-cninfo-update",
        }
        for name, job_id in _JOB_ID_MAP.items():
            job = scheduler.get_job(job_id)
            if job and job.next_run_time:
                next_run_map[name] = job.next_run_time.isoformat()
            else:
                next_run_map[name] = None
    except Exception:
        pass  # Scheduler not running in test/dev environment

    for item in items:
        item["details"] = json.loads(item["details"])
        item["next_run_time"] = next_run_map.get(item["name"])
    return items


# Supported job names → (function_to_call, display_name)
_RETRY_JOBS: dict[str, tuple] = {}

def _get_retry_jobs() -> dict[str, tuple]:
    """Lazy-import to avoid circular imports at module load time."""
    global _RETRY_JOBS
    if not _RETRY_JOBS:
        from .services.market import update_market_data
        from .services.pipeline import run_signal_pipeline
        from .services.rss_news import update_rss_news
        from .services.announcements import update_cninfo_announcements
        _RETRY_JOBS = {
            "market_update": (update_market_data, "行情更新"),
            "signal_pipeline": (run_signal_pipeline, "信号计算"),
            "rss_news_update": (update_rss_news, "RSS 新闻采集"),
            "cninfo_update": (update_cninfo_announcements, "巨潮公告采集"),
        }
    return _RETRY_JOBS


@router.post("/jobs/{name}/retry")
def retry_job(
    name: str,
    x_admin_secret: Annotated[str | None, Header()] = None,
) -> dict:
    """Manually trigger a scheduled job by name.

    Requires X-Admin-Secret header. Runs the job in a background thread
    and returns immediately — use GET /jobs to monitor progress.
    """
    _require_admin(x_admin_secret)
    retry_jobs = _get_retry_jobs()
    if name not in retry_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"未知任务: {name}。支持的任务: {list(retry_jobs.keys())}",
        )
    fn, display_name = retry_jobs[name]
    import threading
    t = threading.Thread(target=fn, name=f"manual-retry-{name}", daemon=True)
    t.start()
    return {"status": "started", "job": name, "display_name": display_name}


# Event APIs
class AnalyzeEventRequest(BaseModel):
    news_id: str | None = Field(default=None, min_length=1, max_length=200)
    title: str | None = Field(default=None, min_length=1, max_length=500)
    summary: str | None = Field(default=None, max_length=20_000)
    time: datetime | None = None

    @model_validator(mode="after")
    def require_source(self) -> "AnalyzeEventRequest":
        if not self.news_id and not self.title:
            raise ValueError("必须提供 news_id 或 title")
        return self


@router.post("/events/analyze")
def analyze_event(
    req: AnalyzeEventRequest,
    x_admin_secret: Annotated[str | None, Header()] = None,
) -> dict:
    _require_admin(x_admin_secret)
    title = req.title
    summary = req.summary or ""
    published_at = req.time.isoformat() if req.time else None
    news_id = req.news_id

    if news_id:
        news = db.row("SELECT * FROM news_items WHERE id=?", (news_id,))
        if not news:
            raise HTTPException(status_code=404, detail="新闻未找到")
        title = news["title"]
        summary = news["summary"] or ""
        published_at = news["published_at"]

    from .services.event_engine import analyze_event_text
    result = analyze_event_text(title, summary, published_at, news_id)
    if not result:
        raise HTTPException(status_code=422, detail="未能从文本中识别出商品因果事件链")

    return result


@router.get("/events")
def get_events(
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    commodity: Annotated[
        Literal["tungsten", "WF6", "oil", "copper", "gold", "lithium"] | None,
        Query(),
    ] = None,
    event_type: Annotated[
        Literal["geo_conflict", "supply_shock", "policy_change", "disruption"] | None,
        Query(),
    ] = None,
    direction: Annotated[Literal["benefit", "harm"] | None, Query()] = None,
) -> dict:
    where_clauses = []
    params = []

    if commodity:
        where_clauses.append("e.id IN (SELECT event_id FROM commodity_impacts WHERE commodity=?)")
        params.append(commodity)
    if event_type:
        where_clauses.append("e.event_type = ?")
        params.append(event_type)
    if direction:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM event_stock_scores ess "
            "WHERE ess.event_id=e.id AND ess.direction=?)"
        )
        params.append(direction)

    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    offset = (page - 1) * limit

    # Count total
    total_query = f"SELECT COUNT(*) AS count FROM events e {where_str}"
    total = db.row(total_query, tuple(params))["count"]

    # Select events
    query = f"""
        SELECT e.* FROM events e
        {where_str}
        ORDER BY e.published_at DESC
        LIMIT ? OFFSET ?
    """
    event_rows = db.rows(query, (*params, limit, offset))

    # Hydrate events with impacts
    events_hydrated = []
    for ev in event_rows:
        ev_dict = dict(ev)
        ev_dict["commodity_impacts"] = db.rows(
            "SELECT commodity, impact_type, direction FROM commodity_impacts WHERE event_id=?",
            (ev_dict["id"],)
        )
        events_hydrated.append(ev_dict)

    return {
        "events": events_hydrated,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0
        }
    }


@router.get("/events/{event_id}")
def get_event_detail(event_id: str) -> dict:
    from .services.event_engine import get_event_detail_by_id
    detail = get_event_detail_by_id(event_id)
    if not detail:
        raise HTTPException(status_code=404, detail="事件不存在")
    return detail


@router.get("/events/{event_id}/reaction")
def get_event_reaction_v2_endpoint(event_id: str) -> dict:
    from .services.transmission_engine import get_event_reactions_v2
    res = get_event_reactions_v2(event_id)
    if not res:
        raise HTTPException(status_code=404, detail="事件不存在")
    return res


@router.get("/stocks/{symbol}/commodity-exposure")
def get_stock_commodity_exposure_endpoint(symbol: str) -> dict:
    from .services.transmission_engine import get_stock_exposure_v2
    res = get_stock_exposure_v2(symbol)
    if not res:
        raise HTTPException(status_code=404, detail="该股票不存在或未配置商品画像")
    return res



@router.post("/events/rebuild")
def rebuild_events(
    x_admin_secret: Annotated[str | None, Header()] = None,
) -> dict:
    _require_admin(x_admin_secret)
    news_list = db.rows("SELECT id, title, summary, published_at FROM news_items")
    from .services.event_engine import analyze_event_text
    with db.connect() as conn:
        conn.execute("DELETE FROM events WHERE news_id IS NOT NULL")
    processed = 0
    created = 0
    for news in news_list:
        processed += 1
        res = analyze_event_text(
            title=news["title"],
            summary=news["summary"] or "",
            published_at=news["published_at"],
            news_id=news["id"]
        )
        if res:
            created += 1
    return {"status": "ok", "processed": processed, "events_created": created}
