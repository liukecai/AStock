from app import db
from app.config import settings
from app.services.news_mapping import map_text_to_stocks, sync_stock_aliases
from app.services.rss_news import parse_feed


RSS_SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Global Markets</title>
    <item>
      <title>BYD shares rally after record high deliveries</title>
      <description>BYD beats expectations as overseas growth accelerates.</description>
      <link>https://example.com/byd-growth</link>
      <pubDate>Thu, 18 Jun 2026 08:00:00 GMT</pubDate>
      <guid>global-1</guid>
    </item>
  </channel>
</rss>
"""


def test_rss_news_maps_english_alias_and_scores_sentiment(tmp_path):
    original_path = settings.database_path
    object.__setattr__(settings, "database_path", tmp_path / "rss.db")
    try:
        db.init_db()
        db.upsert_stock("002594", "比亚迪", "汽车")
        sync_stock_aliases()
        items, links = parse_feed(
            RSS_SAMPLE,
            {
                "name": "Global Markets",
                "path": "/global/markets",
                "language": "en",
                "region": "GLOBAL",
            },
        )
        assert len(items) == 1
        assert items[0]["sentiment"] > 0.4
        assert links == [
            {
                "news_id": items[0]["id"],
                "symbol": "002594",
                "confidence": 0.95,
                "match_type": "alias:BYD",
            }
        ]
    finally:
        object.__setattr__(settings, "database_path", original_path)


def test_stock_code_mapping(tmp_path):
    original_path = settings.database_path
    object.__setattr__(settings, "database_path", tmp_path / "mapping.db")
    try:
        db.init_db()
        db.upsert_stock("300750", "宁德时代", "电力设备")
        sync_stock_aliases()
        matches = map_text_to_stocks("宁德时代（300750）发布新产品")
        assert matches[0].symbol == "300750"
        assert matches[0].confidence == 1.0
        assert matches[0].match_type == "symbol"
    finally:
        object.__setattr__(settings, "database_path", original_path)
