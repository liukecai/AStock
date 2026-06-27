from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import settings
from .services.backtest import BacktestConfig, run_backtest_from_parquet
from .services.calibration import calibrate_from_backtest, save_calibration
from .services.announcements import (
    rescore_cninfo_announcements,
    update_cninfo_announcements,
)
from .services.demo import seed_demo_data
from .services.market import update_market_data
from .services.pipeline import run_signal_pipeline
from .services.rss_news import rescore_rss_news, update_rss_news


def main() -> None:
    parser = argparse.ArgumentParser(prog="aquant")
    parser.add_argument(
        "command",
        choices=[
            "seed",
            "update-market",
            "update-news",
            "update-rss",
            "update-all-news",
            "rescore-news",
            "rescore-rss",
            "run",
            "backtest",
            "calibrate",
            "extract-report",
        ],
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--symbols",
        help="逗号分隔的股票代码；省略时更新全部 A 股",
    )
    parser.add_argument("--universe-size", type=int)
    parser.add_argument("--holding-period", type=int, default=5)
    parser.add_argument("--transaction-cost-bps", type=float, default=0.0)
    parser.add_argument("--output-dir")
    parser.add_argument("--file", help="File path for extraction")
    parser.add_argument("--extract-type", choices=["profile", "event"], default="profile")
    args = parser.parse_args()

    if args.command == "seed":
        seed_demo_data(force=args.force)
    elif args.command == "update-market":
        symbols = args.symbols.split(",") if args.symbols else None
        print(update_market_data(symbols=symbols, universe_size=args.universe_size))
    elif args.command == "update-news":
        print(update_cninfo_announcements())
    elif args.command == "update-rss":
        print(update_rss_news())
    elif args.command == "update-all-news":
        print(update_cninfo_announcements())
        print(update_rss_news())
    elif args.command == "rescore-news":
        print(rescore_cninfo_announcements())
    elif args.command == "rescore-rss":
        print(rescore_rss_news())
    elif args.command in {"backtest", "calibrate"}:
        parquet_root = Path(settings.data_dir) / "parquet"
        output_dir = Path(args.output_dir or Path(settings.data_dir) / "backtest")
        result = run_backtest_from_parquet(
            parquet_root / "factors/signals.parquet",
            parquet_root / "market/daily_prices.parquet",
            output_dir,
            BacktestConfig(
                holding_period=args.holding_period,
                transaction_cost_bps=args.transaction_cost_bps,
            ),
        )
        if args.command == "calibrate":
            import pandas as pd

            calibration = calibrate_from_backtest(
                result,
                pd.read_parquet(output_dir / "trades.parquet"),
            )
            save_calibration(calibration, settings.calibration_path)
            result["calibration"] = calibration
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    elif args.command == "run":
        print(run_signal_pipeline())
    elif args.command == "extract-report":
        if not args.file:
            print("Error: --file is required for extract-report")
            return
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
        
        from .services.llm_extractor import LLMExtractorService
        from . import db
        extractor = LLMExtractorService()
        with db.session_scope() as session:
            if args.extract_type == "profile":
                res = extractor.extract_company_profile(text, source_evidence_id="cli_test", db=session)
            else:
                res = extractor.extract_event(text, source_evidence_id="cli_test", db=session)
            print(res.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
