from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from statistics import pstdev


POSITIVE_WORDS = {
    "增长": 0.35,
    "增持": 0.5,
    "中标": 0.45,
    "突破": 0.35,
    "回购": 0.5,
    "预增": 0.65,
    "创新高": 0.5,
    "利好": 0.5,
    "扭亏": 0.55,
    "签约": 0.3,
    "上调": 0.4,
    "获批": 0.45,
    "分红": 0.35,
    "权益分派": 0.35,
    "评级提升": 0.4,
}
NEGATIVE_WORDS = {
    "减持": -0.5,
    "亏损": -0.5,
    "立案": -0.8,
    "处罚": -0.7,
    "下滑": -0.4,
    "风险": -0.35,
    "终止": -0.45,
    "暴跌": -0.7,
    "退市": -1.0,
    "问询": -0.3,
    "行政处罚": -0.8,
    "警示函": -0.55,
    "诉讼": -0.45,
    "冻结": -0.55,
    "违规": -0.6,
}
POSITIVE_ENGLISH = {
    "growth": 0.35,
    "surge": 0.45,
    "rally": 0.4,
    "upgrade": 0.4,
    "record high": 0.5,
    "profit": 0.3,
    "beats expectations": 0.55,
    "approval": 0.35,
    "buyback": 0.5,
}
NEGATIVE_ENGLISH = {
    "loss": -0.45,
    "plunge": -0.65,
    "downgrade": -0.45,
    "investigation": -0.55,
    "sanction": -0.55,
    "default": -0.8,
    "recall": -0.4,
    "fraud": -0.8,
    "layoff": -0.4,
    "misses expectations": -0.5,
}

EVENT_KEYWORDS = {
    "risk": {
        "风险",
        "处罚",
        "立案",
        "问询",
        "警示函",
        "诉讼",
        "冻结",
        "违规",
        "亏损",
        "退市",
        "违约",
        "investigation",
        "sanction",
        "fraud",
        "default",
        "recall",
    },
    "policy": {
        "政策",
        "国务院",
        "证监会",
        "央行",
        "发改委",
        "财政部",
        "监管",
        "条例",
        "办法",
        "指导意见",
        "补贴",
        "降准",
        "降息",
        "关税",
        "regulation",
        "central bank",
        "interest rate",
        "tariff",
        "subsidy",
    },
    "performance": {
        "业绩",
        "年报",
        "半年报",
        "季报",
        "营收",
        "净利润",
        "预增",
        "扭亏",
        "分红",
        "权益分派",
        "订单",
        "中标",
        "earnings",
        "revenue",
        "profit",
        "growth",
        "record high",
        "deliveries",
        "guidance",
        "dividend",
        "order",
    },
}

EVENT_PRIORITY = ("risk", "policy", "performance")


def classify_event(text: str) -> tuple[str, list[str]]:
    lowered = text.casefold()
    for event_type in EVENT_PRIORITY:
        hits = [
            word
            for word in EVENT_KEYWORDS[event_type]
            if word.casefold() in lowered
        ]
        if hits:
            return event_type, sorted(hits)
    return "general", []


def score_text(text: str) -> tuple[float, list[str]]:
    hits: list[tuple[str, float]] = []
    for word, weight in {**POSITIVE_WORDS, **NEGATIVE_WORDS}.items():
        if word not in text:
            continue
        word_index = text.index(word)
        clause_start = max(
            [text.rfind(mark, 0, word_index) for mark in ("，", "。", "；", "：")]
            + [-1]
        )
        clause_prefix = text[clause_start + 1 : word_index]
        if weight < 0 and any(
            negation in clause_prefix for negation in ("未被", "未受", "没有", "无")
        ):
            continue
        if word == "回购" and any(
            phrase in text for phrase in ("回购注销", "注销部分限制性股票")
        ):
            continue
        if word in text:
            hits.append((word, weight))
    lowered = text.casefold()
    for word, weight in {**POSITIVE_ENGLISH, **NEGATIVE_ENGLISH}.items():
        if word in lowered:
            hits.append((word, weight))
    if not hits:
        return 0.0, []
    score = sum(weight for _, weight in hits) / max(len(hits), 1)
    return round(max(-1.0, min(1.0, score)), 3), [word for word, _ in hits]


def aggregate_news(
    news: list[dict], reference_date: date | None = None
) -> dict[str, float | int | list[str]]:
    if not news:
        return {
            "sentiment": 0.0,
            "burst": 0.0,
            "mentions_today": 0,
            "keywords": [],
            "event_counts": {},
        }

    today = reference_date or datetime.now().date()
    today_items = [
        item for item in news if datetime.fromisoformat(item["published_at"]).date() == today
    ]
    previous_counts = []
    for days_ago in range(1, 6):
        target = today - timedelta(days=days_ago)
        previous_counts.append(
            sum(
                datetime.fromisoformat(item["published_at"]).date() == target
                for item in news
            )
        )
    baseline = sum(previous_counts) / 5
    mentions = len(today_items)
    deviation = pstdev(previous_counts)
    burst = (mentions - baseline) / max(deviation, 1.0)
    weighted = today_items or news[:10]
    sentiment = sum(float(item["sentiment"]) for item in weighted) / len(weighted)
    keywords = Counter(
        keyword for item in weighted for keyword in item.get("keywords", [])
    ).most_common(5)
    event_counts = Counter(
        item.get("event_type", "general") for item in weighted
    )
    return {
        "sentiment": round(sentiment, 3),
        "burst": round(burst, 2),
        "mentions_today": mentions,
        "keywords": [word for word, _ in keywords],
        "event_counts": dict(event_counts),
    }
