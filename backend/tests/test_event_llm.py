from __future__ import annotations

import json
import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.db import init_db
from app.services.event_engine import analyze_event_text

def set_setting(name: str, value: any) -> None:
    object.__setattr__(settings, name, value)

@pytest.fixture
def setup_test_db(tmp_path):
    original_path = settings.database_path
    original_scheduler = settings.enable_scheduler
    original_demo = settings.demo_data
    original_llm_enabled = settings.event_llm_enabled
    original_llm_api_key = settings.event_llm_api_key
    original_llm_base_url = settings.event_llm_base_url
    original_llm_model = settings.event_llm_model
    original_llm_timeout = settings.event_llm_timeout_seconds

    test_db_path = tmp_path / "test_llm_events.db"
    set_setting("database_path", test_db_path)
    set_setting("enable_scheduler", False)
    set_setting("demo_data", True)

    init_db()
    from app.services.demo import seed_demo_data
    seed_demo_data(force=True)
    
    from app.services.pipeline import run_signal_pipeline
    run_signal_pipeline()

    yield

    set_setting("database_path", original_path)
    set_setting("enable_scheduler", original_scheduler)
    set_setting("demo_data", original_demo)
    set_setting("event_llm_enabled", original_llm_enabled)
    set_setting("event_llm_api_key", original_llm_api_key)
    set_setting("event_llm_base_url", original_llm_base_url)
    set_setting("event_llm_model", original_llm_model)
    set_setting("event_llm_timeout_seconds", original_llm_timeout)


def test_llm_success_path(setup_test_db, monkeypatch):
    # Configure LLM settings
    set_setting("event_llm_enabled", True)
    set_setting("event_llm_api_key", "test-key-sensenova")
    set_setting("event_llm_base_url", "https://token.sensenova.cn/v1")
    set_setting("event_llm_model", "sensenova-6.7-flash-lite")

    llm_response_content = {
        "is_relevant": True,
        "commodity": "tungsten",
        "event_type": "geo_conflict",
        "subtype": "geopolitics",
        "impact_type": "supply_shortage",
        "direction": "benefit",
        "intensity": 0.9,
        "confidence": 0.95,
        "rationale": "LLM analysis: tungsten mine production affected by geopolitical risk."
    }

    mock_resp = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps(llm_response_content)
                }
            }
        ]
    }

    original_post = httpx.Client.post
    def mock_client_post(self, url, *args, **kwargs):
        if "sensenova.cn" in str(url) or "chat/completions" in str(url):
            resp = httpx.Response(200, json=mock_resp)
            resp.request = httpx.Request("POST", url)
            return resp
        return original_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "post", mock_client_post)

    title = "地缘紧张加剧导致国际矿山开采受限"
    summary = "国际形势严峻导致生产受限。"
    res = analyze_event_text(title, summary, "2026-06-22T10:00:00")

    assert res is not None
    assert res["extraction_source"] == "llm"
    assert "LLM 优先抽取" in res["stock_scores"][0]["evidence"]
    assert res["commodity_impacts"][0]["commodity"] == "tungsten"
    assert res["commodity_impacts"][0]["impact_type"] == "supply_shortage"
    assert res["intensity"] == 0.9
    assert res["confidence"] == 0.95
    assert json.loads(res["extraction_raw_output"])["rationale"] == llm_response_content["rationale"]


def test_llm_irrelevant_event_422(setup_test_db, monkeypatch):
    set_setting("event_llm_enabled", True)
    set_setting("event_llm_api_key", "test-key")

    mock_resp = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "is_relevant": False,
                        "commodity": None,
                        "event_type": None,
                        "subtype": "",
                        "impact_type": None,
                        "direction": None,
                        "intensity": 0.0,
                        "confidence": 0.0,
                        "rationale": "Irrelevant business update"
                    })
                }
            }
        ]
    }

    original_post = httpx.Client.post
    def mock_client_post(self, url, *args, **kwargs):
        if "sensenova.cn" in str(url) or "chat/completions" in str(url):
            resp = httpx.Response(200, json=mock_resp)
            resp.request = httpx.Request("POST", url)
            return resp
        return original_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "post", mock_client_post)

    with TestClient(app) as client:
        req = {
            "title": "公司发布日常财务报告",
            "summary": "报告显示利润符合预期。",
            "time": "2026-06-22T10:00:00"
        }
        res = client.post("/api/events/analyze", json=req)
        assert res.status_code == 422
        assert "未能从文本中识别出商品因果事件链" in res.json()["detail"]


def test_llm_invalid_json_fallback(setup_test_db, monkeypatch):
    set_setting("event_llm_enabled", True)
    set_setting("event_llm_api_key", "test-key")

    original_post = httpx.Client.post
    def mock_client_post(self, url, *args, **kwargs):
        if "sensenova.cn" in str(url) or "chat/completions" in str(url):
            resp = httpx.Response(200, json={"choices": [{"message": {"content": "{invalid_json_indeed"}}]})
            resp.request = httpx.Request("POST", url)
            return resp
        return original_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "post", mock_client_post)

    # Use a headline that will definitely be parsed by rules for 'oil'
    title = "中东爆发军事袭击，沙特石油管道完全中断"
    summary = "由于武装袭击，原油日产量减少，布伦特原油暴涨。"
    res = analyze_event_text(title, summary, "2026-06-22T10:00:00")

    assert res is not None
    assert res["extraction_source"] == "rule"
    assert "规则回退" in res["stock_scores"][0]["evidence"]
    assert res["commodity_impacts"][0]["commodity"] == "oil"


def test_llm_timeout_fallback(setup_test_db, monkeypatch):
    set_setting("event_llm_enabled", True)
    set_setting("event_llm_api_key", "test-key")

    original_post = httpx.Client.post
    def mock_client_post(self, url, *args, **kwargs):
        if "sensenova.cn" in str(url) or "chat/completions" in str(url):
            raise httpx.TimeoutException("Connection timed out")
        return original_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "post", mock_client_post)

    title = "中东爆发军事袭击，沙特石油管道完全中断"
    summary = "由于武装袭击，原油日产量减少，布伦特原油暴涨。"
    res = analyze_event_text(title, summary, "2026-06-22T10:00:00")

    assert res is not None
    assert res["extraction_source"] == "rule"
    assert "规则回退" in res["stock_scores"][0]["evidence"]
    assert res["commodity_impacts"][0]["commodity"] == "oil"


def test_llm_no_key_fallback(setup_test_db):
    set_setting("event_llm_enabled", True)
    set_setting("event_llm_api_key", None)  # Key is not configured

    title = "中东爆发军事袭击，沙特石油管道完全中断"
    summary = "由于武装袭击，原油日产量减少，布伦特原油暴涨。"
    res = analyze_event_text(title, summary, "2026-06-22T10:00:00")

    assert res is not None
    assert res["extraction_source"] == "rule"
    assert "规则回退" in res["stock_scores"][0]["evidence"]
    assert res["commodity_impacts"][0]["commodity"] == "oil"
