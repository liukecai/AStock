from fastapi.testclient import TestClient

from app import db
from app.config import settings
from app.main import app


def test_dashboard_and_detail_api(tmp_path):
    database_path = tmp_path / "test.db"
    original_path = settings.database_path
    original_scheduler = settings.enable_scheduler
    original_demo = settings.demo_data
    original_admin_secret = settings.admin_secret
    object.__setattr__(settings, "database_path", database_path)
    object.__setattr__(settings, "enable_scheduler", False)
    object.__setattr__(settings, "demo_data", True)
    object.__setattr__(settings, "admin_secret", None)

    try:
        with TestClient(app) as client:
            health = client.get("/api/health")
            assert health.status_code == 200
            assert health.json()["stock_count"] >= 8
            assert health.json()["news_count"] > 0

            dashboard = client.get("/api/dashboard")
            assert dashboard.status_code == 200
            payload = dashboard.json()
            assert payload["summary"]["stock_count"] >= 8
            assert payload["signals"]
            assert "research_weight_pct" in payload["signals"][0]
            assert payload["signals"][0]["market_board"] in {
                "沪A", "深A", "创业板", "科创板"
            }

            expected_boards = {
                "沪A": {"600519", "601318", "600036"},
                "深A": {"002594", "000858", "000001"},
                "创业板": {"300750"},
                "科创板": {"688981"},
            }
            for board, expected_symbols in expected_boards.items():
                board_response = client.get(
                    f"/api/dashboard?board={board}&limit=100"
                )
                assert board_response.status_code == 200
                board_payload = board_response.json()
                assert expected_symbols.issubset({
                    item["symbol"] for item in board_payload["signals"]
                })
                assert board_payload["pagination"]["total"] >= len(expected_symbols)
                assert {
                    item["market_board"] for item in board_payload["signals"]
                } == {board}

            today = client.get("/api/stocks/today?top_n=3")
            assert today.status_code == 200
            assert len(today.json()["signals"]) == 3

            symbol = payload["signals"][0]["symbol"]
            signal = client.get(f"/api/signal?symbol={symbol}")
            assert signal.status_code == 200
            assert signal.json()["symbol"] == symbol
            detail = client.get(f"/api/stocks/{symbol}")
            assert detail.status_code == 200
            assert len(detail.json()["prices"]) >= 60
    finally:
        object.__setattr__(settings, "database_path", original_path)
        object.__setattr__(settings, "enable_scheduler", original_scheduler)
        object.__setattr__(settings, "demo_data", original_demo)
        object.__setattr__(settings, "admin_secret", original_admin_secret)


def test_admin_auth_required_for_mutations(tmp_path):
    database_path = tmp_path / "test-auth.db"
    original_path = settings.database_path
    original_scheduler = settings.enable_scheduler
    original_demo = settings.demo_data
    original_admin_secret = settings.admin_secret
    object.__setattr__(settings, "database_path", database_path)
    object.__setattr__(settings, "enable_scheduler", False)
    object.__setattr__(settings, "demo_data", True)
    object.__setattr__(settings, "admin_secret", "top-secret")

    try:
        with TestClient(app) as client:
            status = client.get("/api/admin/auth-status")
            assert status.status_code == 200
            assert status.json() == {"required": True}

            forbidden = client.post("/api/pipeline/run")
            assert forbidden.status_code == 403

            authorized = client.post(
                "/api/admin/authorize",
                headers={"X-Admin-Secret": "top-secret"},
            )
            assert authorized.status_code == 200

            rerun = client.post(
                "/api/pipeline/run",
                headers={"X-Admin-Secret": "top-secret"},
            )
            assert rerun.status_code == 200
            assert "signal_date" in rerun.json()
    finally:
        object.__setattr__(settings, "database_path", original_path)
        object.__setattr__(settings, "enable_scheduler", original_scheduler)
        object.__setattr__(settings, "demo_data", original_demo)
        object.__setattr__(settings, "admin_secret", original_admin_secret)


def test_legacy_events_filters_and_init_db_idempotent(tmp_path):
    database_path = tmp_path / "test-events.db"
    original_path = settings.database_path
    original_scheduler = settings.enable_scheduler
    original_demo = settings.demo_data
    original_admin_secret = settings.admin_secret
    object.__setattr__(settings, "database_path", database_path)
    object.__setattr__(settings, "enable_scheduler", False)
    object.__setattr__(settings, "demo_data", False)
    object.__setattr__(settings, "admin_secret", None)

    try:
        db.init_db()
        db.init_db()

        with db.connect() as conn:
            db._exec(
                conn,
                """
                INSERT INTO stocks(symbol, name, industry, updated_at)
                VALUES (?, ?, ?, ?)
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
                """,
                (
                    "comm_oil",
                    "Commodity",
                    "oil",
                    "oil",
                    "[]",
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
                    "evt_filter",
                    "geo_conflict",
                    "general",
                    "原油供应受扰",
                    "测试事件",
                    '[{"entity_id":"comm_oil","name":"oil"}]',
                    0.8,
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
                ("impact_filter", "evt_filter", "comm_oil", "supply_disruption", 0.8),
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
                    "evt_filter",
                    "601857",
                    88.0,
                    75.0,
                    60.0,
                    55.0,
                    50.0,
                    0.8,
                    0.0,
                    '{"direction":"harm"}',
                    0.9,
                    1,
                    "watch",
                    "2026-06-27T09:00:00",
                ),
            )

        with TestClient(app) as client:
            commodity_resp = client.get("/api/events?commodity=oil")
            assert commodity_resp.status_code == 200
            commodity_ids = [item["id"] for item in commodity_resp.json()["events"]]
            assert commodity_ids == ["evt_filter"]

            direction_resp = client.get("/api/events?direction=harm")
            assert direction_resp.status_code == 200
            direction_ids = [item["id"] for item in direction_resp.json()["events"]]
            assert direction_ids == ["evt_filter"]
    finally:
        object.__setattr__(settings, "database_path", original_path)
        object.__setattr__(settings, "enable_scheduler", original_scheduler)
        object.__setattr__(settings, "demo_data", original_demo)
        object.__setattr__(settings, "admin_secret", original_admin_secret)
