from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, urlparse

from .. import db
from ..config import settings
from ..schemas import NewsEvent
from .lake import export_parquet_snapshots
from .sentiment import RULE_MODEL_VERSION, classify_event, score_text


def _announcement_id(url: str, symbol: str, title: str, published_at: str) -> str:
    query = parse_qs(urlparse(url).query)
    announcement_id = query.get("announcementId", [""])[0]
    if announcement_id:
        return f"cninfo:{announcement_id}:{symbol}"
    digest = hashlib.sha1(
        f"{symbol}|{published_at}|{title}".encode("utf-8")
    ).hexdigest()
    return f"cninfo:{digest}"


def _normalize_time(value: object) -> str:
    text = str(value).strip()
    if len(text) == 10:
        text += " 00:00:00"
    return datetime.fromisoformat(text).replace(microsecond=0).isoformat()


def update_cninfo_announcements(history_days: int | None = None) -> dict:
    import akshare as ak

    db.init_db()
    history_days = history_days or settings.news_history_days
    now = datetime.now().replace(microsecond=0)
    latest = db.row(
        "SELECT MAX(published_at) AS value FROM news_items WHERE source='巨潮资讯'"
    )
    if latest and latest["value"]:
        start = datetime.fromisoformat(latest["value"]).date() - timedelta(days=1)
    else:
        start = date.today() - timedelta(days=history_days)
    end = date.today()
    started_at = now.isoformat()
    db.update_job(
        "cninfo_update",
        "running",
        message=f"正在获取巨潮公告 {start} 至 {end}",
        started_at=started_at,
    )

    try:
        frame = ak.stock_zh_a_disclosure_report_cninfo(
            symbol="",
            market="沪深京",
            keyword="",
            category="",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
        )
        symbols = {
            item["symbol"] for item in db.rows("SELECT symbol FROM stocks")
        }
        rows_by_id: dict[str, dict] = {}
        for item in frame.to_dict("records"):
            symbol = str(item["代码"]).zfill(6)
            if symbol not in symbols:
                continue
            title = str(item["公告标题"]).strip()
            published_at = _normalize_time(item["公告时间"])
            url = str(item["公告链接"]).replace("http://", "https://", 1)
            sentiment, keywords = score_text(title)
            event_type, event_keywords = classify_event(title)
            row_id = _announcement_id(url, symbol, title, published_at)
            event = NewsEvent(
                id=row_id,
                time=published_at,
                title=title,
                source="巨潮资讯",
                source_type="announcement",
                url=url,
                sentiment=sentiment,
                model_version=RULE_MODEL_VERSION,
                score_source="rule",
                model_raw_output={
                    "sentiment": sentiment,
                    "keywords": keywords,
                },
                event_type=event_type,
                keywords=list(dict.fromkeys([*keywords, *event_keywords])),
            )
            rows_by_id[row_id] = {
                "symbol": symbol,
                **event.storage_row(),
            }
        rows = list(rows_by_id.values())
        
        # Write directly to news_items and news_stock_links
        items = [
            {
                "id": r["id"],
                "source": r["source"],
                "source_type": r["source_type"],
                "language": r["language"],
                "region": r["region"],
                "published_at": r["published_at"],
                "title": r["title"],
                "summary": r["summary"],
                "url": r["url"],
                "sentiment": r["sentiment"],
                "model_version": r["model_version"],
                "score_source": r["score_source"],
                "model_raw_output": r["model_raw_output"],
                "event_type": r["event_type"],
                "keywords": r["keywords"],
                "raw_payload": r["raw_payload"],
            }
            for r in rows
        ]
        db.upsert_news_items(items)
        db.upsert_news_links(
            [
                {
                    "news_id": r["id"],
                    "symbol": r["symbol"],
                    "confidence": 1.0,
                    "match_type": "announcement",
                }
                for r in rows
            ]
        )
        result = {
            "fetched": len(frame),
            "matched": len(rows),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        result["parquet"] = export_parquet_snapshots(
            (
                "news/news_events.parquet",
                "news/news_stock_links.parquet",
            )
        )
        db.update_job(
            "cninfo_update",
            "completed",
            current=len(rows),
            total=len(frame),
            message=f"巨潮公告完成：全市场 {len(frame)}，命中股票池 {len(rows)}",
            details=result,
            started_at=started_at,
            finished_at=datetime.now().replace(microsecond=0).isoformat(),
        )
        return result
    except Exception as exc:
        db.update_job(
            "cninfo_update",
            "failed",
            message=str(exc),
            details={"error": repr(exc)},
            started_at=started_at,
            finished_at=datetime.now().replace(microsecond=0).isoformat(),
        )
        raise


def rescore_cninfo_announcements() -> dict[str, int]:
    items = db.rows(
        "SELECT id, title, summary FROM news_items WHERE source='巨潮资讯'"
    )
    updates = []
    for item in items:
        text = f"{item['title']}。{item['summary']}"
        sentiment, keywords = score_text(text)
        event_type, event_keywords = classify_event(text)
        updates.append(
            (
                sentiment,
                RULE_MODEL_VERSION,
                "rule",
                json.dumps(
                    {"sentiment": sentiment, "keywords": keywords},
                    ensure_ascii=False,
                ),
                event_type,
                json.dumps(
                    list(dict.fromkeys([*keywords, *event_keywords])),
                    ensure_ascii=False,
                ),
                item["id"],
            )
        )
    with db.connect() as conn:
        conn.executemany(
            """
            UPDATE news_items
            SET sentiment=?, model_version=?, score_source=?,
                model_raw_output=?, event_type=?, keywords=?
            WHERE id=?
            """,
            updates,
        )
    previous = db.row("SELECT details FROM jobs WHERE name='cninfo_update'")
    details = json.loads(previous["details"]) if previous else {}
    details["matched"] = len(updates)
    db.update_job(
        "cninfo_update",
        "completed",
        current=len(updates),
        total=int(details.get("fetched", len(updates))),
        message=f"巨潮公告完成：去重后命中股票池 {len(updates)}",
        details=details,
        finished_at=datetime.now().replace(microsecond=0).isoformat(),
    )
    return {"rescored": len(updates)}
