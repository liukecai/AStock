# 05 Database Design

> AStock V2 数据库设计。
>
> 支撑 Evidence、Knowledge Graph、Reasoning Engine、Validation Loop 与 Web Explainability 的数据存储。
>
> 前置阅读：[02_Knowledge_Graph_Design.md](./02_Knowledge_Graph_Design.md)（实体/关系/证据模型）、[03_Reasoning_Engine.md](./03_Reasoning_Engine.md)（推理/暴露度/评分/验证数据结构）。

---

## 1. 总体设计

### 1.1 设计目标

V2 数据库需要支持：原始证据存储、候选与正式知识图谱、事件实例、推理路径、股票暴露度、综合评分、历史验证、任务状态和审计日志。

### 1.2 核心表组

```text
Core Tables          → stocks / companies / data_sources / job_runs
Evidence Tables      → evidence / evidence_chunks
KG Tables            → kg_entities / kg_relations / relation_evidence / candidate_entities / candidate_relations
Reasoning Tables     → event_instances / event_impacts / reasoning_paths / stock_exposures / stock_event_scores
Validation Tables    → event_validation_results / validation_summary
Audit Tables         → kg_change_logs / review_logs
```

### 1.3 与上游模块关系

```text
Evidence Collector     → evidence
LLM Extraction         → candidate_entities / candidate_relations
KG Service             → kg_entities / kg_relations
Reasoning Engine       → reasoning_paths / stock_exposures
Scoring Engine         → stock_event_scores
Validation Engine      → event_validation_results
Web API                → read optimized DTO
```

---

## 2. Core Tables

### stocks

| 字段 | 类型 | 说明 |
|---|---|---|
| stock_code | TEXT PK | 股票代码 |
| stock_name | TEXT | 股票名称 |
| exchange | TEXT | 交易所 |
| list_date | TEXT | 上市日期 |
| industry | TEXT | 所属行业 |
| company_entity_id | TEXT FK | 关联 kg_entities |

### companies

| 字段 | 类型 | 说明 |
|---|---|---|
| company_id | TEXT PK | 公司 ID |
| company_name | TEXT | 公司名称 |
| legal_name | TEXT | 法定名称 |
| short_name | TEXT | 简称 |
| website | TEXT | 官网 |
| entity_id | TEXT FK | 关联 kg_entities |

### job_runs

| 字段 | 类型 | 说明 |
|---|---|---|
| job_id | TEXT PK | 任务 ID |
| job_name | TEXT | 任务名称 |
| started_at / finished_at | DATETIME | 开始/结束时间 |
| status | TEXT | pending / running / success / failed / partial_success |
| error_message | TEXT | 错误信息 |
| processed_count | INTEGER | 处理数量 |
| summary | TEXT | 摘要 |

---

## 3. Knowledge Graph Tables

### kg_entities

| 字段 | 类型 | 说明 |
|---|---|---|
| entity_id | TEXT PK | 全局唯一 |
| entity_type | TEXT | Company / Stock / Product / Material / Commodity / Industry / Sector / Concept / EventType / EventInstance / Evidence |
| name | TEXT | 展示名称 |
| canonical_name | TEXT | 归一化名称 |
| aliases_json | TEXT | 别名列表 JSON |
| description | TEXT | 简要说明 |
| metadata_json | TEXT | 扩展属性 |
| status | TEXT | active / inactive / candidate / rejected / merged |
| merged_into_id | TEXT | 合并目标实体 |
| created_at / updated_at | DATETIME | 时间戳 |

### kg_relations

| 字段 | 类型 | 说明 |
|---|---|---|
| relation_id | TEXT PK | 全局唯一 |
| source_entity_id | TEXT FK | 起点实体 |
| target_entity_id | TEXT FK | 终点实体 |
| relation_type | TEXT | produces / belongs_to / uses / used_in / impacts / ... |
| direction | TEXT | directed |
| weight | REAL | 推理权重 0.0~1.0 |
| confidence | REAL | 置信度 0.0~1.0 |
| source_type | TEXT | 关系来源类型 |
| status | TEXT | candidate / active / rejected / deprecated / validated / needs_review |
| created_at / updated_at | DATETIME | 时间戳 |

**唯一约束**：`UNIQUE(source_entity_id, relation_type, target_entity_id)`

### evidence

