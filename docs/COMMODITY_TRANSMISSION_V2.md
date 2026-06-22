# Commodity Transmission V2

## Goal

Upgrade the current commodity event engine from:

`event -> commodity shock -> sector/stock`

to:

`event/price move -> commodity shock -> company business exposure -> earnings transmission -> market sentiment -> stock reaction`

This first-stage implementation should stay narrow and production-safe:

- keep the current V1 event APIs and scoring behavior unchanged
- add a parallel V2 transmission layer
- support only `oil`, `lithium`, and `copper`
- focus on backend data model, scoring, and read-only APIs

## Scope

### In scope

1. Add company commodity profile data for a small curated stock universe
2. Add V2 reaction scoring on top of existing detected events
3. Persist V2 scores and transmission details in SQLite
4. Add read-only APIs for:
   - event V2 reaction detail
   - stock commodity exposure detail
5. Seed initial profiles for `oil`, `lithium`, `copper`
6. Add tests for scoring and API access

### Out of scope

1. Do not replace the current `event_stock_scores` V1 table or endpoints
2. Do not build a full sentiment engine from live board behavior yet
3. Do not add a heavy frontend redesign in this step
4. Do not attempt full-market automatic profile generation

## Architecture

### Current V1

`event -> commodity_impacts -> event_stock_scores`

### Added V2

`event -> commodity shock -> company commodity profile -> earnings transmission -> reaction score`

V2 should reuse the existing event detection result from `events` and `commodity_impacts`.

## Data model

### 1. company_commodity_profiles

One row per `symbol + commodity`.

Suggested schema:

- `symbol TEXT NOT NULL`
- `commodity TEXT NOT NULL`
- `role TEXT NOT NULL`
- `channel TEXT NOT NULL`
- `benefit_when_price_up INTEGER NOT NULL DEFAULT 0`
- `benefit_when_price_down INTEGER NOT NULL DEFAULT 0`
- `exposure_strength REAL NOT NULL DEFAULT 50.0`
- `pricing_power REAL NOT NULL DEFAULT 50.0`
- `inventory_sensitivity REAL NOT NULL DEFAULT 50.0`
- `pass_through_ability REAL NOT NULL DEFAULT 50.0`
- `earnings_elasticity REAL NOT NULL DEFAULT 50.0`
- `lag_days INTEGER NOT NULL DEFAULT 0`
- `evidence TEXT NOT NULL DEFAULT ''`
- `updated_at TEXT NOT NULL`

Primary key:

- `(symbol, commodity)`

Allowed values:

- `role`
  - `upstream_resource`
  - `upstream_service`
  - `midstream_processing`
  - `downstream_manufacturing`
  - `transport`

- `channel`
  - `revenue`
  - `cost`
  - `spread`
  - `inventory`

### 2. event_earnings_impacts

One row per `event + symbol` for the intermediate business transmission output.

Suggested schema:

- `event_id TEXT NOT NULL`
- `symbol TEXT NOT NULL`
- `commodity TEXT NOT NULL`
- `revenue_impact_score REAL NOT NULL`
- `margin_impact_score REAL NOT NULL`
- `profit_impact_score REAL NOT NULL`
- `confidence REAL NOT NULL DEFAULT 0.7`
- `horizon TEXT NOT NULL DEFAULT 'medium'`
- `reason TEXT NOT NULL`

Primary key:

- `(event_id, symbol)`

### 3. event_stock_reaction_scores_v2

Final V2 reaction scores.

Suggested schema:

- `event_id TEXT NOT NULL`
- `symbol TEXT NOT NULL`
- `commodity TEXT NOT NULL`
- `shock_score REAL NOT NULL`
- `exposure_score REAL NOT NULL`
- `earnings_score REAL NOT NULL`
- `sentiment_score REAL NOT NULL`
- `trend_score REAL NOT NULL`
- `reaction_score REAL NOT NULL`
- `direction TEXT NOT NULL`
- `horizon TEXT NOT NULL DEFAULT 'medium'`
- `confidence REAL NOT NULL DEFAULT 0.7`
- `transmission_chain TEXT NOT NULL`
- `evidence TEXT NOT NULL`

Primary key:

- `(event_id, symbol)`

Allowed values:

- `direction`: `benefit` or `harm`
- `horizon`: `short`, `medium`, `fundamental`

## Initial curated company profiles

Seed only a compact first batch.

### Oil

- `601857` 中国石油
  - `role=upstream_resource`
  - `channel=revenue`
  - `benefit_when_price_up=1`
  - `earnings_elasticity=85`

