from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from . import db
from .services.pipeline import run_signal_pipeline

router = APIRouter(prefix="/api")


def _decode_signal(item: dict) -> dict:
    item["metrics"] = json.loads(item["metrics"])
    item["research_weight_pct"] = item["metrics"].get("research_weight_pct", 0)
    return item


@router.get("/health")
def health() -> dict:
    job = db.row("SELECT * FROM jobs WHERE name='market_update'")
    if job:
        job["details"] = json.loads(job["details"])
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
    }


@router.get("/dashboard")
def dashboard(
    status: Annotated[str | None, Query()] = None,
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

    if status and status != "全部":
        total_filtered = db.row(
            "SELECT COUNT(*) AS count FROM signals WHERE signal_date=? AND status=?",
            (signal_date, status),
        )["count"]
    else:
        total_filtered = total_universe

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
def run_pipeline() -> dict:
    return run_signal_pipeline()


@router.get("/jobs")
def jobs() -> list[dict]:
    items = db.rows("SELECT * FROM jobs ORDER BY name")
    for item in items:
        item["details"] = json.loads(item["details"])
    return items
