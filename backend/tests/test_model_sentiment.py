from unittest.mock import patch, MagicMock
import httpx
import pytest
from app.services.sentiment import SentimentInference, get_model_sentiment
from app.services.rss_news import parse_feed
from app.config import settings


def test_get_model_sentiment_success():
    # Test a successful API call to the model-service
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sentiment": 0.8543,
        "confidence": 0.95,
        "label": "Positive",
        "probabilities": {"Positive": 0.9, "Negative": 0.05, "Neutral": 0.05}
    }
    
    with patch("httpx.post", return_value=mock_response) as mock_post:
        score = get_model_sentiment("比亚迪销量大增", "zh")
        assert score == 0.8543
        mock_post.assert_called_once_with(
            f"{settings.model_service_url}/analyze",
            json={"text": "比亚迪销量大增", "lang": "zh"},
            timeout=5.0
        )


def test_get_model_sentiment_failure():
    # Test handling of non-200 responses
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    
    with patch("httpx.post", return_value=mock_response):
        score = get_model_sentiment("比亚迪销量大增", "zh")
        assert score is None


def test_get_model_sentiment_exception():
    # Test handling of network exceptions (timeout / connection error)
    with patch("httpx.post", side_effect=httpx.ConnectError("Connection refused")):
        score = get_model_sentiment("比亚迪销量大增", "zh")
        assert score is None


def test_parse_feed_uses_model_sentiment_and_falls_back(tmp_path):
    from app import db
    from app.services.news_mapping import sync_stock_aliases
    
    original_path = settings.database_path
    object.__setattr__(settings, "database_path", tmp_path / "test_sentiment.db")
    try:
        db.init_db()
        sync_stock_aliases()
        
        RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <title>Test Feed</title>
            <item>
              <title>测试新闻标题</title>
              <description>正常测试内容。这部分没有被扣减或违约。</description>
              <link>https://example.com/test</link>
              <pubDate>Thu, 18 Jun 2026 08:00:00 GMT</pubDate>
              <guid>test-1</guid>
            </item>
          </channel>
        </rss>
        """
        # 1. Test using model sentiment
        with patch(
            "app.services.rss_news.get_model_inference",
            return_value=SentimentInference(
                sentiment=0.75,
                model_version="test-finbert-v1",
                score_source="model",
                raw_output={"label": "Positive"},
            ),
        ):
            items, _ = parse_feed(
                RSS_SAMPLE.encode("utf-8"),
                {"name": "Test Feed", "path": "/test", "language": "zh", "region": "CN"}
            )
            assert len(items) == 1
            assert items[0]["sentiment"] == 0.75
            assert items[0]["model_version"] == "test-finbert-v1"
            assert items[0]["score_source"] == "model"
            assert '"label": "Positive"' in items[0]["model_raw_output"]

        # 2. Test falling back to rule-based sentiment
        with patch("app.services.rss_news.get_model_inference", return_value=None):
            items, _ = parse_feed(
                RSS_SAMPLE.encode("utf-8"),
                {"name": "Test Feed", "path": "/test", "language": "zh", "region": "CN"}
            )
            assert len(items) == 1
            # The content has no keywords from positive/negative list, so rule-based sentiment score should be 0.0
            assert items[0]["sentiment"] == 0.0
            assert items[0]["model_version"] == "rule-keywords-v1"
            assert items[0]["score_source"] == "rule"
    finally:
        object.__setattr__(settings, "database_path", original_path)
