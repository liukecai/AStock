from __future__ import annotations

import argparse

from .services.announcements import (
    rescore_cninfo_announcements,
    update_cninfo_announcements,
)
from .services.demo import seed_demo_data
from .services.market import update_market_data
from .services.pipeline import run_signal_pipeline
from .services.rss_news import update_rss_news


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
            "run",
        ],
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--symbols",
        help="逗号分隔的股票代码；省略时更新全部 A 股",
    )
    parser.add_argument("--universe-size", type=int)
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
    print(run_signal_pipeline())


if __name__ == "__main__":
    main()
