from app.config import Settings


def test_empty_rss_feeds_env_uses_defaults(monkeypatch):
    monkeypatch.setenv("RSS_FEEDS_JSON", "")

    settings = Settings()

    assert settings.rss_feeds
    assert settings.rss_feeds[0]["name"] == "财联社电报"