| 字段 | 类型 | 说明 |
|---|---|---|
| evidence_id | TEXT PK | 证据唯一 ID |
| source_type | TEXT | annual_report / prospectus / announcement / news / yaml_seed / llm_extraction / ... |
| source_name / source_url | TEXT | 来源名称和链接 |
| title / raw_text | TEXT | 标题和原文 |
| published_at / collected_at | DATETIME | 发布/采集时间 |
| related_company / related_stock_code | TEXT | 相关公司和股票 |
| source_confidence | REAL | 来源基础可信度 |
| content_hash | TEXT UNIQUE | 去重 hash |
| status | TEXT | active / archived / rejected |

### relation_evidence

| 字段 | 类型 | 说明 |
|---|---|---|
| relation_id | TEXT FK | 关系 ID |
| evidence_id | TEXT FK | 证据 ID |
| support_type | TEXT | direct / indirect / weak / contradictory |
| extracted_text | TEXT | 证据片段 |
| confidence_delta | REAL | 该证据对置信度的贡献 |
| created_at | DATETIME | — |

### candidate_entities / candidate_relations

结构与 `kg_entities` / `kg_relations` 类似，增加：

| 字段 | 说明 |
|---|---|
| extractor_type | rule / llm / manual |
| prompt_version | LLM prompt 版本 |
| review_status | pending / approved / rejected / needs_more_evidence |
| reviewer / reviewed_at | 审核人和时间 |

---

## 4. Event & Reasoning Tables

### event_instances

| 字段 | 类型 | 说明 |
|---|---|---|
| event_id | TEXT PK | 事件 ID |
| event_type | TEXT | 事件类型 |
| subtype | TEXT | 子类型 |
| title | TEXT | 事件标题 |
| description | TEXT | 事件描述 |
| entities_json | TEXT | 涉及实体列表 |
| intensity | TEXT | 强度 |
| direction | TEXT | 影响方向 |
| time_window | TEXT | 预期影响窗口 |
| source_evidence_id | TEXT FK | 来源证据 |
| occurred_at | DATETIME | 事件发生时间 |
| created_at | DATETIME | — |

### event_impacts

| 字段 | 类型 | 说明 |
|---|---|---|
| impact_id | TEXT PK | — |
| event_id | TEXT FK | 事件 ID |
| entity_id | TEXT FK | 受影响实体 |
| impact_type | TEXT | direct / indirect |
| impact_score | REAL | 影响强度 |

### reasoning_paths

| 字段 | 类型 | 说明 |
|---|---|---|
| path_id | TEXT PK | — |
| event_id | TEXT FK | 事件 ID |
| stock_code | TEXT | 候选股票 |
| start_entity_id / end_entity_id | TEXT | 路径起终点 |
| nodes_json | TEXT | 路径节点列表 |
| edges_json | TEXT | 路径边列表（含 relation_type / weight / confidence） |
| path_score | REAL | 路径综合分数 |
| path_length | INTEGER | 路径跳数 |
| created_at | DATETIME | — |

### stock_exposures

| 字段 | 类型 | 说明 |
|---|---|---|
| event_id | TEXT FK | 事件 ID |
| stock_code | TEXT | 股票代码 |
| entity_id | TEXT FK | 暴露实体 |
| exposure_score | REAL | 暴露度 |
| confidence | REAL | 置信度 |
| reason_path_id | TEXT FK | 关联推理路径 |

### stock_event_scores

| 字段 | 类型 | 说明 |
|---|---|---|
| event_id | TEXT FK | — |
| stock_code | TEXT | — |
| final_score | REAL | 最终分数 |
| exposure_score / trend_score / sentiment_score / volume_score / event_intensity / validation_score | REAL | 各子因子 |
| score_breakdown_json | TEXT | 分数拆解 JSON |
| confidence | REAL | 整体置信度 |
| rank | INTEGER | 排名 |
| label | TEXT | 分档标签 |
| created_at | DATETIME | — |

---

## 5. Validation Tables

### event_validation_results

