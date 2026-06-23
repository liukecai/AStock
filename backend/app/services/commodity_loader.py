"""
commodity_loader.py
-------------------
从 config/commodity_graph/*.yaml 加载商品知识库，返回与原 COMMODITY_KB 字典
结构相同的数据，并附带数据库 seed 所需的额外字段（_sector_mappings、
_sector_exposures、_company_profiles）。

若 YAML 目录不存在或加载失败，会打印警告并返回空字典，由调用方决定是否回退
到硬编码数据。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# config/commodity_graph/ 相对于本文件的路径
_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config" / "commodity_graph"


def _load_yaml_safe(path: Path) -> dict[str, Any] | None:
    """安全加载单个 YAML 文件；失败时打印错误并返回 None。"""
    try:
        import yaml  # type: ignore[import]
    except ImportError:
        print(
            "[commodity_loader] pyyaml 未安装，无法加载商品 YAML 配置。"
            "请执行: pip install pyyaml",
            file=sys.stderr,
        )
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as exc:
        print(f"[commodity_loader] 加载 {path.name} 失败: {exc}", file=sys.stderr)
        return None


def load_commodity_kb() -> dict[str, Any]:
    """
    加载所有商品 YAML 文件，返回 COMMODITY_KB 格式的字典。

    每个 key 对应一种商品，value 包含：
    - name, keywords, exact_stocks, sector_keywords,
      default_sector, upstream_sectors, downstream_sectors
      （供 event_engine 识别与评分使用）
    - _sector_mappings:  list[dict]  供 init_db seed commodity_sector_mappings
    - _sector_exposures: list[dict]  供 init_db seed sector_stock_exposures
    - _company_profiles: list[dict]  供 init_db seed company_commodity_profiles
    """
    if not _CONFIG_DIR.exists():
        print(
            f"[commodity_loader] 配置目录 {_CONFIG_DIR} 不存在，跳过 YAML 加载。",
            file=sys.stderr,
        )
        return {}

    kb: dict[str, Any] = {}
    yaml_files = sorted(_CONFIG_DIR.glob("*.yaml"))
    if not yaml_files:
        print(
            f"[commodity_loader] {_CONFIG_DIR} 目录下没有 .yaml 文件。",
            file=sys.stderr,
        )
        return {}

    for yaml_file in yaml_files:
        data = _load_yaml_safe(yaml_file)
        if data is None:
            continue
        commodity = data.get("commodity")
        if not commodity:
            print(
                f"[commodity_loader] {yaml_file.name} 缺少 'commodity' 字段，已跳过。",
                file=sys.stderr,
            )
            continue

        # exact_stocks: YAML 中 key 是字符串股票代码，value 是 {relationship, name}
        raw_exact = data.get("exact_stocks") or {}
        exact_stocks: dict[str, dict[str, str]] = {
            str(sym): {"relationship": cfg.get("relationship", "upstream"), "name": cfg.get("name", "")}
            for sym, cfg in raw_exact.items()
        }

        kb[commodity] = {
            "name": data.get("name", commodity),
            "keywords": data.get("keywords") or [],
            "exact_stocks": exact_stocks,
            "sector_keywords": data.get("sector_keywords") or [],
            "default_sector": data.get("default_sector", ""),
            "upstream_sectors": data.get("upstream_sectors") or [],
            "downstream_sectors": data.get("downstream_sectors") or [],
            # Extra fields for DB seeding (not used by event_engine directly)
            "_sector_mappings": [
                {
                    "commodity": commodity,
                    "sector": m["sector"],
                    "relationship": m.get("relationship", "upstream"),
                    "coefficient": float(m.get("coefficient", 1.0)),
                }
                for m in (data.get("sector_mappings") or [])
            ],
            "_sector_exposures": [
                {
                    "sector": e["sector"],
                    "symbol": str(e["symbol"]),
                    "exposure": float(e.get("exposure", 100.0)),
                }
                for e in (data.get("sector_exposures") or [])
            ],
            "_company_profiles": [
                {
                    "symbol": str(p["symbol"]),
                    "commodity": commodity,
                    "role": p.get("role", "upstream_resource"),
                    "channel": p.get("channel", "revenue"),
                    "benefit_when_price_up": int(bool(p.get("benefit_when_price_up", True))),
                    "benefit_when_price_down": int(bool(p.get("benefit_when_price_down", False))),
                    "exposure_strength": float(p.get("exposure_strength", 50.0)),
                    "pricing_power": float(p.get("pricing_power", 50.0)),
                    "inventory_sensitivity": float(p.get("inventory_sensitivity", 50.0)),
                    "pass_through_ability": float(p.get("pass_through_ability", 50.0)),
                    "earnings_elasticity": float(p.get("earnings_elasticity", 50.0)),
                    "lag_days": int(p.get("lag_days", 0)),
                    "evidence": p.get("evidence", ""),
                }
                for p in (data.get("company_profiles") or [])
            ],
        }

    return kb


# Module-level singleton loaded once at import time.
# Call reload_kb() to refresh without restarting the process.
_COMMODITY_KB: dict[str, Any] = {}


def get_commodity_kb() -> dict[str, Any]:
    """返回当前已加载的 COMMODITY_KB，若未初始化则先加载。"""
    global _COMMODITY_KB
    if not _COMMODITY_KB:
        _COMMODITY_KB = load_commodity_kb()
    return _COMMODITY_KB


def reload_kb() -> dict[str, Any]:
    """热重载：重新读取所有 YAML 文件并更新模块级缓存。"""
    global _COMMODITY_KB
    _COMMODITY_KB = load_commodity_kb()
    print(f"[commodity_loader] 知识库已重载，共 {len(_COMMODITY_KB)} 种商品。", file=sys.stderr)
    return _COMMODITY_KB
