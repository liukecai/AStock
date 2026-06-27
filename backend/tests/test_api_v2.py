from fastapi.testclient import TestClient

from app import db
from app.config import settings
from app.main import app


def _configure_test_settings(tmp_path):
    database_path = tmp_path / "test-api-v2.db"
    original = {
        "database_path": settings.database_path,
        "enable_scheduler": settings.enable_scheduler,
        "demo_data": settings.demo_data,
        "admin_secret": settings.admin_secret,
    }
    object.__setattr__(settings, "database_path", database_path)
    object.__setattr__(settings, "enable_scheduler", False)
    object.__setattr__(settings, "demo_data", False)
    object.__setattr__(settings, "admin_secret", None)
    return original


def _restore_test_settings(original):
    for key, value in original.items():
        object.__setattr__(settings, key, value)


def _seed_v2_read_model():
    db.init_db()
    with db.connect() as conn:
        db._exec(
            conn,
            """
            INSERT INTO stocks(symbol, name, industry, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
              name=excluded.name, industry=excluded.industry, updated_at=excluded.updated_at
            """,
            ("601857", "中国石油", "石油石化", "2026-06-27T09:00:00"),
        )
        db._exec(
            conn,
            """
            INSERT INTO kg_entities(
                entity_id, entity_type, name, canonical_name, aliases_json,
                description, metadata_json, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
              name=excluded.name, canonical_name=excluded.canonical_name, aliases_json=excluded.aliases_json,
              description=excluded.description, metadata_json=excluded.metadata_json, status=excluded.status,
              updated_at=excluded.updated_at
            """,
            (
                "comm_oil",
                "Commodity",
                "oil",
                "oil",
                '["crude oil"]',
                "",
                "{}",
                "active",
                "2026-06-27T09:00:00",
                "2026-06-27T09:00:00",
            ),
        )
        db._exec(
            conn,
            """
            INSERT INTO event_instances(
                event_id, event_type, subtype, title, description,
                entities_json, intensity, direction, occurred_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "evt_v2_read",
                "supply_shock",
                "general",
                "原油供应冲击",
                "测试用 V2 事件",
                '[{"entity_id":"comm_oil","name":"oil"}]',
                0.9,
                "benefit",
                "2026-06-27T09:00:00",
                "2026-06-27T09:00:00",
            ),
        )
        db._exec(
            conn,
            """
            INSERT INTO event_impacts(impact_id, event_id, entity_id, impact_type, impact_score)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("impact_v2_read", "evt_v2_read", "comm_oil", "supply_disruption", 0.9),
        )
        db._exec(
            conn,
            """
            INSERT INTO reasoning_paths(
                path_id, event_id, stock_code, start_entity_id, end_entity_id,
                nodes_json, edges_json, path_score, path_length, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "path_v2_read",
                "evt_v2_read",
                "601857",
                "comm_oil",
                "601857",
                '[{"id":"comm_oil"},{"id":"601857"}]',
                '[{"relation_id":"rel_oil","relation_type":"upstream"}]',
                88.0,
                1,
                "2026-06-27T09:00:00",
            ),
        )
        db._exec(
            conn,
            """
            INSERT INTO stock_event_scores(
                event_id, stock_code, final_score, exposure_score, trend_score,
                sentiment_score, volume_score, event_intensity, validation_score,
                score_breakdown_json, confidence, rank, label, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "evt_v2_read",
                "601857",
                86.0,
                78.0,
                62.0,
                55.0,
                50.0,
                0.9,
                0.0,
                '{"direction":"benefit","event_impact":0.9,"sector_exposure":78.0,"trend_strength":62.0}',
                0.91,
                1,
                "watch",
                "2026-06-27T09:00:00",
            ),
        )
        db._exec(
            conn,
            """
            INSERT INTO event_validation_results(
                validation_id, event_id, stock_code, path_id, window, t0_date, end_date,
                absolute_return, benchmark_return, industry_return, excess_return_index,
                excess_return_industry, max_gain, max_drawdown, hit, status, calculated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "val_v2_read",
                "evt_v2_read",
                "601857",
                "path_v2_read",
                "T+5",
                "2026-06-27T00:00:00",
                "2026-07-04T00:00:00",
                0.08,
                0.02,
                0.03,
                0.06,
                0.05,
                0.10,
                -0.02,
                1,
                "calculated",
                "2026-07-04T15:00:00",
            ),
        )
        db._exec(
            conn,
            """
            INSERT INTO validation_summary(
                summary_id, summary_type, summary_key, window,
                sample_count, hit_rate, avg_excess_return, weight_adjustment, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "summary_v2_read",
                "relation",
                "rel_oil",
                "T+5",
                1,
                1.0,
                0.05,
                0.1,
                "2026-07-04T16:00:00",
            ),
        )


