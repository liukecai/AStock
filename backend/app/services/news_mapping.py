from __future__ import annotations

import re
from dataclasses import dataclass

from .. import db


CURATED_ALIASES = {
    "CATL": "300750",
    "Contemporary Amperex": "300750",
    "BYD": "002594",
    "Kweichow Moutai": "600519",
    "Moutai": "600519",
    "SMIC": "688981",
    "China Merchants Bank": "600036",
    "CMB": "600036",
    "Wuliangye": "000858",
}

NAME_SUFFIXES = (
    "股份有限公司",
    "集团股份有限公司",
    "集团有限公司",
    "股份",
    "集团",
    "控股",
)


@dataclass(frozen=True)
class StockMatch:
    symbol: str
    confidence: float
    match_type: str
    alias: str


def _derived_aliases(name: str) -> set[str]:
    aliases = {name}
    clean = re.sub(r"^(?:\*?ST|SST|N)", "", name, flags=re.IGNORECASE).strip()
    aliases.add(clean)
    for suffix in NAME_SUFFIXES:
        if clean.endswith(suffix):
            aliases.add(clean[: -len(suffix)])
    return {alias for alias in aliases if len(alias) >= 3}


def sync_stock_aliases() -> int:
    stocks = db.rows("SELECT symbol, name FROM stocks")
    rows: list[tuple[str, str, str, float]] = []
    symbols = {item["symbol"] for item in stocks}
    for stock in stocks:
        for alias in _derived_aliases(stock["name"]):
            confidence = 1.0 if alias == stock["name"] else 0.9
            rows.append((alias, stock["symbol"], "zh", confidence))
    for alias, symbol in CURATED_ALIASES.items():
        if symbol in symbols:
            rows.append((alias, symbol, "en", 0.95))
    with db.connect() as conn:
        conn.executemany(
            """
            INSERT INTO stock_aliases(alias, symbol, language, confidence)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(alias, symbol) DO UPDATE SET
              language=excluded.language, confidence=excluded.confidence
            """,
            rows,
        )
    return len(rows)


def map_text_to_stocks(text: str, max_matches: int = 12) -> list[StockMatch]:
    if not text:
        return []
    aliases = db.rows(
        """
        SELECT alias, symbol, language, confidence
        FROM stock_aliases
        ORDER BY length(alias) DESC
        """
    )
    lowered = text.casefold()
    matches: dict[str, StockMatch] = {}
    for item in aliases:
        alias = item["alias"]
        if alias.casefold() not in lowered:
            continue
        candidate = StockMatch(
            symbol=item["symbol"],
            confidence=float(item["confidence"]),
            match_type="alias",
            alias=alias,
        )
        existing = matches.get(candidate.symbol)
        if not existing or candidate.confidence > existing.confidence:
            matches[candidate.symbol] = candidate

    valid_symbols = {
        item["symbol"] for item in db.rows("SELECT symbol FROM stocks")
    }
    for symbol in set(re.findall(r"(?<!\d)([0368]\d{5})(?!\d)", text)):
        if symbol in valid_symbols:
            matches[symbol] = StockMatch(symbol, 1.0, "symbol", symbol)

    return sorted(
        matches.values(), key=lambda item: item.confidence, reverse=True
    )[:max_matches]

