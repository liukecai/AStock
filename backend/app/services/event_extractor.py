from typing import Any, Tuple, Optional

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

def identify_event_type(text: str) -> Optional[Tuple[str, str]]:
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
    if any(kw in lowered for kw in ["恢复产量", "产量恢复", "增产", "扩产", "提高产量"]):
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

def extract_intensity_confidence(title: str, summary: str) -> Tuple[float, float]:
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

def identify_commodity_from_db(text: str, db_module) -> Optional[dict]:
    """
    Search kg_entities for a matching commodity based on the text.
    """
    lowered = text.lower()
    rows = db_module.rows(
        "SELECT entity_id, name, aliases_json FROM kg_entities WHERE entity_type IN ('Commodity', 'Product', 'Material') AND status='active'"
    )
    for row in rows:
            import json
            aliases = json.loads(row["aliases_json"]) if isinstance(row["aliases_json"], str) else row["aliases_json"]
            keywords = [row["name"].lower()] + [a.lower() for a in aliases]
            if any(kw in lowered for kw in keywords):
                return {"entity_id": row["entity_id"], "name": row["name"]}
    return None

def extract_event_rule_based(title: str, summary: str, db_module) -> dict[str, Any]:
    source_text = title + " " + summary
    commodity_data = identify_commodity_from_db(source_text, db_module)
    if not commodity_data:
        return {"is_relevant": False}

    event_classification = identify_event_type(source_text)
    if not event_classification:
        return {"is_relevant": False}

    event_type, subtype = event_classification
    impact_type = identify_commodity_shock(source_text)
    intensity, confidence = extract_intensity_confidence(title, summary)
    direction = commodity_impact_direction(source_text, impact_type)

    return {
        "is_relevant": True,
        "commodity": commodity_data["name"],
        "entity_id": commodity_data["entity_id"],
        "event_type": event_type,
        "subtype": subtype,
        "impact_type": impact_type,
        "direction": direction,
        "intensity": intensity,
        "confidence": confidence,
        "rationale": "Rule-based keyword extraction"
    }
