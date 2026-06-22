from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from .. import db
from .event_llm import extract_event_llm

COMMODITY_KB = {
    "tungsten": {
        "name": "钨",
        "keywords": ["钨", "tungsten", "中钨", "厦钨", "硬质合金", "钨矿"],
        "exact_stocks": {
            "000657": {"relationship": "upstream", "name": "中钨高新"},
            "600549": {"relationship": "upstream", "name": "厦门钨业"},
            "603993": {"relationship": "upstream", "name": "洛阳钼业"}
        },
        "sector_keywords": ["有色金属", "小金属", "硬质合金", "材料", "金属"],
        "default_sector": "有色金属",
        "upstream_sectors": ["有色金属", "小金属", "硬质合金"],
        "downstream_sectors": []
    },
    "WF6": {
        "name": "六氟化钨",
        "keywords": ["六氟化钨", "WF6", "中船特气", "特气", "电子气体"],
        "exact_stocks": {
            "688146": {"relationship": "upstream", "name": "中船特气"}
        },
        "sector_keywords": ["电子化学品", "特种气体", "化学制品", "半导体材料"],
        "default_sector": "电子化学品",
        "upstream_sectors": ["电子化学品", "特种气体", "化学制品"],
        "downstream_sectors": ["半导体", "电子", "半导体材料"]
    },
    "oil": {
        "name": "原油/石油",
        "keywords": ["原油", "石油", "oil", "opec", "欧佩克", "油价", "布伦特", "汽油", "柴油"],
        "exact_stocks": {
            "601857": {"relationship": "upstream", "name": "中国石油"},
            "600028": {"relationship": "upstream", "name": "中国石化"},
            "601808": {"relationship": "upstream", "name": "中海油服"}
        },
        "sector_keywords": ["石油石化", "采掘服务", "油气开采", "化工", "航空机场"],
        "default_sector": "石油石化",
        "upstream_sectors": ["石油石化", "采掘服务", "油气开采"],
        "downstream_sectors": ["化工", "航空机场", "航空", "机场"]
    },
    "copper": {
        "name": "铜",
        "keywords": ["铜", "copper", "铜价", "精炼铜", "电解铜"],
        "exact_stocks": {
            "600362": {"relationship": "upstream", "name": "江西铜业"},
            "601899": {"relationship": "upstream", "name": "紫金矿业"},
            "000878": {"relationship": "upstream", "name": "云南铜业"}
        },
        "sector_keywords": ["有色金属", "铜", "铜业", "电力设备"],
        "default_sector": "有色金属",
        "upstream_sectors": ["有色金属", "铜", "铜业"],
        "downstream_sectors": ["电力设备"]
    },
    "gold": {
        "name": "黄金",
        "keywords": ["黄金", "gold", "金价", "贵金属", "金矿"],
        "exact_stocks": {
            "600547": {"relationship": "upstream", "name": "山东黄金"},
            "600489": {"relationship": "upstream", "name": "中金黄金"},
            "600988": {"relationship": "upstream", "name": "赤峰黄金"}
        },
        "sector_keywords": ["贵金属", "黄金", "有色金属"],
        "default_sector": "贵金属",
        "upstream_sectors": ["贵金属", "黄金", "有色金属"],
        "downstream_sectors": []
    },
    "lithium": {
        "name": "锂",
        "keywords": ["锂", "lithium", "碳酸锂", "氢氧化锂", "盐湖提锂", "电池级碳酸锂"],
        "exact_stocks": {
            "002466": {"relationship": "upstream", "name": "天齐锂业"},
            "002460": {"relationship": "upstream", "name": "赣锋锂业"},
            "000792": {"relationship": "upstream", "name": "盐湖股份"}
        },
        "sector_keywords": ["能源金属", "电池材料", "锂电池", "汽车", "有色金属"],
        "default_sector": "能源金属",
        "upstream_sectors": ["能源金属", "电池材料"],
        "downstream_sectors": ["锂电池", "汽车", "电力设备"]
    }
}

EVENT_TYPE_KEYWORDS = {
    "geo_conflict": ["地缘", "战争", "军事", "红海", "袭击", "制裁", "冲突", "俄乌", "巴以", "紧张局势"],
    "supply_shock": [
        "供应中断", "减产", "停产", "断供", "供应受限", "紧张", "短缺",
        "吃紧", "供给偏紧", "库存大跌", "库存减少", "供应过剩",
        "供给过剩", "库存激增", "增产", "扩产", "恢复产量", "产量恢复",
        "提高产量",
        "需求疲弱", "需求下降", "需求萎缩", "消费低迷", "暴涨", "大涨",
        "上涨", "暴跌", "大跌", "下跌",
    ],
    "policy_change": ["政策", "收储", "出口管制", "加税", "关税", "环保督察", "规划", "退税", "补贴", "准入"],
    "disruption": ["罢工", "地震", "停电", "事故", "洪涝", "飓风", "火灾", "暴雨", "恶劣天气"]
}

