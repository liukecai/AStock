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

            dashboard = client.get("/api/dashboard")
            assert dashboard.status_code == 200
            payload = dashboard.json()
            assert payload["summary"]["stock_count"] == 8
            assert payload["signals"]

            symbol = payload["signals"][0]["symbol"]
            detail = client.get(f"/api/stocks/{symbol}")
            assert detail.status_code == 200
            assert len(detail.json()["prices"]) >= 60
    finally:
        object.__setattr__(settings, "database_path", original_path)
        object.__setattr__(settings, "enable_scheduler", original_scheduler)
        object.__setattr__(settings, "demo_data", original_demo)
