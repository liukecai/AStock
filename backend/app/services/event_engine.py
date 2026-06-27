import hashlib
import json
import sys
from datetime import datetime
from typing import Any

from .. import db
from .event_llm import extract_event_llm
from .event_extractor import extract_event_rule_based, identify_commodity_from_db
from .graph_querier import query_impacted_stocks
from .exposure_calculator import calculate_exposure
from .scoring_engine import calculate_stock_score, rank_stocks

def reload_commodity_kb() -> None:
    # Deprecated in V2. Left for backward compatibility.
    pass

def analyze_event_text(
    title: str,
    summary: str = "",
    published_at: str | None = None,
    news_id: str | None = None
) -> dict[str, Any] | None:
    if not title:
        return None

    extraction_source = "rule"
    extracted = None

    try:
        llm_res = extract_event_llm(title, summary)
        if llm_res is not None:
            extracted = llm_res
            extraction_source = "llm"
    except Exception as e:
        pass

    if extracted is None:
        extracted = extract_event_rule_based(title, summary, db)
        extraction_source = "rule"

    if not extracted or not extracted.get("is_relevant"):
        return None

    commodity_name = extracted.get("commodity")
    entity_id = extracted.get("entity_id")
    event_type = extracted.get("event_type", "supply_shock")
    subtype = extracted.get("subtype", "general")
    impact_type = extracted.get("impact_type", "supply_shortage")
    direction = extracted.get("direction", "benefit")
    intensity = extracted.get("intensity", 0.6)
    confidence = extracted.get("confidence", 0.8)

    if not published_at:
        published_at = datetime.now().isoformat()
        
    pub_dt = datetime.fromisoformat(published_at)

    h = hashlib.md5(f"{title}-{published_at}".encode("utf-8")).hexdigest()
    event_id = f"evt_v2_{h[:16]}"
    
    with db.connect() as conn:
        # Save to V2 EventInstance
        db._exec(
            conn,
            """
            INSERT INTO event_instances(
                event_id, event_type, subtype, title, description,
                entities_json, intensity, direction, occurred_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                event_type=excluded.event_type,
                subtype=excluded.subtype,
                title=excluded.title,
                description=excluded.description,
                entities_json=excluded.entities_json,
                intensity=excluded.intensity,
                direction=excluded.direction,
                occurred_at=excluded.occurred_at
            """,
            (
                event_id, event_type, subtype, title, summary,
                json.dumps([{"entity_id": entity_id, "name": commodity_name}]),
                intensity, direction, pub_dt, datetime.now()
            )
        )
        
        # Save to V2 EventImpact
        impact_id = f"imp_{h[:8]}_{entity_id}"
        db._exec(
            conn,
            """
            INSERT INTO event_impacts(impact_id, event_id, entity_id, impact_type, impact_score)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(impact_id) DO UPDATE SET impact_score=excluded.impact_score
            """,
            (impact_id, event_id, entity_id, impact_type, intensity)
        )
        
    # Reason
    paths = query_impacted_stocks(db, entity_id, context_date=pub_dt, max_depth=4)
    scored_paths = calculate_exposure(paths, depth_decay_factor=0.8)
    
    # Calculate scores
    final_stock_scores = []
    
    for path in scored_paths:
        symbol = path.get("stock_symbol") or path["stock_or_company_id"]
        # Fetch trend score
        trend_score = 50.0
        latest_sig = db.row("SELECT trend_score FROM signals WHERE symbol=? ORDER BY signal_date DESC LIMIT 1", (symbol,))
        if latest_sig:
            trend_score = float(latest_sig["trend_score"])
            
        score_data = calculate_stock_score(
            exposure_score=path["exposure_score"],
            exposure_confidence=path["confidence"],
            event_type=event_type,
            event_intensity=intensity,
            event_confidence=confidence,
            trend_strength=trend_score
        )
        
        # Determine stock direction
        # Simple rule: if first edge is downstream, flip direction if harm? 
        # Actually, let's keep it simple for MVP: follow the event's commodity direction if upstream, flip if downstream.
        stock_direction = direction
        if path["edges"]:
            first_edge = path["edges"][0]
            if first_edge["relation_type"] in ["uses", "downstream"]:
                stock_direction = "benefit" if direction == "harm" else "harm"
        
        score_data["direction"] = stock_direction
        score_data["symbol"] = symbol
        score_data["entity_id"] = path["stock_or_company_id"]
        score_data["path"] = path
        final_stock_scores.append(score_data)
        
    final_stock_scores = rank_stocks(final_stock_scores)
    
    with db.connect() as conn:
        # Clear existing paths and scores for this event (if any)
        db._exec(conn, "DELETE FROM stock_event_scores WHERE event_id=?", (event_id,))
        db._exec(conn, "DELETE FROM stock_exposures WHERE event_id=?", (event_id,))
        db._exec(conn, "DELETE FROM reasoning_paths WHERE event_id=?", (event_id,))
        
        for idx, item in enumerate(final_stock_scores):
            path = item["path"]
            path_id = f"path_{event_id}_{item['symbol']}"
            
            db._exec(
                conn,
                """
                INSERT INTO reasoning_paths(
                    path_id, event_id, stock_code, start_entity_id, end_entity_id,
                    nodes_json, edges_json, path_score, path_length, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    path_id, event_id, item['symbol'], entity_id, item['entity_id'],
                    json.dumps(path["nodes"], ensure_ascii=False),
                    json.dumps(path["edges"], ensure_ascii=False),
                    path["exposure_score"], path["path_length"], datetime.now()
                )
            )
            
            db._exec(
                conn,
                """
                INSERT INTO stock_exposures(
                    event_id, stock_code, entity_id, exposure_score, confidence, reason_path_id
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id, item['symbol'], entity_id, path["exposure_score"],
                    path["confidence"], path_id
                )
            )
            
            b = item["score_breakdown"]
            b["direction"] = item["direction"]
            db._exec(
                conn,
                """
                INSERT INTO stock_event_scores(
                    event_id, stock_code, final_score, exposure_score, trend_score,
                    sentiment_score, volume_score, event_intensity, validation_score,
                    score_breakdown_json, confidence, rank, label, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id, item['symbol'], item["final_score"], b["sector_exposure"],
                    b["trend_strength"], b["sentiment_score"], b["volume_score"],
                    intensity, 0.0, json.dumps(b, ensure_ascii=False),
                    item["confidence"], item["rank"], item["label"], datetime.now()
                )
            )
            
    return get_event_detail_by_id(event_id)

def get_event_detail_by_id(event_id: str) -> dict[str, Any] | None:
    event = db.row("SELECT *, event_id as id FROM event_instances WHERE event_id=?", (event_id,))
    if not event:
        return None
        
    impacts = db.rows(
        "SELECT i.*, k.name AS commodity FROM event_impacts i JOIN kg_entities k ON i.entity_id = k.entity_id WHERE i.event_id=?", 
        (event_id,)
    )
    
    scores = db.rows(
        """
        SELECT s.*, r.nodes_json, r.edges_json, st.name, st.industry
        FROM stock_event_scores s
        JOIN reasoning_paths r ON s.event_id = r.event_id AND s.stock_code = r.stock_code
        LEFT JOIN stocks st ON s.stock_code = st.symbol
        WHERE s.event_id=?
        ORDER BY s.rank ASC
        """,
        (event_id,)
    )
    
    stock_scores = []
    for s in scores:
        sd = dict(s)
        if isinstance(sd.get("score_breakdown_json"), str):
            sd["score_breakdown_json"] = json.loads(sd["score_breakdown_json"])
        if isinstance(sd.get("nodes_json"), str):
            sd["nodes_json"] = json.loads(sd["nodes_json"])
        if isinstance(sd.get("edges_json"), str):
            sd["edges_json"] = json.loads(sd["edges_json"])
            
        b = sd.get("score_breakdown_json", {})
        sd["direction"] = b.get("direction", "benefit")
        sd["event_score"] = sd.get("final_score", 0.0)
        sd["event_impact"] = b.get("event_impact", 0.0)
        sd["sector_exposure"] = b.get("sector_exposure", 0.0)
        sd["trend_strength"] = b.get("trend_strength", 0.0)
        sd["evidence"] = "基于知识图谱的多跳因果推理"
        
        stock_scores.append(sd)
        
    event_dict = dict(event)
    event_dict["commodity_impacts"] = [dict(i) for i in impacts]
    event_dict["stock_scores"] = stock_scores
    if isinstance(event_dict.get("entities_json"), str):
        event_dict["entities_json"] = json.loads(event_dict["entities_json"])
        
    return event_dict