| 字段 | 类型 | 说明 |
|---|---|---|
| validation_id | TEXT PK | — |
| event_id | TEXT FK | 事件 ID |
| stock_code | TEXT | 股票代码 |
| path_id | TEXT FK | 推理路径 |
| window | TEXT | T+1 / T+3 / T+5 / T+10 |
| t0_date / end_date | DATE | 起止日期 |
| absolute_return | REAL | 绝对收益 |
| benchmark_return / industry_return | REAL | 基准/行业收益 |
| excess_return_index / excess_return_industry | REAL | 超额收益 |
| max_gain / max_drawdown | REAL | 窗口内最大涨幅/回撤 |
| hit | BOOLEAN | 是否命中 |
| status | TEXT | calculated / pending / missing_data / suspended |
| calculated_at | DATETIME | — |

### validation_summary

| 字段 | 类型 | 说明 |
|---|---|---|
| summary_id | TEXT PK | — |
| summary_type | TEXT | event_type / entity / path / stock |
| summary_key | TEXT | 聚合键 |
| window | TEXT | 时间窗口 |
| sample_count | INTEGER | 样本数 |
| hit_rate | REAL | 胜率 |
| avg_excess_return | REAL | 平均超额收益 |
| weight_adjustment | REAL | 权重调整建议 |
| updated_at | DATETIME | — |

---

## 6. Audit Tables

### kg_change_logs

| 字段 | 说明 |
|---|---|
| operation_type | entity_upsert / relation_upsert / confidence_update / weight_update / status_update / alias_merge |
| entity_id / relation_id | 操作对象 |
| old_value / new_value | 变更内容 |
| reason | 变更原因 |
| operator | system / llm_extractor / yaml_loader / manual_admin / validation_engine |
| created_at | — |

---

## 7. 迁移策略

### 7.1 SQLite → PostgreSQL

| 项目 | 策略 |
|---|---|
| ORM | 统一使用 SQLAlchemy，避免 SQLite 专有语法 |
| Migration | 使用 Alembic 管理迁移脚本 |
| JSON 字段 | 第一阶段 TEXT 存 JSON 字符串，迁移后升级 JSONB |
| 时机 | 并发写入需求增加或数据量超过 SQLite 承受能力时 |

### 7.2 SQLite 注意事项

- 避免多 worker 并发写入，写任务尽量串行。
- 大批量写入使用事务。
- 定期备份。
- 控制单表无限增长。

---

## 8. 索引设计

### 核心索引

| 表 | 索引字段 |
|---|---|
| kg_entities | canonical_name, entity_type, status |
| kg_relations | source_entity_id, target_entity_id, relation_type, status |
| relation_evidence | relation_id |
| evidence | content_hash, source_type, related_stock_code |
| candidate_relations | review_status, extractor_type |
| event_instances | event_type, occurred_at |
| reasoning_paths | event_id, stock_code, path_score |
| stock_exposures | event_id, stock_code |
| stock_event_scores | event_id, stock_code, final_score, rank |
| event_validation_results | event_id, stock_code, window |
| validation_summary | summary_type, summary_key, window |

### 缓存策略

可缓存：个股知识卡、热门实体邻居、事件推理路径、Why This Stock 解释、验证聚合统计。

缓存失效条件：kg_relations 更新、evidence 更新、stock_event_scores 更新、validation_summary 更新。

---

## 9. 架构决策记录（ADR）

### ADR-001：第一阶段继续支持 SQLite

部署简单，开发速度快，适合 MVP。所有表设计兼容 PostgreSQL。

### ADR-002：使用 SQLAlchemy 隔离数据库差异

降低迁移成本，表结构统一管理，便于引入 Alembic。

### ADR-003：Evidence 独立建表并长期保留

关系可追溯，前端可展示证据，支持多来源合并。

### ADR-004：Candidate 与正式图谱分表

隔离噪音，支持审核和回滚。候选实体/关系进入 `candidate_*` 表，正式图谱使用 `kg_*` 表。

### ADR-005：推理路径必须落库

`reasoning_paths` 保存完整路径（`nodes_json` / `edges_json`），支持 Why This Stock、路径级验证和人工复核。

### ADR-006：评分必须保存 breakdown

`stock_event_scores` 保存各子因子和 `score_breakdown_json`，便于前端解释、调参和复盘。

### ADR-007：Validation 结果单独建表

`event_validation_results` + `validation_summary` 支持事件级复盘、路径级统计和权重回写。

### ADR-008：JSON 字段先以 TEXT 兼容，后续迁移 JSONB

兼容 SQLite，迁移 PostgreSQL 后升级。
