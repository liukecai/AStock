from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Protocol

from .. import db
from ..config import settings
from ..schemas import StockBar
from .lake import export_parquet_snapshots


class MarketProvider(Protocol):
    def stock_list(self) -> list[dict]: ...

    def daily_prices(
        self, symbol: str, start_date: str, end_date: str
    ) -> list[StockBar]: ...


@dataclass
class AkshareProvider:
    """Thin adapter around AKShare so provider changes stay outside strategy code."""

    adjust: str = "qfq"
    source: str = settings.akshare_source

    @staticmethod
    def _ak():
        try:
            import akshare as ak
        except ImportError as exc:
            raise RuntimeError(
                "未安装 AKShare，请执行 pip install -r requirements-market.txt"
            ) from exc
        return ak

    def stock_list(self) -> list[dict]:
        ak = self._ak()
        if self.source == "eastmoney":
            frame = ak.stock_zh_a_spot_em()
            frame = frame.sort_values("成交额", ascending=False, na_position="last")
            return [
                {
                    "symbol": str(row["代码"]).zfill(6),
                    "name": str(row["名称"]),
                    "turnover": float(row["成交额"]) if row["成交额"] == row["成交额"] else 0,
                }
                for _, row in frame.iterrows()
            ]
        frame = ak.stock_zh_a_spot()
        frame = frame.sort_values("成交额", ascending=False, na_position="last")
        return [
            {
                "symbol": str(row["代码"])[-6:],
                "name": str(row["名称"]),
                "turnover": float(row["成交额"]) if row["成交额"] == row["成交额"] else 0,
            }
            for _, row in frame.iterrows()
        ]

    def daily_prices(
        self, symbol: str, start_date: str, end_date: str
    ) -> list[StockBar]:
        ak = self._ak()
        if self.source == "eastmoney":
            frame = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust=self.adjust,
            )
        else:
            prefix = "sh" if symbol.startswith(("5", "6", "9")) else "sz"
            if symbol.startswith(("4", "8")):
                prefix = "bj"
            frame = ak.stock_zh_a_daily(
                symbol=f"{prefix}{symbol}",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust=self.adjust,
            )
        if frame.empty:
            return []
        frame = frame.rename(
            columns={
                "日期": "trade_date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "date": "trade_date",
            }
        )
        return [
            StockBar(
                code=symbol,
                date=row["trade_date"].isoformat()
                if hasattr(row["trade_date"], "isoformat")
                else str(row["trade_date"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
                amount=float(row.get("amount", 0) or 0),
            )
            for _, row in frame.iterrows()
        ]

    def daily_prices_with_retry(
        self, symbol: str, start_date: str, end_date: str, retries: int = 3
    ) -> list[StockBar]:
        import random
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                delay = getattr(settings, "akshare_delay", 0.35)
                if delay > 0:
                    time.sleep(delay * random.uniform(0.8, 1.2))
                return self.daily_prices(symbol, start_date, end_date)
            except Exception as exc:
                last_error = exc
                time.sleep(2.0 * (attempt + 1))
        raise RuntimeError(f"{symbol}: {last_error}") from last_error


def update_market_data(
    provider: MarketProvider | None = None,
    symbols: list[str] | None = None,
    history_days: int | None = None,
    universe_size: int | None = None,
    workers: int | None = None,
) -> dict[str, int | str]:
    provider = provider or AkshareProvider()
    history_days = history_days or settings.akshare_history_days
    universe_size = (
        settings.akshare_universe_size if universe_size is None else universe_size
    )
    workers = workers or settings.akshare_workers
    db.init_db()
    started_at = datetime.now().replace(microsecond=0).isoformat()
    db.update_job(
        "market_update",
        "running",
        message="正在获取 A 股股票池",
        started_at=started_at,
    )
    try:
        listed = provider.stock_list()
    except Exception as exc:
        db.update_job(
            "market_update",
            "failed",
            message=str(exc),
            finished_at=datetime.now().replace(microsecond=0).isoformat(),
        )
        raise
    allowed = set(symbols or [])
    targets = [item for item in listed if not allowed or item["symbol"] in allowed]
    if not allowed and universe_size > 0:
        targets = targets[:universe_size]
    end = date.today()
    updated = 0
    failed = 0
    errors: list[str] = []
    total = len(targets)
    db.update_job(
        "market_update",
        "running",
        total=total,
        message=f"开始更新 {total} 只股票",
        started_at=started_at,
    )

    def fetch(stock: dict) -> tuple[dict, list[StockBar], str]:
        symbol = stock["symbol"]
        latest = db.row(
            "SELECT MAX(trade_date) AS value FROM daily_prices WHERE symbol=?",
            (symbol,),
        )
        # qfq values can change after corporate actions; refresh a rolling window.
        if latest and latest["value"]:
            start = max(
                date.fromisoformat(latest["value"]) - timedelta(days=30),
                end - timedelta(days=history_days),
            )
        else:
            start = end - timedelta(days=history_days)
        fetcher = getattr(provider, "daily_prices_with_retry", provider.daily_prices)
        bars = fetcher(symbol, start.isoformat(), end.isoformat())

        # Resolve stock industry classification from database cache or CNINFO
        existing_stock = db.row("SELECT industry FROM stocks WHERE symbol=?", (symbol,))
        if existing_stock and existing_stock["industry"] and existing_stock["industry"] != "未分类":
            industry = existing_stock["industry"]
        else:
            try:
                df = provider._ak().stock_profile_cninfo(symbol=symbol)
                if not df.empty and "所属行业" in df.columns:
                    industry = str(df["所属行业"].iloc[0]).strip() or "未分类"
                else:
                    industry = "未分类"
            except Exception:
                industry = "未分类"

        return stock, bars, industry

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch, stock): stock for stock in targets}
        for future in as_completed(futures):
            stock = futures[future]
            try:
                stock, bars, industry = future.result()
                db.upsert_stock(stock["symbol"], stock["name"], industry)
                db.upsert_prices(
                    stock["symbol"], [bar.storage_row() for bar in bars]
                )
                updated += 1
            except Exception as exc:
                failed += 1
                if len(errors) < 20:
                    errors.append(f"{stock['symbol']}: {exc}")
            current = updated + failed
            if current % 10 == 0 or current == total:
                db.update_job(
                    "market_update",
                    "running",
                    current=current,
                    total=total,
                    message=f"已完成 {current}/{total}",
                    details={"updated": updated, "failed": failed, "errors": errors},
                    started_at=started_at,
                )

    result = {
        "updated": updated,
        "failed": failed,
        "total": total,
        "latest_trade_date": db.latest_trade_date() or "",
    }
    db.update_job(
        "market_update",
        "completed" if updated else "failed",
        current=updated + failed,
        total=total,
        message=f"行情更新完成：成功 {updated}，失败 {failed}",
        details={**result, "errors": errors},
        started_at=started_at,
        finished_at=datetime.now().replace(microsecond=0).isoformat(),
    )
    result["parquet"] = export_parquet_snapshots(
        ("market/daily_prices.parquet",)
    )
    return result