def identify_commodity(text: str) -> str | None:
    lowered = text.lower()
    # Check WF6 first to avoid conflict with tungsten (钨) in "六氟化钨"
    if any(kw in lowered for kw in ["六氟化钨", "wf6", "中船特气"]):
        return "WF6"
    for comm, cfg in COMMODITY_KB.items():
        if comm == "WF6":
            continue
        if any(kw in lowered for kw in cfg["keywords"]):
            return comm
    return None

def identify_event_type(text: str) -> tuple[str, str] | None:
    lowered = text.lower()
    best_type = ""
    max_matches = 0
    for etype, kws in EVENT_TYPE_KEYWORDS.items():
        matches = sum(1 for kw in kws if kw in lowered)
        if matches > max_matches:
            max_matches = matches
            best_type = etype
    if not best_type:
        return None

    # Determine subtype
    subtype = "general"
    if best_type == "geo_conflict":
        subtype = "geopolitics"
    elif best_type == "supply_shock":
        if "减产" in lowered or "停产" in lowered:
            subtype = "production_cut"
        elif "短缺" in lowered or "偏紧" in lowered:
            subtype = "shortage"
    elif best_type == "policy_change":
        if "出口" in lowered or "管制" in lowered:
            subtype = "export_control"
        elif "收储" in lowered:
            subtype = "national_reserve"
    elif best_type == "disruption":
        if "罢工" in lowered:
            subtype = "strike"
        elif "地震" in lowered or "天气" in lowered or "洪涝" in lowered:
            subtype = "natural_disaster"
    return best_type, subtype

def identify_commodity_shock(text: str) -> str:
    lowered = text.lower()
    if any(
        kw in lowered
        for kw in ["恢复产量", "产量恢复", "增产", "扩产", "提高产量"]
    ):
        return "supply_increase"
    if any(kw in lowered for kw in ["需求疲弱", "需求下降", "需求萎缩", "消费低迷"]):
        return "demand_weakness"
    if any(kw in lowered for kw in ["供应过剩", "供给过剩", "库存激增", "产能过剩"]):
        return "oversupply"
    if any(kw in lowered for kw in ["支持", "补贴", "收储", "利好政策", "鼓励", "规划"]):
        return "policy_support"
    if any(kw in lowered for kw in ["中断", "停产", "减产", "停工", "关闭", "罢工", "爆炸", "事故"]):
        return "supply_disruption"
    if any(kw in lowered for kw in ["短缺", "紧张", "不足", "缺口", "吃紧"]):
        return "supply_shortage"
    return "supply_shortage"


def commodity_impact_direction(text: str, impact_type: str) -> str:
    lowered = text.lower()
    price_decline = ["暴跌", "大跌", "下跌", "跳水", "价格走低", "价格承压"]
    if impact_type in {"demand_weakness", "oversupply", "supply_increase"}:
        return "harm"
    if any(keyword in lowered for keyword in price_decline):
        return "harm"
    return "benefit"


def extract_intensity_confidence(title: str, summary: str) -> tuple[float, float]:
    text = (title + " " + summary).lower()
    intensity = 0.6
    confidence = 0.85
    
    high_intensity = ["暴涨", "大涨", "急剧", "爆发", "袭击", "中断", "完全", "重创", "历史新高", "大跌", "暴跌"]
    med_intensity = ["上涨", "下跌", "受限", "减产", "停产", "调整", "偏紧", "收储"]
    if any(kw in text for kw in high_intensity):
        intensity = 0.9
    elif any(kw in text for kw in med_intensity):
        intensity = 0.75

    low_conf = ["可能", "预计", "或将", "拟", "传闻", "不确定", "猜测"]
    high_conf = ["公告", "正式", "确认", "已", "决定", "签订", "达成"]
    if any(kw in text for kw in low_conf):
        confidence = 0.65
    elif any(kw in text for kw in high_conf):
        confidence = 0.95
    return intensity, confidence


