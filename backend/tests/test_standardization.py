import sqlite3

from app import db
from app.config import settings
from app.schemas import NewsEvent, StockBar
from app.services.lake import export_parquet_snapshots


def test_standard_schemas_and_parquet_snapshot(tmp_path):
    original_path = settings.database_path
    original_data_dir = settings.data_dir
    object.__setattr__(settings, "database_path", tmp_path / "standard.db")
    object.__setattr__(settings, "data_dir", tmp_path)
    try:
        db.init_db()
        bar = StockBar(
            code="1",
            date="2026-06-18",
            open=10,
            high=11,
            low=9,
            close=10.5,
            volume=1000,
            amount=10500,
        )
        assert bar.code == "000001"
        db.upsert_stock(bar.code, "平安银行")
        db.upsert_prices(bar.code, [bar.storage_row()])

        event = NewsEvent(
            id="test:event",
            time="2026-06-18T10:00:00",
            title="平安银行业绩增长",
            source="测试源",
            source_type="rss",
            sentiment=0.35,
            event_type="performance",
            keywords=["增长"],
        )
        db.upsert_news_items([event.storage_row()])
        db.upsert_news_links(
            [
                {
                    "news_id": event.id,
                    "symbol": bar.code,
                    "confidence": 1,
                    "match_type": "test",
                }
            ]
        )

        result = export_parquet_snapshots()
        assert result["market/daily_prices.parquet"] == 1
        assert result["news/news_events.parquet"] == 1
        assert (tmp_path / "parquet/market/daily_prices.parquet").exists()
    finally:
        object.__setattr__(settings, "database_path", original_path)
        object.__setattr__(settings, "data_dir", original_data_dir)


def test_existing_database_gets_amount_and_event_type_columns(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE daily_prices (
              symbol TEXT, trade_date TEXT, open REAL, high REAL, low REAL,
              close REAL, volume REAL, PRIMARY KEY(symbol, trade_date)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE news_items (
              id TEXT PRIMARY KEY, source TEXT, source_type TEXT, language TEXT,
              region TEXT, published_at TEXT, title TEXT, summary TEXT, url TEXT,
              sentiment REAL, keywords TEXT, raw_payload TEXT, created_at TEXT
            )
            """
        )
    original_path = settings.database_path
    object.__setattr__(settings, "database_path", path)
    try:
        db.init_db()
        with sqlite3.connect(path) as conn:
            price_columns = {
                item[1] for item in conn.execute("PRAGMA table_info(daily_prices)")
            }
            news_columns = {
                item[1] for item in conn.execute("PRAGMA table_info(news_items)")
            }
        assert "amount" in price_columns
        assert "event_type" in news_columns
    finally:
        object.__setattr__(settings, "database_path", original_path)