def test_v2_read_endpoints_use_v2_tables(tmp_path):
    original = _configure_test_settings(tmp_path)
    try:
        _seed_v2_read_model()

        with TestClient(app) as client:
            events_resp = client.get("/api/v2/events")
            assert events_resp.status_code == 200
            event_payload = events_resp.json()
            assert event_payload["success"] is True
            assert event_payload["data"][0]["id"] == "evt_v2_read"
            assert event_payload["data"][0]["commodity_impacts"][0]["commodity"] == "oil"

            impacts_resp = client.get("/api/v2/events/evt_v2_read/impacts")
            assert impacts_resp.status_code == 200
            assert impacts_resp.json()["data"][0]["commodity"] == "oil"

            stocks_resp = client.get("/api/v2/events/evt_v2_read/stocks")
            assert stocks_resp.status_code == 200
            stock_row = stocks_resp.json()["data"][0]
            assert stock_row["stock_code"] == "601857"
            assert stock_row["direction"] == "benefit"

            stock_events_resp = client.get("/api/v2/stocks/601857/events")
            assert stock_events_resp.status_code == 200
            assert stock_events_resp.json()["data"][0]["id"] == "evt_v2_read"

            explain_resp = client.get("/api/v2/stocks/601857/explain", params={"event_id": "evt_v2_read"})
            assert explain_resp.status_code == 200
            explain_data = explain_resp.json()["data"]
            assert explain_data["direction"] == "benefit"
            assert explain_data["nodes_json"][0]["id"] == "comm_oil"

            validation_resp = client.get("/api/v2/validation/events/evt_v2_read")
            assert validation_resp.status_code == 200
            assert validation_resp.json()["data"][0]["stock_code"] == "601857"

            validation_stock_resp = client.get("/api/v2/validation/events/evt_v2_read/stocks/601857")
            assert validation_stock_resp.status_code == 200
            assert validation_stock_resp.json()["data"]["validation_id"] == "val_v2_read"

            summary_resp = client.get("/api/v2/validation/summary", params={"summary_type": "relation", "key": "rel_oil"})
            assert summary_resp.status_code == 200
            assert summary_resp.json()["data"][0]["summary_id"] == "summary_v2_read"
    finally:
        _restore_test_settings(original)


def test_v2_input_upload_writes_v2_tables(monkeypatch, tmp_path):
    original = _configure_test_settings(tmp_path)
    try:
        db.init_db()
        with db.connect() as conn:
            db._exec(
                conn,
                """
                INSERT INTO kg_entities(
                    entity_id, entity_type, name, canonical_name, aliases_json,
                    description, metadata_json, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "comm_oil",
                    "Commodity",
                    "oil",
                    "oil",
                    '["petroleum"]',
                    "",
                    "{}",
                    "active",
                    "2026-06-27T09:00:00",
                    "2026-06-27T09:00:00",
                ),
            )

        class _FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "event_type": "policy_change",
                    "target_entity": "oil",
                    "direction": "positive",
                    "intensity": "high",
                    "confidence": 0.95,
                }

        class _FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, url, json):
                return _FakeResponse()

        monkeypatch.setattr("app.api_v2.input.httpx.AsyncClient", _FakeAsyncClient)

        with TestClient(app) as client:
            upload_resp = client.post(
                "/api/v2/input/upload",
                json={"text": "oil 市场出现重大政策变化", "source_name": "manual"},
            )
            assert upload_resp.status_code == 200
            payload = upload_resp.json()["data"]
            event_id = payload["event_id"]
            assert payload["extracted"]["direction"] == "benefit"

        event_row = db.row(
            "SELECT * FROM event_instances WHERE event_id=?",
            (event_id,),
        )
        assert event_row is not None
        assert event_row["direction"] == "benefit"

        impact_row = db.row(
            "SELECT * FROM event_impacts WHERE event_id=?",
            (event_id,),
        )
        assert impact_row is not None
        assert impact_row["entity_id"] == "comm_oil"

        legacy_event_row = db.row("SELECT * FROM events WHERE id=?", (event_id,))
        assert legacy_event_row is None
    finally:
        _restore_test_settings(original)