- `600028` 中国石化
  - `role=midstream_processing`
  - `channel=spread`
  - `benefit_when_price_up=1`
  - `benefit_when_price_down=1`
  - lower confidence than pure upstream

- `601808` 中海油服
  - `role=upstream_service`
  - `channel=revenue`
  - `benefit_when_price_up=1`
  - positive lag due to capex transmission

- `601111` 中国国航
  - `role=transport`
  - `channel=cost`
  - `benefit_when_price_down=1`

### Lithium

- `002466` 天齐锂业
- `002460` 赣锋锂业
- `000792` 盐湖股份
  - `role=upstream_resource`
  - `channel=revenue`
  - `benefit_when_price_up=1`
  - `benefit_when_price_down=0`

- `300750` 宁德时代
  - `role=downstream_manufacturing`
  - `channel=cost`
  - `benefit_when_price_down=1`

### Copper

- `600362` 江西铜业
- `601899` 紫金矿业
- `000878` 云南铜业
  - `role=upstream_resource`
  - `channel=revenue`
  - `benefit_when_price_up=1`

- `300274` 阳光电源
  - `role=downstream_manufacturing`
  - `channel=cost`
  - `benefit_when_price_down=1`

## Scoring

V2 reaction score:

`0.25 * shock_score + 0.25 * exposure_score + 0.25 * earnings_score + 0.15 * sentiment_score + 0.10 * trend_score`

### shock_score

Derived from existing event extraction output:

- base by `impact_type`
- adjusted by `intensity` and `confidence`

### exposure_score

Primarily from `company_commodity_profiles.exposure_strength`, adjusted by:

- `pricing_power`
- `pass_through_ability`
- `inventory_sensitivity`

### earnings_score

Derived from:

- price direction vs `benefit_when_price_up/down`
- `earnings_elasticity`
- `channel`
- `lag_days`

### sentiment_score

Keep this simple in phase 1:

- start from a constant baseline `50`
- optionally boost exact-profile names already known as market leaders

### trend_score

Reuse existing latest `signals.trend_score`, fallback to `50`

## Transmission rules

Implement simple deterministic rules first.

### Price direction

Map current event direction to a commodity price direction:

- `direction=benefit` on commodity impact means commodity price/support is positive -> `price_up`
- `direction=harm` means commodity price/support is negative -> `price_down`

### Company direction

For each company profile:

- if `price_up` and `benefit_when_price_up=1` -> stock direction `benefit`
- if `price_up` and `benefit_when_price_up=0` -> stock direction `harm`
- if `price_down` and `benefit_when_price_down=1` -> stock direction `benefit`
- if `price_down` and `benefit_when_price_down=0` -> stock direction `harm`

### Earnings heuristics

Suggested first-stage formulas:

- `revenue_impact_score`
  - high for `channel=revenue` when aligned with commodity move
  - low for `channel=cost`

- `margin_impact_score`
  - high for `channel=cost` when move reduces input costs
  - high for `channel=spread` when move favors crack/spread logic

- `profit_impact_score`
  - weighted blend of revenue/margin plus elasticity

## API

Add read-only endpoints:

### GET /api/events/{event_id}/reaction

Returns:

- event core fields
- commodity impacts
- V2 reaction scores ordered by `reaction_score DESC`
- embedded transmission chain and evidence

### GET /api/stocks/{symbol}/commodity-exposure

Returns:

- stock basic info
- all company commodity profiles for that symbol

## Service layout

Suggested new service file:

- `backend/app/services/transmission_engine.py`

Suggested responsibilities:

1. load company commodity profiles
2. build earnings impacts for an event
3. score V2 reactions
4. persist V2 outputs
5. fetch V2 detail for APIs

Integration point:

- call V2 rebuild/scoring from `analyze_event_text` after the existing V1 event and commodity impact rows are saved

Important:

- V2 failures must not break V1 event creation
- if V2 scoring fails, return normal V1 event detail as before

## Testing

Minimum coverage:

1. DB init creates new tables
2. Seeded profiles exist for oil/lithium/copper
3. Oil supply disruption event:
   - upstream oil names score as benefit
   - airline scores as harm
4. Lithium oversupply / price down event:
   - lithium miners score as harm
   - downstream battery exposure can score as benefit
5. Copper shortage / price up event:
   - upstream copper names score as benefit
6. New APIs return structured V2 data
7. Existing V1 commodity event APIs remain green

## Delivery constraints

1. Preserve current API compatibility
2. Prefer additive schema changes
3. Keep code and seeds readable, not over-generalized
4. Do not introduce network dependence in tests
