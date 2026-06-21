from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class StockBar(BaseModel):
    """Canonical daily bar used between market providers and storage."""

    code: str = Field(min_length=6, max_length=6)
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float = Field(ge=0)
    amount: float = Field(default=0, ge=0)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: Any) -> str:
        return str(value).zfill(6)

    def storage_row(self) -> dict[str, float | str]:
        return {
            "trade_date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount,
        }


class NewsEvent(BaseModel):
    """Canonical news entity independent from stock associations."""

    id: str
    time: str
    title: str
    source: str
    source_type: str
    language: str = "zh"
    region: str = "CN"
    summary: str = ""
    url: str = ""
    sentiment: float = Field(default=0, ge=-1, le=1)
    event_type: str = "general"
    keywords: list[str] = Field(default_factory=list)
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("time")
    @classmethod
    def normalize_time(cls, value: str) -> str:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(
            microsecond=0
        ).isoformat()

    def storage_row(self) -> dict[str, Any]:
        import json

        return {
            "id": self.id,
            "source": self.source,
            "source_type": self.source_type,
            "language": self.language,
            "region": self.region,
            "published_at": self.time,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "sentiment": self.sentiment,
            "event_type": self.event_type,
            "keywords": json.dumps(self.keywords, ensure_ascii=False),
            "raw_payload": json.dumps(self.raw_payload, ensure_ascii=False),
        }

