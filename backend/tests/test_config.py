from app.config import Settings


def test_empty_rss_feeds_env_uses_defaults(monkeypatch):
    monkeypatch.setenv("RSS_FEEDS_JSON", "")

    settings = Settings()

    assert settings.rss_feeds
    assert settings.rss_feeds[0]["name"] == "财联社电报"


def test_llm_config_defaults(monkeypatch):
    monkeypatch.delenv("EVENT_LLM_ENABLED", raising=False)
    monkeypatch.delenv("EVENT_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("EVENT_LLM_API_KEY", raising=False)
    monkeypatch.delenv("EVENT_LLM_MODEL", raising=False)
    monkeypatch.delenv("EVENT_LLM_TIMEOUT_SECONDS", raising=False)

    settings = Settings()
    assert settings.event_llm_enabled is False
    assert settings.event_llm_base_url == "https://token.sensenova.cn/v1"
    assert settings.event_llm_api_key is None
    assert settings.event_llm_model == "sensenova-6.7-flash-lite"
    assert settings.event_llm_timeout_seconds == 10.0


def test_llm_config_override(monkeypatch):
    monkeypatch.setenv("EVENT_LLM_ENABLED", "True")
    monkeypatch.setenv("EVENT_LLM_BASE_URL", "https://api.openai.com/v1/")
    monkeypatch.setenv("EVENT_LLM_API_KEY", "sk-12345")
    monkeypatch.setenv("EVENT_LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("EVENT_LLM_TIMEOUT_SECONDS", "15.5")

    settings = Settings()
    assert settings.event_llm_enabled is True
    assert settings.event_llm_base_url == "https://api.openai.com/v1"
    assert settings.event_llm_api_key == "sk-12345"
    assert settings.event_llm_model == "gpt-4o"
    assert settings.event_llm_timeout_seconds == 15.5
