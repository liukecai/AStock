from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .. import db


def calculate_v2_transmission(event_id: str) -> None:
    """
    Calculates the V2 transmission scoring for a given event, including
    commodity price direction, company earnings impacts, and stock reaction scores.
    Saves results to event_earnings_impacts and event_stock_reaction_scores_v2.
    """
    # 1. Clear existing V2 rows for this event to keep it idempotent
    with db.connect() as conn:
        conn.execute("DELETE FROM event_earnings_impacts WHERE event_id=?", (event_id,))
        conn.execute("DELETE FROM event_stock_reaction_scores_v2 WHERE event_id=?", (event_id,))

    # 2. Get event
    event = db.row("SELECT * FROM events WHERE id=?", (event_id,))
    if not event:
        return

    # 3. Get commodity impacts
    impacts = db.rows("SELECT * FROM commodity_impacts WHERE event_id=?", (event_id,))
    if not impacts:
        return

    intensity = event.get("intensity", 0.6)
    confidence = event.get("confidence", 0.85)

    for impact in impacts:
        commodity = impact.get("commodity")
        # Support only curated commodities
        if commodity not in ("oil", "lithium", "copper"):
            continue

        impact_type = impact.get("impact_type", "supply_shortage")
        direction = impact.get("direction", "benefit")

        # Map commodity price direction
        price_direction = "price_up" if direction == "benefit" else "price_down"

        # Base scores by impact_type
        base_scores = {
            "supply_disruption": 90.0,
            "supply_shortage": 85.0,
            "oversupply": 80.0,
            "supply_increase": 75.0,
            "demand_weakness": 70.0,
            "policy_support": 70.0
        }
        base_score = base_scores.get(impact_type, 75.0)
        shock_score = round(min(max(base_score + (intensity - 0.5) * 20.0, 0.0), 100.0) * confidence, 2)

        # Get company profiles
        profiles = db.rows("SELECT * FROM company_commodity_profiles WHERE commodity=?", (commodity,))
        for profile in profiles:
            symbol = profile["symbol"]
            role = profile["role"]
            channel = profile["channel"]
            benefit_when_price_up = profile["benefit_when_price_up"]
            benefit_when_price_down = profile["benefit_when_price_down"]
            exposure_strength = profile["exposure_strength"]
            pricing_power = profile["pricing_power"]
            inventory_sensitivity = profile["inventory_sensitivity"]
            pass_through_ability = profile["pass_through_ability"]
            earnings_elasticity = profile["earnings_elasticity"]
            lag_days = profile["lag_days"]

            # Company direction
            if price_direction == "price_up":
                stock_direction = "benefit" if benefit_when_price_up == 1 else "harm"
            else:
                stock_direction = "benefit" if benefit_when_price_down == 1 else "harm"

            # Exposure score
            exposure_score = round(
                0.6 * exposure_strength +
                0.15 * pricing_power +
                0.15 * pass_through_ability +
                0.1 * inventory_sensitivity,
                2
            )

            # Revenue impact score
            if channel == "revenue":
                revenue_impact_score = 85.0 + 0.15 * earnings_elasticity
            elif channel == "spread":
                revenue_impact_score = 50.0 + 0.1 * pricing_power
            else:
                revenue_impact_score = 20.0

            # Margin impact score
            if channel == "cost":
                margin_impact_score = 85.0 + 0.15 * pass_through_ability
            elif channel == "spread":
                margin_impact_score = 80.0 + 0.15 * pricing_power
            elif channel == "inventory":
                margin_impact_score = 75.0 + 0.15 * inventory_sensitivity
            else:
                margin_impact_score = 30.0

            # Profit impact score
            profit_impact_score = 0.5 * (revenue_impact_score + margin_impact_score) * (0.5 + 0.5 * (earnings_elasticity / 100.0))

            # Lag discount
            lag_discount = 1.0 - min(lag_days, 90) / 180.0
            earnings_score = round(profit_impact_score * lag_discount, 2)

            # Sentiment score (phase 1: baseline 50 + role/profile boost)
            boost = 5.0
            if role == "upstream_resource":
                boost = 15.0
            elif role in ("downstream_manufacturing", "transport"):
                boost = 10.0
            sentiment_score = 50.0 + boost

            # Trend score (reuses signals.trend_score, falls back to 50)
            trend_score = 50.0
            latest_sig = db.row(
                """
                SELECT trend_score FROM signals 
                WHERE symbol=? 
                ORDER BY signal_date DESC LIMIT 1
                """,
                (symbol,)
            )
            if latest_sig:
                trend_score = float(latest_sig["trend_score"])

            # Final V2 reaction score
            reaction_score = round(
                0.25 * shock_score +
                0.25 * exposure_score +
                0.25 * earnings_score +
                0.15 * sentiment_score +
                0.10 * trend_score,
                2
            )

            reason = (
                f"针对商品 {commodity} 的 {impact_type} 冲击，该企业角色为 {role}，传导渠道为 {channel}。 "
                f"由于该商品价格预期为 {price_direction}，企业{'受益' if stock_direction == 'benefit' else '受损'}。 "
                f"其中，收入影响得分为 {revenue_impact_score:.1f}，毛利影响得分为 {margin_impact_score:.1f}，"
                f"综合利润影响得分为 {profit_impact_score:.1f}（弹性系数 {earnings_elasticity:.1f}，滞后天数 {lag_days}天）。"
            )

            transmission_chain = {
                "commodity": commodity,
                "price_direction": price_direction,
                "role": role,
                "channel": channel,
                "lag_days": lag_days,
                "scores": {
                    "shock": shock_score,
                    "exposure": exposure_score,
                    "earnings": earnings_score,
                    "sentiment": sentiment_score,
                    "trend": trend_score
                }
            }

            evidence = (
                f"新闻识别到 {commodity} 发生 {impact_type} 冲击（冲击得分: {shock_score:.1f}）。 "
                f"根据企业商品画像（{symbol}），其主要角色是 {role}，主要业务传导渠道是 {channel}。 "
                f"预期商品价格走向为 {price_direction}，由此判定股票反应方向为 {stock_direction}。 "
                f"细分得分：曝险得分 {exposure_score:.1f}，业绩传导得分 {earnings_score:.1f}，"
                f"市场情绪得分 {sentiment_score:.1f}，趋势得分 {trend_score:.1f}。 "
                f"最终 V2 传导评分: {reaction_score:.1f}。"
            )

            with db.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO event_earnings_impacts (
                        event_id, symbol, commodity, revenue_impact_score, margin_impact_score,
                        profit_impact_score, confidence, horizon, reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id, symbol, commodity, revenue_impact_score, margin_impact_score,
                        profit_impact_score, confidence, "medium", reason
                    )
                )

                conn.execute(
                    """
                    INSERT INTO event_stock_reaction_scores_v2 (
                        event_id, symbol, commodity, shock_score, exposure_score,
                        earnings_score, sentiment_score, trend_score, reaction_score,
                        direction, horizon, confidence, transmission_chain, evidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id, symbol, commodity, shock_score, exposure_score,
                        earnings_score, sentiment_score, trend_score, reaction_score,
                        stock_direction, "medium", confidence, json.dumps(transmission_chain, ensure_ascii=False), evidence
                    )
                )


def get_event_reactions_v2(event_id: str) -> dict[str, Any] | None:
    """
    Returns the event detail hydrated with V2 reaction scores and transmission chain.
    """
    event = db.row("SELECT * FROM events WHERE id=?", (event_id,))
    if not event:
        return None

    event_dict = dict(event)
    event_dict["commodity_impacts"] = db.rows(
        "SELECT commodity, impact_type, direction FROM commodity_impacts WHERE event_id=?",
        (event_id,)
    )

    reactions = db.rows(
        """
        SELECT r.*, s.name, s.industry 
        FROM event_stock_reaction_scores_v2 r
        JOIN stocks s ON r.symbol = s.symbol
        WHERE r.event_id=?
        ORDER BY r.reaction_score DESC
        """,
        (event_id,)
    )

    reactions_decoded = []
    for r in reactions:
        r_dict = dict(r)
        r_dict["transmission_chain"] = json.loads(r_dict["transmission_chain"])
        reactions_decoded.append(r_dict)

    event_dict["reactions"] = reactions_decoded
    return event_dict


def get_stock_exposure_v2(symbol: str) -> dict[str, Any] | None:
    """
    Returns stock basic details and its corresponding company commodity profiles.
    """
    stock = db.row("SELECT * FROM stocks WHERE symbol=?", (symbol,))
    if not stock:
        return None

    profiles = db.rows(
        "SELECT * FROM company_commodity_profiles WHERE symbol=?",
        (symbol,)
    )
    if not profiles:
        return None

    return {
        "stock": dict(stock),
        "profiles": [dict(p) for p in profiles]
    }
