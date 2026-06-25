from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

import feedparser
import httpx

from .. import db
from ..config import settings
from ..schemas import NewsEvent
from .lake import export_parquet_snapshots
from .news_mapping import map_text_to_stocks, sync_stock_aliases
from .sentiment import (
    RULE_MODEL_VERSION,
    classify_event,
    get_model_inference,
    score_text,
)


def _plain_text(value: str | None) -> str:
    if not value:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def _published_at(entry: dict) -> str:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if not value:
            continue
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            try:
                parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                continue
        if parsed.tzinfo:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed.replace(microsecond=0).isoformat()
    return datetime.now().replace(microsecond=0).isoformat()


def _news_id(source: str, url: str, title: str, published_at: str) -> str:
    value = url.strip() or f"{source}|{title}|{published_at}"
    return "rss:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_feed(payload: bytes, feed: dict) -> tuple[list[dict], list[dict]]:
    parsed = feedparser.parse(payload)
    items: list[dict] = []
    links: list[dict] = []
    for entry in parsed.entries:
        title = _plain_text(entry.get("title"))
        summary = _plain_text(
            entry.get("summary")
            or entry.get("description")
            or (entry.get("content") or [{}])[0].get("value")
        )
        url = str(entry.get("link", "")).strip()
        published_at = _published_at(entry)
        text = f"{title}。{summary}"
        rule_sentiment, keywords = score_text(text)
        
        # Request DL sentiment model from decoupled model-service with fallback to dictionary lookup
        inference = get_model_inference(text, lang=feed.get("language", "zh"))
        sentiment = inference.sentiment if inference is not None else rule_sentiment
        
        event_type, event_keywords = classify_event(text)
        item_id = _news_id(feed["name"], url, title, published_at)
        event = NewsEvent(
            id=item_id,
            time=published_at,
            title=title,
            summary=summary[:4000],
            source=feed["name"],
            source_type="rss",
            language=feed.get("language", "zh"),
            region=feed.get("region", "CN"),
            url=url,
            sentiment=sentiment,
            model_version=(
                inference.model_version if inference else RULE_MODEL_VERSION
            ),
            score_source=inference.score_source if inference else "rule",
            model_raw_output=(
                inference.raw_output
                if inference
                else {"sentiment": rule_sentiment, "keywords": keywords}
            ),
            event_type=event_type,
            keywords=list(dict.fromkeys([*keywords, *event_keywords])),
            raw_payload={"feed_path": feed["path"], "guid": entry.get("id", "")},
        )
        items.append(event.storage_row())
        matches = {
            match.symbol: match
            for match in map_text_to_stocks(summary, context="body")
        }
        for match in map_text_to_stocks(title, context="title"):
            matches[match.symbol] = match
        for match in matches.values():
            links.append(
                {
                    "news_id": item_id,
                    "symbol": match.symbol,
                    "confidence": match.confidence,
                    "match_type": f"{match.match_type}:{match.alias}",
                }
            )
    return items, links


def update_rss_news() -> dict:
    db.init_db()
    sync_stock_aliases()
    started_at = datetime.now().replace(microsecond=0).isoformat()
    feeds = list(settings.rss_feeds)
    db.update_job(
        "rss_news_update",
        "running",
        total=len(feeds),
        message=f"正在更新 {len(feeds)} 个 RSS 新闻源",
        started_at=started_at,
    )
    totals = {"feeds": len(feeds), "succeeded": 0, "failed": 0, "items": 0, "links": 0}
    errors: list[dict] = []

    with httpx.Client(
        timeout=45,
        headers={"User-Agent": "A-Quant-Insight/0.2 RSS reader"},
        follow_redirects=True,
    ) as client:
        for index, feed in enumerate(feeds, start=1):
            try:
                url = urljoin(settings.rsshub_base_url + "/", feed["path"].lstrip("/"))
                response = client.get(url)
                response.raise_for_status()
                items, links = parse_feed(response.content, feed)
                db.upsert_news_items(items)
                db.replace_news_links([item["id"] for item in items], links)
                totals["succeeded"] += 1
                totals["items"] += len(items)
                totals["links"] += len(links)
            except Exception as exc:
                totals["failed"] += 1
                errors.append({"source": feed["name"], "error": str(exc)[:300]})
            db.update_job(
                "rss_news_update",
                "running",
                current=index,
                total=len(feeds),
                message=f"已处理 {index}/{len(feeds)} 个 RSS 源",
                details={**totals, "errors": errors},
                started_at=started_at,
            )

    status = "completed" if totals["succeeded"] else "failed"
    details = {**totals, "errors": errors}
    details["parquet"] = export_parquet_snapshots(
        (
            "news/news_events.parquet",
            "news/news_stock_links.parquet",
        )
    )
    db.update_job(
        "rss_news_update",
        status,
        current=len(feeds),
        total=len(feeds),
        message=(
            f"RSS 新闻完成：{totals['succeeded']} 成功，{totals['failed']} 失败，"
            f"{totals['items']} 篇，{totals['links']} 个股票映射"
        ),
        details=details,
        started_at=started_at,
        finished_at=datetime.now().replace(microsecond=0).isoformat(),
    )
    return details


def rescore_rss_news() -> dict:
    """Re-score already-stored RSS news items that fell back to rule-based scoring when model-service was offline."""
    db.init_db()
    items = db.rows(
        "SELECT id, title, summary, language FROM news_items WHERE score_source = 'rule' AND source != '巨潮资讯'"
    )
    if not items:
        return {"status": "ok", "rescored": 0, "message": "No RSS news items with rule-based fallback score found."}
        
    updates = []
    success_count = 0
    for item in items:
        text = f"{item['title']}。{item['summary']}"
        lang = item.get("language", "zh")
        inference = get_model_inference(text, lang=lang)
        if inference is not None:
            updates.append((
                inference.sentiment,
                inference.model_version,
                inference.score_source,
                json.dumps(inference.raw_output, ensure_ascii=False),
                item["id"]
            ))
            success_count += 1
            
    if updates:
        with db.connect() as conn:
            db._execmany(
                conn,
                """
                UPDATE news_items
                SET sentiment=?, model_version=?, score_source=?, model_raw_output=?
                WHERE id=?
                """,
                updates,
            )
            
        export_parquet_snapshots(
            (
                "news/news_events.parquet",
                "news/news_stock_links.parquet",
            )
        )
        
    return {
        "status": "ok",
        "total_queued": len(items),
        "rescored": success_count,
        "message": f"Successfully rescored {success_count}/{len(items)} RSS news items using model-service."
    }

