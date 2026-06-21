from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta

import numpy as np

from .. import db
from .sentiment import score_text


STOCKS = [
    ("600519", "贵州茅台", "食品饮料", 1520.0, 0.0010),
    ("300750", "宁德时代", "电力设备", 240.0, 0.0017),
    ("002594", "比亚迪", "汽车", 320.0, 0.0013),
    ("601318", "中国平安", "非银金融", 52.0, 0.0004),
    ("000858", "五粮液", "食品饮料", 132.0, 0.0007),
    ("688981", "中芯国际", "电子", 88.0, 0.0021),
    ("600036", "招商银行", "银行", 46.0, 0.0006),
    ("000001", "平安银行", "银行", 12.0, -0.0001),
    ("000657", "中钨高新", "有色金属", 10.0, 0.0005),
    ("600549", "厦门钨业", "有色金属", 18.0, 0.0008),
    ("603993", "洛阳钼业", "有色金属", 8.0, 0.0012),
    ("688146", "中船特气", "电子化学品", 35.0, 0.0006),
    ("601857", "中国石油", "石油石化", 8.0, 0.0004),
    ("600028", "中国石化", "石油石化", 6.5, 0.0003),
    ("601808", "中海油服", "采掘服务", 15.0, 0.0005),
    ("600547", "山东黄金", "贵金属", 28.0, 0.0011),
    ("600489", "中金黄金", "贵金属", 12.0, 0.0009),
    ("600988", "赤峰黄金", "贵金属", 18.0, 0.0013),
    ("002466", "天齐锂业", "能源金属", 40.0, -0.0005),
    ("002460", "赣锋锂业", "能源金属", 38.0, -0.0004),
    ("000792", "盐湖股份", "能源金属", 17.0, -0.0001),
    ("600362", "江西铜业", "有色金属", 22.0, 0.0008),
    ("601899", "紫金矿业", "有色金属", 16.0, 0.0015),
    ("000878", "云南铜业", "有色金属", 13.0, 0.0006),
    ("601111", "中国国航", "航空机场", 8.0, 0.0002),
]
NEWS_TEMPLATES = [
    "{}发布经营数据，核心业务保持增长",
    "{}获得机构增持，市场关注度提升",
    "{}公告新项目签约，订单稳步推进",
    "{}提示行业波动风险，短期业绩承压",
    "{}推出股份回购计划",
]


def seed_demo_data(force: bool = False) -> None:
    db.init_db()
    existing = db.row("SELECT COUNT(*) AS count FROM daily_prices")
    if existing and existing["count"] and not force:
        return

    end = date.today()
    days = [
        end - timedelta(days=offset)
        for offset in range(180, -1, -1)
        if (end - timedelta(days=offset)).weekday() < 5
    ]
    for symbol, name, industry, base, drift in STOCKS:
        db.upsert_stock(symbol, name, industry)
        seed = int(hashlib.sha256(symbol.encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        returns = rng.normal(drift, 0.014, len(days))
        closes = base * np.cumprod(1 + returns)
        volumes = rng.lognormal(15.5, 0.35, len(days))
        prices = []
        for index, trade_day in enumerate(days):
            close = closes[index]
            open_price = close * (1 + rng.normal(0, 0.004))
            prices.append(
                {
                    "trade_date": trade_day.isoformat(),
                    "open": round(float(open_price), 3),
                    "high": round(float(max(open_price, close) * (1 + rng.uniform(0, 0.012))), 3),
                    "low": round(float(min(open_price, close) * (1 - rng.uniform(0, 0.012))), 3),
                    "close": round(float(close), 3),
                    "volume": round(float(volumes[index]), 0),
                    "amount": round(float(volumes[index] * close), 2),
                }
            )
        db.upsert_prices(symbol, prices)

        news_items = []
        news_links = []
        for index in range(8):
            template = NEWS_TEMPLATES[(index + seed) % len(NEWS_TEMPLATES)]
            title = template.format(name)
            sentiment, keywords = score_text(title)
            published = datetime.now() - timedelta(days=index % 6, hours=index)
            news_id = hashlib.sha1(f"{symbol}-{title}-{index}".encode()).hexdigest()
            news_items.append(
                {
                    "id": news_id,
                    "source": "演示数据",
                    "source_type": "legacy",
                    "language": "zh",
                    "region": "CN",
                    "published_at": published.replace(microsecond=0).isoformat(),
                    "title": title,
                    "summary": "",
                    "url": "",
                    "sentiment": sentiment,
                    "event_type": "general",
                    "keywords": __import__("json").dumps(keywords, ensure_ascii=False),
                    "raw_payload": "{}",
                }
            )
            news_links.append(
                {
                    "news_id": news_id,
                    "symbol": symbol,
                    "confidence": 1.0,
                    "match_type": "legacy",
                }
            )
        db.upsert_news_items(news_items)
        db.upsert_news_links(news_links)
