from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from pathlib import Path


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "A-Quant Insight"
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    database_path: Path = field(
        default_factory=lambda: Path(os.getenv("DATABASE_PATH", "./data/aquant.db"))
    )
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "./data")))
    calibration_path: Path = field(
        default_factory=lambda: Path(
            os.getenv(
                "CALIBRATION_PATH",
                str(
                    Path(os.getenv("DATA_DIR", "./data"))
                    / "research_calibration.json"
                ),
            )
        )
    )
    enable_parquet_snapshots: bool = field(
        default_factory=lambda: _as_bool(
            os.getenv("ENABLE_PARQUET_SNAPSHOTS"), True
        )
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"
            ).split(",")
            if origin.strip()
        )
    )
    enable_scheduler: bool = field(
        default_factory=lambda: _as_bool(os.getenv("ENABLE_SCHEDULER"), True)
    )
    market_update_hour: int = field(
        default_factory=lambda: int(os.getenv("MARKET_UPDATE_HOUR", "16"))
    )
    market_update_minute: int = field(
        default_factory=lambda: int(os.getenv("MARKET_UPDATE_MINUTE", "5"))
    )
    signal_update_hour: int = field(
        default_factory=lambda: int(os.getenv("SIGNAL_UPDATE_HOUR", "16"))
    )
    signal_update_minute: int = field(
        default_factory=lambda: int(os.getenv("SIGNAL_UPDATE_MINUTE", "30"))
    )
    news_update_hour: int = field(
        default_factory=lambda: int(os.getenv("NEWS_UPDATE_HOUR", "20"))
    )
    news_update_minute: int = field(
        default_factory=lambda: int(os.getenv("NEWS_UPDATE_MINUTE", "30"))
    )
    news_history_days: int = field(
        default_factory=lambda: int(os.getenv("NEWS_HISTORY_DAYS", "7"))
    )
    rsshub_base_url: str = field(
        default_factory=lambda: os.getenv("RSSHUB_BASE_URL", "http://rsshub:1200").rstrip("/")
    )
    model_service_url: str = field(
        default_factory=lambda: os.getenv("MODEL_SERVICE_URL", "http://model-service:8001").rstrip("/")
    )
    rss_update_minute: int = field(
        default_factory=lambda: int(os.getenv("RSS_UPDATE_MINUTE", "15"))
    )
    rss_feeds: tuple[dict, ...] = field(
        default_factory=lambda: tuple(
            json.loads(os.getenv("RSS_FEEDS_JSON", "null"))
            or [
                {"name": "财联社电报", "path": "/cls/telegraph", "language": "zh", "region": "CN"},
                {"name": "华尔街见闻股市", "path": "/wallstreetcn/news/shares", "language": "zh", "region": "CN"},
                {"name": "华尔街见闻公司", "path": "/wallstreetcn/news/enterprise", "language": "zh", "region": "CN"},
                {"name": "36氪快讯", "path": "/36kr/newsflashes", "language": "zh", "region": "CN"},
                {"name": "Bloomberg Markets", "path": "/bloomberg/markets", "language": "en", "region": "GLOBAL"},
                {"name": "Bloomberg Business", "path": "/bloomberg/bbiz", "language": "en", "region": "GLOBAL"},
                {"name": "Al Jazeera Economy", "path": "/aljazeera/english/economy", "language": "en", "region": "GLOBAL"},
            ]
        )
    )
    market_provider: str = field(
        default_factory=lambda: os.getenv("MARKET_PROVIDER", "akshare")
    )
    demo_data: bool = field(
        default_factory=lambda: _as_bool(os.getenv("DEMO_DATA"), False)
    )
    akshare_universe_size: int = field(
        default_factory=lambda: int(os.getenv("AKSHARE_UNIVERSE_SIZE", "0"))
    )
    akshare_source: str = field(
        default_factory=lambda: os.getenv("AKSHARE_SOURCE", "sina")
    )
    akshare_delay: float = field(
        default_factory=lambda: float(os.getenv("AKSHARE_DELAY", "0.35"))
    )
    akshare_history_days: int = field(
        default_factory=lambda: int(os.getenv("AKSHARE_HISTORY_DAYS", "500"))
    )
    akshare_workers: int = field(
        default_factory=lambda: int(os.getenv("AKSHARE_WORKERS", "3"))
    )


settings = Settings()
