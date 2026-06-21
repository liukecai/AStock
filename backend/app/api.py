from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query

from . import db
from .services.pipeline import run_signal_pipeline

router = APIRouter(prefix="/api")


def _decode_signal(item: dict) -> dict:
    item["metrics"] = json.loads(item["metrics"])
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
def dashboard(limit: int = Query(20, ge=1, le=100)) -> dict:
    latest = db.row("SELECT MAX(signal_date) AS value FROM signals")
    signal_date = latest["value"] if latest else None
    if not signal_date:
        return {"signal_date": None, "signals": [], "summary": {}}
    items = db.rows(
        """
        SELECT s.*, st.name, st.industry
        FROM signals s JOIN stocks st USING(symbol)
        WHERE s.signal_date=?
        ORDER BY s.total_score DESC LIMIT ?
        """,
        (signal_date, limit),
    )
    decoded = [_decode_signal(item) for item in items]
    return {
        "signal_date": signal_date,
        "signals": decoded,
        "summary": {
            "stock_count": len(decoded),
            "bullish_count": sum(item["metrics"]["bullish"] for item in decoded),
            "hot_count": sum(item["burst"] >= 3 for item in decoded),
            "average_score": round(
                sum(item["total_score"] for item in decoded) / max(len(decoded), 1), 2
            ),
        },
    }


@router.get("/stocks/{symbol}")
def stock_detail(symbol: str) -> dict:
    stock = db.row("SELECT * FROM stocks WHERE symbol=?", (symbol,))
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")
    prices = db.rows(
        """
        SELECT trade_date, open, high, low, close, volume
        FROM daily_prices WHERE symbol=? ORDER BY trade_date DESC LIMIT 120
        """,
        (symbol,),
    )
    prices.reverse()
    news = db.rows(
        """
        SELECT n.published_at, n.title, n.summary, n.source, n.source_type,
               n.language, n.region, n.url, n.sentiment, n.keywords,
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
