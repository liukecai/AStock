from __future__ import annotations

from datetime import date
import numpy as np

from app import db
from app.config import settings
from app.services.pipeline import run_signal_pipeline


def test_industry_neutralization_logic(tmp_path):
    original_path = settings.database_path
    original_data_dir = settings.data_dir
    original_snapshots = settings.enable_parquet_snapshots

    # Use object.__setattr__ to modify the frozen settings in place cleanly
    db_file = tmp_path / "test_aquant_neutral.db"
    object.__setattr__(settings, "database_path", db_file)
    object.__setattr__(settings, "data_dir", tmp_path)
    object.__setattr__(settings, "enable_parquet_snapshots", False)

    try:
        db.init_db()

        # Seed mock stocks with different industries
        db.upsert_stock("600519", "贵州茅台", "食品饮料")
        db.upsert_stock("000858", "五粮液", "食品饮料")
        db.upsert_stock("300750", "宁德时代", "电力设备")

        # Seed mock prices (60 days) to pass trend calculation requirements
        for symbol in ["600519", "000858", "300750"]:
            prices = []
            for i in range(60):
                day = date(2026, 6, 21) - __import__("datetime").timedelta(days=60 - i)
                prices.append({
                    "trade_date": day.isoformat(),
                    "open": float(100 + i),
                    "high": float(105 + i),
                    "low": float(95 + i),
                    "close": float(102 + i),
                    "volume": float(100000),
                    "amount": float(10000000),
                })
            db.upsert_prices(symbol, prices)

        # Run the signal pipeline
        run_signal_pipeline()

        # Query signals
        signals = {row["symbol"]: row for row in db.rows("SELECT * FROM signals")}

        assert "600519" in signals
        assert "000858" in signals
        assert "300750" in signals

        # Parse metrics
        m_maotai = __import__("json").loads(signals["600519"]["metrics"])
        m_wuliangye = __import__("json").loads(signals["000858"]["metrics"])
        m_catl = __import__("json").loads(signals["300750"]["metrics"])

        # Check that neutralized scores exist
        for key in ["trend_score_neutral", "sentiment_score_neutral", "volume_score_neutral", "total_score_neutral"]:
            assert key in m_maotai
            assert key in m_wuliangye
            assert key in m_catl

        # Since 300750 is the only stock in "电力设备" industry, its neutralized score must be exactly 0
        assert abs(m_catl["trend_score_neutral"]) == 0.0
        assert abs(m_catl["sentiment_score_neutral"]) == 0.0
        assert abs(m_catl["volume_score_neutral"]) == 0.0
        assert abs(m_catl["total_score_neutral"]) == 0.0

        # For "食品饮料" industry, the sum of neutralized scores of 600519 and 000858 should be extremely close to 0 (mean-subtracted)
        assert abs(m_maotai["trend_score_neutral"] + m_wuliangye["trend_score_neutral"]) < 0.02
        assert abs(m_maotai["total_score_neutral"] + m_wuliangye["total_score_neutral"]) < 0.02

    finally:
        object.__setattr__(settings, "database_path", original_path)
        object.__setattr__(settings, "data_dir", original_data_dir)
        object.__setattr__(settings, "enable_parquet_snapshots", original_snapshots)
