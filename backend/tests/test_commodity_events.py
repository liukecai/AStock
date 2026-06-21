from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.db import init_db, rows, connect


def test_commodity_event_scoring_and_api(tmp_path):
    database_path = tmp_path / "test_events.db"
    original_path = settings.database_path
    original_scheduler = settings.enable_scheduler
    original_demo = settings.demo_data
    object.__setattr__(settings, "database_path", database_path)
    object.__setattr__(settings, "enable_scheduler", False)
    object.__setattr__(settings, "demo_data", True)

    try:
        # 1. Initialize and seed DB using demo seeder (which we modified to include tungsten & oil stocks)
        init_db()
        from app.services.demo import seed_demo_data
        seed_demo_data(force=True)
        
        # 2. Run signal pipeline to populate trend scores
        from app.services.pipeline import run_signal_pipeline
        run_signal_pipeline()

        with TestClient(app) as client:
            # Check health statistics
            health = client.get("/api/health")
            assert health.status_code == 200
            health_data = health.json()
            assert "event_stats" in health_data
            assert health_data["event_stats"]["event_count"] == 0

            # 3. Test API POST /api/events/analyze
            # Case A: Tungsten supply disruption (positive price shock -> benefit to upstream)
            tungsten_req = {
                "title": "地缘冲突加剧导致我国钨矿出口受限，原料供应极度短缺，钨价格出现暴涨",
                "summary": "根据财联社消息，海外矿山出货受阻，钨矿出口面临严格限制，导致硬质合金及小金属加工端面临严重供货缺口。",
                "time": "2026-06-22T08:00:00"
            }
            res = client.post("/api/events/analyze", json=tungsten_req)
            assert res.status_code == 200
            evt_data = res.json()
            
            # Verify event attributes
            assert evt_data["title"] == tungsten_req["title"]
            assert evt_data["event_type"] == "geo_conflict" or evt_data["event_type"] == "supply_shock"
            assert evt_data["commodity_impacts"][0]["commodity"] == "tungsten"
            assert evt_data["commodity_impacts"][0]["impact_type"] == "supply_shortage"
            
            # Verify stock scores for tungsten
            stock_scores = evt_data["stock_scores"]
            assert len(stock_scores) > 0
            
            # Check specific stocks
            symbols_matched = {s["symbol"] for s in stock_scores}
            # 中钨高新 (000657), 厦门钨业 (600549), 洛阳钼业 (603993) should be matched
            assert "000657" in symbols_matched
            assert "600549" in symbols_matched
            
            # Check formula decomposition on 厦门钨业
            xm_tungsten = next(s for s in stock_scores if s["symbol"] == "600549")
            assert xm_tungsten["sector_exposure"] == 100.0
            assert xm_tungsten["direction"] == "benefit"
            
            expected_score = 0.5 * xm_tungsten["event_impact"] + 0.3 * xm_tungsten["sector_exposure"] + 0.2 * xm_tungsten["trend_strength"]
            assert abs(xm_tungsten["event_score"] - expected_score) < 0.05
            assert xm_tungsten["causal_chain"]["commodity"] == "tungsten"
            assert "Event Score = 0.5 * Event Impact" in xm_tungsten["evidence"]

            # Case B: Oil price / supply disruption (harm downstream chemical/aviation, benefit oil producer)
            oil_req = {
                "title": "中东产油重镇遭到突袭，主要原油管道完全中断，OPEC组织紧急商讨对策",
                "summary": "由于战争袭击，原油日产量减少超百万桶，市场预计供求缺口扩大，布伦特原油暴涨8%。",
                "time": "2026-06-22T09:00:00"
            }
            res_oil = client.post("/api/events/analyze", json=oil_req)
            assert res_oil.status_code == 200
            evt_oil = res_oil.json()
            assert evt_oil["commodity_impacts"][0]["commodity"] == "oil"
            assert evt_oil["commodity_impacts"][0]["impact_type"] == "supply_disruption"
            
            # Check upstream benefits (中国石油, etc.) and downstream harms (if chemical/airline exists)
            oil_scores = evt_oil["stock_scores"]
            cn_petro = next(s for s in oil_scores if s["symbol"] == "601857")
            assert cn_petro["direction"] == "benefit"
            assert cn_petro["sector_exposure"] == 100.0
            harmed_symbols = {
                score["symbol"]
                for score in oil_scores
                if score["direction"] == "harm"
            }
            assert harmed_symbols

            # 4. Test GET /api/events with filters and pagination
            events_list = client.get("/api/events?page=1&limit=5&commodity=tungsten")
            assert events_list.status_code == 200
            list_data = events_list.json()
            assert len(list_data["events"]) == 1
            assert list_data["events"][0]["title"] == tungsten_req["title"]
            
            # Filter by type
            events_by_type = client.get("/api/events?event_type=geo_conflict")
            assert events_by_type.status_code == 200

            harmed_events = client.get("/api/events?direction=harm")
            assert harmed_events.status_code == 200
            harmed_ids = {event["id"] for event in harmed_events.json()["events"]}
            assert evt_oil["id"] in harmed_ids

            invalid_filter = client.get("/api/events?direction=positive")
            assert invalid_filter.status_code == 422
            
            # 5. Test GET /api/events/{id}
            evt_id = evt_data["id"]
            detail = client.get(f"/api/events/{evt_id}")
            assert detail.status_code == 200
            assert detail.json()["id"] == evt_id
            assert len(detail.json()["stock_scores"]) > 0

            # Test 404 for event detail
            assert client.get("/api/events/evt_non_existent").status_code == 404

            repeated = client.post("/api/events/analyze", json=tungsten_req)
            assert repeated.status_code == 200
            repeated_detail = repeated.json()
            assert len(repeated_detail["commodity_impacts"]) == 1

            invalid_time = client.post(
                "/api/events/analyze",
                json={"title": "原油供应短缺", "time": "not-a-date"},
            )
            assert invalid_time.status_code == 422

            oil_slump = client.post(
                "/api/events/analyze",
                json={
                    "title": "全球原油需求疲弱，库存激增推动油价暴跌",
                    "summary": "供应过剩令石油价格继续承压。",
                    "time": "2026-06-22T11:00:00",
                },
            )
            assert oil_slump.status_code == 200
            slump_payload = oil_slump.json()
            assert slump_payload["direction"] == "harm"
            slump_scores = {
                score["symbol"]: score for score in slump_payload["stock_scores"]
            }
            assert slump_scores["601857"]["direction"] == "harm"
            assert slump_scores["601111"]["direction"] == "benefit"

            # 6. Test POST /api/events/rebuild
            # Insert a news item to database directly that matches WF6 (中船特气)
            with connect() as conn:
                conn.execute(
                    """
                    INSERT INTO news_items(
                        id, source, source_type, language, region, published_at,
                        title, summary, sentiment, keywords, raw_payload, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "news_wf6_test",
                        "测试源",
                        "legacy",
                        "zh",
                        "CN",
                        "2026-06-22T10:00:00",
                        "中船特气签订大单，六氟化钨（WF6）国内市占率居首",
                        "公告显示，公司新签订六氟化钨特气订单，保障半导体先进制程供应。",
                        0.8,
                        "[]",
                        "{}",
                        "2026-06-22T10:00:00"
                    )
                )
            
            rebuild_res = client.post("/api/events/rebuild")
            assert rebuild_res.status_code == 200
            rebuild_data = rebuild_res.json()
            assert rebuild_data["events_created"] > 0

            # The rebuild should have created an event for WF6, and scored 中船特气 (688146)
            # Let's verify 中船特气 is scored
            wf6_evts = client.get("/api/events?commodity=WF6")
            assert wf6_evts.status_code == 200
            wf6_evt_id = wf6_evts.json()["events"][0]["id"]
            
            wf6_detail = client.get(f"/api/events/{wf6_evt_id}")
            wf6_scores = wf6_detail.json()["stock_scores"]
            zctq = next(s for s in wf6_scores if s["symbol"] == "688146")
            assert zctq["sector_exposure"] == 100.0
            assert zctq["direction"] == "benefit"

            # Check health statistics again to see if it increased
            health2 = client.get("/api/health")
            assert health2.status_code == 200
            stats2 = health2.json()["event_stats"]
            assert stats2["event_count"] >= 3 # tungsten, oil, wf6
            assert stats2["by_commodity"]["tungsten"] >= 1
            assert stats2["by_commodity"]["oil"] >= 1
            assert stats2["by_commodity"]["WF6"] >= 1

    finally:
        object.__setattr__(settings, "database_path", original_path)
        object.__setattr__(settings, "enable_scheduler", original_scheduler)
        object.__setattr__(settings, "demo_data", original_demo)