def extract_event_rule_based(title: str, summary: str) -> dict[str, Any]:
    commodity = identify_commodity(title + " " + summary)
    if not commodity:
        return {"is_relevant": False}

    source_text = title + " " + summary
    event_classification = identify_event_type(source_text)
    if not event_classification:
        return {"is_relevant": False}

    event_type, subtype = event_classification
    impact_type = identify_commodity_shock(source_text)
    intensity, confidence = extract_intensity_confidence(title, summary)
    direction = commodity_impact_direction(source_text, impact_type)

    return {
        "is_relevant": True,
        "commodity": commodity,
        "event_type": event_type,
        "subtype": subtype,
        "impact_type": impact_type,
        "direction": direction,
        "intensity": intensity,
        "confidence": confidence,
        "rationale": "Rule-based keyword extraction"
    }


def analyze_event_text(
    title: str,
    summary: str = "",
    published_at: str | None = None,
    news_id: str | None = None
) -> dict[str, Any] | None:
    if not title:
        return None

    extraction_source = "rule"
    extraction_raw_output = "{}"
    extracted = None

    try:
        llm_res = extract_event_llm(title, summary)
        if llm_res is not None:
            extracted = llm_res
            extraction_source = "llm"
            extraction_raw_output = json.dumps(llm_res, ensure_ascii=False)
    except Exception as e:
        # Graceful fallback to rule-based logic
        pass

    if extracted is None:
        extracted = extract_event_rule_based(title, summary)
        extraction_source = "rule"
        extraction_raw_output = json.dumps(extracted, ensure_ascii=False)

    if not extracted.get("is_relevant"):
        return None

    commodity = extracted["commodity"]
    event_type = extracted["event_type"]
    subtype = extracted["subtype"]
    impact_type = extracted["impact_type"]
    direction = extracted["direction"]
    intensity = extracted["intensity"]
    confidence = extracted["confidence"]

    if not published_at:
        published_at = datetime.now().isoformat()

    # Generate Event ID
    h = hashlib.md5(f"{title}-{published_at}".encode("utf-8")).hexdigest()
    event_id = f"evt_{h[:16]}"
    
    # Upsert the event and replace derived rows so repeated analysis/rebuild is idempotent.
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO events(
                id, news_id, title, summary, event_type, subtype,
                intensity, direction, confidence, published_at, created_at,
                extraction_source, extraction_raw_output
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                news_id=excluded.news_id,
                title=excluded.title,
                summary=excluded.summary,
                event_type=excluded.event_type,
                subtype=excluded.subtype,
                intensity=excluded.intensity,
                direction=excluded.direction,
                confidence=excluded.confidence,
                published_at=excluded.published_at,
                created_at=excluded.created_at,
                extraction_source=excluded.extraction_source,
                extraction_raw_output=excluded.extraction_raw_output
            """,
            (
                event_id,
                news_id,
                title,
                summary,
                event_type,
                subtype,
                intensity,
                direction,
                confidence,
                published_at,
                datetime.now().isoformat(),
                extraction_source,
                extraction_raw_output
            )
        )
        conn.execute("DELETE FROM commodity_impacts WHERE event_id=?", (event_id,))
        conn.execute("DELETE FROM event_stock_scores WHERE event_id=?", (event_id,))
        conn.execute(
            """
            INSERT INTO commodity_impacts(event_id, commodity, impact_type, direction)
            VALUES (?, ?, ?, ?)
            """,
            (event_id, commodity, impact_type, direction)
        )
        
    # Query all active stocks in the pool
    stocks = db.rows("SELECT symbol, name, industry FROM stocks")
    kb = COMMODITY_KB[commodity]
    
    # Calculate Event Impact
    base_impact = {
        "geo_conflict": 90.0,
        "supply_shock": 80.0,
        "policy_change": 75.0,
        "disruption": 70.0
    }.get(event_type, 60.0)
    event_impact = min(max(base_impact + (intensity - 0.5) * 20.0, 0.0), 100.0) * confidence
    event_impact = round(event_impact, 2)
    
    # Save scores and evidence
    stock_scores_to_save = []
    
    # For mapping
    for stock in stocks:
        symbol = stock["symbol"]
        name = stock["name"]
        industry = stock["industry"]
        
        sector_exposure = 0.0
        relationship = "upstream"
        exposure_type = "none"
        
        # 1. Exact stock symbol match
        if symbol in kb["exact_stocks"]:
            sector_exposure = 100.0
            relationship = kb["exact_stocks"][symbol]["relationship"]
            exposure_type = "precise"
        # 2. Industry keywords match
        elif any(kw in industry for kw in kb["sector_keywords"]):
            sector_exposure = 60.0
            exposure_type = "keyword_fallback"
            
            # Determine relationship from industry
            if any(dkw in industry for dkw in ["汽车", "电池", "半导体", "电力设备", "航空", "机场"]):
                relationship = "downstream"
            elif any(ukw in industry for ukw in kb["upstream_sectors"]):
                relationship = "upstream"
            else:
                relationship = "upstream" # Default fallback
                
        if sector_exposure == 0.0:
            continue # No exposure, skip
            
        # Determine Direction
        if direction == "harm":
            stock_direction = "harm" if relationship == "upstream" else "benefit"
        elif impact_type in ["supply_shortage", "supply_disruption"]:
            stock_direction = "benefit" if relationship == "upstream" else "harm"
        elif impact_type == "policy_support":
            stock_direction = "benefit" if relationship == "upstream" else "harm"
        else:
            stock_direction = "benefit" if relationship == "upstream" else "harm"
            
        # Fetch Trend Strength from signals
        # Get the latest signal_date in the database, then find the stock trend_score
        trend_strength = 50.0
        latest_sig = db.row(
            """
            SELECT trend_score FROM signals 
            WHERE symbol=? 
            ORDER BY signal_date DESC LIMIT 1
            """,
            (symbol,)
        )
        if latest_sig:
            trend_strength = float(latest_sig["trend_score"])
            
        # Event Score formula:
        # Event Score = 0.5 * Event Impact + 0.3 * Sector Exposure + 0.2 * Trend Strength
        event_score = 0.5 * event_impact + 0.3 * sector_exposure + 0.2 * trend_strength
        event_score = round(min(max(event_score, 0.0), 100.0), 2)
        
        # Build causal chain details
        causal_chain = {
            "commodity": commodity,
            "commodity_name": kb["name"],
            "impact_type": impact_type,
            "relationship": relationship,
            "exposure_type": exposure_type,
            "sector": industry
        }
        
        source_label = "LLM 优先抽取" if extraction_source == "llm" else "规则回退"
        evidence = (
            f"新闻事件《{title}》（来源：{source_label}）识别为 {kb['name']} 行业的 {impact_type} 冲击。 "
            f"该股票属于 {industry} 行业（通过 {exposure_type} 映射，属于 {relationship} 环节）。"
            f"计算分解：Event Score = 0.5 * Event Impact ({event_impact}) + 0.3 * Sector Exposure ({sector_exposure}) + 0.2 * Trend Strength ({trend_strength}) = {event_score}。 "
            f"影响方向：{'受益 (benefit)' if stock_direction == 'benefit' else '受损 (harm)'}。"
        )
        
        stock_scores_to_save.append({
            "event_id": event_id,
            "symbol": symbol,
            "name": name,
            "industry": industry,
            "event_score": event_score,
            "event_impact": event_impact,
            "sector_exposure": sector_exposure,
            "trend_strength": trend_strength,
            "direction": stock_direction,
            "causal_chain": json.dumps(causal_chain, ensure_ascii=False),
            "evidence": evidence
        })
        
    with db.connect() as conn:
        for item in stock_scores_to_save:
            conn.execute(
                """
                INSERT OR REPLACE INTO event_stock_scores(
                    event_id, symbol, event_score, event_impact, sector_exposure,
                    trend_strength, direction, causal_chain, evidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["event_id"],
                    item["symbol"],
                    item["event_score"],
                    item["event_impact"],
                    item["sector_exposure"],
                    item["trend_strength"],
                    item["direction"],
                    item["causal_chain"],
                    item["evidence"]
                )
            )
            
    # Load and return the saved event with full causal chain and stock scores
    return get_event_detail_by_id(event_id)

def get_event_detail_by_id(event_id: str) -> dict[str, Any] | None:
    event = db.row("SELECT * FROM events WHERE id=?", (event_id,))
    if not event:
        return None
        
    commodity_impacts = db.rows(
        "SELECT commodity, impact_type, direction FROM commodity_impacts WHERE event_id=?",
        (event_id,)
    )
    
    stock_scores_raw = db.rows(
        """
        SELECT ess.*, s.name, s.industry 
        FROM event_stock_scores ess
        JOIN stocks s ON ess.symbol = s.symbol
        WHERE ess.event_id=?
        ORDER BY ess.direction ASC, ess.event_score DESC
        """,
        (event_id,)
    )
    
    stock_scores = []
    for s in stock_scores_raw:
        s["causal_chain"] = json.loads(s["causal_chain"])
        stock_scores.append(s)
        
    event_dict = dict(event)
    event_dict["commodity_impacts"] = [dict(ci) for ci in commodity_impacts]
    event_dict["stock_scores"] = stock_scores
    return event_dict
