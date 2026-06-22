from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.db import connect, init_db, rows


def test_commodity_transmission_v2_flow(tmp_path):
    # Setup isolated test database path
    database_path = tmp_path / "test_transmission_v2.db"
    original_path = settings.database_path
    original_scheduler = settings.enable_scheduler
    original_demo = settings.demo_data
    original_parquet = settings.enable_parquet_snapshots
    object.__setattr__(settings, "database_path", database_path)
    object.__setattr__(settings, "enable_scheduler", False)
    object.__setattr__(settings, "demo_data", True)
    object.__setattr__(settings, "enable_parquet_snapshots", False)

    try:
        # 1. Initialize DB (creates all V2 tables and seeds profiles)
        init_db()

        # Verify that profiles table exists and has oil/lithium/copper seeded
        seeded_profiles = rows("SELECT * FROM company_commodity_profiles")
        assert len(seeded_profiles) >= 12

        commodities = {p["commodity"] for p in seeded_profiles}
        assert "oil" in commodities
        assert "lithium" in commodities
        assert "copper" in commodities

        # Check a specific seeded profile, e.g., 中国石油 (601857)
        cn_petro_profile = next(p for p in seeded_profiles if p["symbol"] == "601857" and p["commodity"] == "oil")
        assert cn_petro_profile["role"] == "upstream_resource"
        assert cn_petro_profile["channel"] == "revenue"
        assert cn_petro_profile["benefit_when_price_up"] == 1
        assert cn_petro_profile["earnings_elasticity"] == 85.0

        # Seed other demo stock data (prices and signals so trend scores can be fetched)
        from app.services.demo import seed_demo_data
        seed_demo_data(force=True)

        from app.services.pipeline import run_signal_pipeline
        run_signal_pipeline()

        with TestClient(app) as client:
            # 2. Test Oil Supply Disruption: Upstream benefit, aviation harm
            oil_disruption_req = {
                "title": "突发！地缘局势恶化导致沙特油田停产，原油日产锐减百万桶，油价瞬间暴涨",
                "summary": "红海和中东地区冲突骤然加剧，市场供应受到极强冲击，布伦特原油和美油价格暴涨突破近年高位。",
                "time": "2026-06-22T08:00:00"
            }
            res_oil = client.post("/api/events/analyze", json=oil_disruption_req)
            assert res_oil.status_code == 200
            oil_evt = res_oil.json()

            assert "v2_reaction_scores" in oil_evt
            v2_scores = oil_evt["v2_reaction_scores"]
            assert len(v2_scores) > 0

            # 中国石油 (601857) should benefit
            cn_petro_v2 = next(s for s in v2_scores if s["symbol"] == "601857")
            assert cn_petro_v2["direction"] == "benefit"
            assert cn_petro_v2["commodity"] == "oil"
            assert cn_petro_v2["reaction_score"] > 0
            assert "transmission_chain" in cn_petro_v2
            assert cn_petro_v2["transmission_chain"]["price_direction"] == "price_up"
            assert cn_petro_v2["transmission_chain"]["role"] == "upstream_resource"

            # 中国国航 (601111) should be harmed (downstream transport cost)
            air_china_v2 = next(s for s in v2_scores if s["symbol"] == "601111")
            assert air_china_v2["direction"] == "harm"
            assert air_china_v2["reaction_score"] > 0
            assert air_china_v2["transmission_chain"]["price_direction"] == "price_up"
            assert air_china_v2["transmission_chain"]["role"] == "transport"

            # 3. Test Lithium Oversupply / Price Down: Lithium miners harm, downstream benefit (寧德時代)
            lithium_down_req = {
                "title": "全球锂矿产能集中释放，市场供给出现严重过剩，碳酸锂价格暴跌至历史低位",
                "summary": "由于下游电动车需求增速放缓以及前期新建项目集中投产，盐湖提锂与矿石锂生产商库存激增，导致锂价持续大跌。",
                "time": "2026-06-22T09:00:00"
            }
            res_lithium = client.post("/api/events/analyze", json=lithium_down_req)
            assert res_lithium.status_code == 200
            lithium_evt = res_lithium.json()

            v2_scores_li = lithium_evt["v2_reaction_scores"]
            assert len(v2_scores_li) > 0

            # 天齐锂业 (002466) should be harmed by price down
            tianqi_v2 = next(s for s in v2_scores_li if s["symbol"] == "002466")
            assert tianqi_v2["direction"] == "harm"
            assert tianqi_v2["transmission_chain"]["price_direction"] == "price_down"

            # 宁德时代 (300750) should benefit from price down
            catl_v2 = next(s for s in v2_scores_li if s["symbol"] == "300750")
            assert catl_v2["direction"] == "benefit"
            assert catl_v2["transmission_chain"]["price_direction"] == "price_down"

            # 4. Test Copper Shortage / Price Up: Upstream benefit
            copper_up_req = {
                "title": "主要精炼铜冶炼厂宣布限产计划，铜供给预期吃紧，精炼铜期价连涨创高点",
                "summary": "由于智利及秘鲁铜精矿供应持续短缺，冶炼费TC大幅下降，各大铜厂计划减少产出，铜价大涨。",
                "time": "2026-06-22T10:00:00"
            }
            res_copper = client.post("/api/events/analyze", json=copper_up_req)
            assert res_copper.status_code == 200
            copper_evt = res_copper.json()

            v2_scores_cu = copper_evt["v2_reaction_scores"]
            assert len(v2_scores_cu) > 0

            # 江西铜业 (600362) should benefit
            jiangxi_v2 = next(s for s in v2_scores_cu if s["symbol"] == "600362")
            assert jiangxi_v2["direction"] == "benefit"
            assert jiangxi_v2["transmission_chain"]["price_direction"] == "price_up"

            # 5. Test V2 Read-Only APIs
            event_id = oil_evt["id"]

            # GET /api/events/{event_id}/reaction
            reaction_res = client.get(f"/api/events/{event_id}/reaction")
            assert reaction_res.status_code == 200
            reaction_data = reaction_res.json()
            assert reaction_data["id"] == event_id
            assert "reactions" in reaction_data
            assert len(reaction_data["reactions"]) > 0
            assert "transmission_chain" in reaction_data["reactions"][0]
            assert "evidence" in reaction_data["reactions"][0]

            # GET /api/stocks/{symbol}/commodity-exposure
            # Upstream Oil (601857)
            exposure_res = client.get("/api/stocks/601857/commodity-exposure")
            assert exposure_res.status_code == 200
            exposure_data = exposure_res.json()
            assert exposure_data["stock"]["symbol"] == "601857"
            assert len(exposure_data["profiles"]) == 1
            assert exposure_data["profiles"][0]["commodity"] == "oil"

            # 404 Case
            assert client.get("/api/events/evt_invalid_v2/reaction").status_code == 404
            assert client.get("/api/stocks/999999/commodity-exposure").status_code == 404
            assert client.get("/api/stocks/000657/commodity-exposure").status_code == 404

        with connect() as conn:
            conn.execute(
                """
                INSERT INTO event_earnings_impacts(
                    event_id, symbol, commodity, revenue_impact_score, margin_impact_score,
                    profit_impact_score, confidence, horizon, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (oil_evt["id"], "601857", "copper", 70.0, 35.0, 55.0, 0.7, "medium", "copper case"),
            )
            conn.execute(
                """
                INSERT INTO event_stock_reaction_scores_v2(
                    event_id, symbol, commodity, shock_score, exposure_score, earnings_score,
                    sentiment_score, trend_score, reaction_score, direction, horizon,
                    confidence, transmission_chain, evidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (oil_evt["id"], "601857", "copper", 75.0, 68.0, 58.0, 54.0, 50.0, 62.0, "benefit", "medium", 0.75, "{}", "copper reaction"),
            )
        multi_impacts = rows(
            "SELECT commodity FROM event_earnings_impacts WHERE event_id=? AND symbol=? ORDER BY commodity",
            (oil_evt["id"], "601857"),
        )
        assert [row["commodity"] for row in multi_impacts] == ["copper", "oil"]
        multi_reactions = rows(
            "SELECT commodity FROM event_stock_reaction_scores_v2 WHERE event_id=? AND symbol=? ORDER BY commodity",
            (oil_evt["id"], "601857"),
        )
        assert [row["commodity"] for row in multi_reactions] == ["copper", "oil"]

    finally:
        # Restore settings
        object.__setattr__(settings, "database_path", original_path)
        object.__setattr__(settings, "enable_scheduler", original_scheduler)
        object.__setattr__(settings, "demo_data", original_demo)
        object.__setattr__(settings, "enable_parquet_snapshots", original_parquet)
