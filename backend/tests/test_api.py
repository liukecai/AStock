from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_dashboard_and_detail_api(tmp_path):
    database_path = tmp_path / "test.db"
    original_path = settings.database_path
    original_scheduler = settings.enable_scheduler
    original_demo = settings.demo_data
    object.__setattr__(settings, "database_path", database_path)
    object.__setattr__(settings, "enable_scheduler", False)
    object.__setattr__(settings, "demo_data", True)

    try:
        with TestClient(app) as client:
            health = client.get("/api/health")
            assert health.status_code == 200
            assert health.json()["stock_count"] == 8
            assert health.json()["news_count"] > 0

            dashboard = client.get("/api/dashboard")
            assert dashboard.status_code == 200
            payload = dashboard.json()
            assert payload["summary"]["stock_count"] == 8
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
                assert {
                    item["symbol"] for item in board_payload["signals"]
                } == expected_symbols
                assert board_payload["pagination"]["total"] == len(expected_symbols)
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
