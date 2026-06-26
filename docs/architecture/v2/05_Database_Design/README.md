# 05 Database Design

> 本目录定义 AStock V2 的数据库设计。
>
> 数据库设计目标是支撑 Evidence、Knowledge Graph、Reasoning Engine、Validation Loop 与 Web Explainability。

---

## 文档范围

```text
05_Database_Design/
├── README.md
├── 00_Overview.md
├── 01_Core_Tables.md
├── 02_Knowledge_Graph_Tables.md
├── 03_Event_Reasoning_Tables.md
├── 04_Validation_Tables.md
├── 05_Migration_Strategy.md
├── 06_Indexing_Performance.md
└── 07_ADR.md
```

---

## 阅读顺序

1. `00_Overview.md`：理解 V2 数据库总体设计。
2. `01_Core_Tables.md`：理解基础表和通用字段。
3. `02_Knowledge_Graph_Tables.md`：理解图谱相关表。
4. `03_Event_Reasoning_Tables.md`：理解事件推理相关表。
5. `04_Validation_Tables.md`：理解验证闭环相关表。
6. `05_Migration_Strategy.md`：理解 SQLite 到 PostgreSQL 的迁移策略。
7. `06_Indexing_Performance.md`：理解索引和性能设计。
8. `07_ADR.md`：理解数据库设计关键决策。

---

## 数据库设计目标

V2 数据库需要支持：

- 原始证据存储。
- 候选实体与候选关系。
- 正式知识图谱。
- 事件实例。
- 推理路径。
- 股票暴露度。
- 综合评分。
- 历史验证。
- 任务状态。
- 审计日志。

---

## 核心表组

```text
Core Tables
  ↓
stocks
companies
data_sources
job_runs

Evidence Tables
  ↓
evidence
evidence_chunks

Knowledge Graph Tables
  ↓
kg_entities
kg_relations
relation_evidence
candidate_entities
candidate_relations

Reasoning Tables
  ↓
event_instances
event_impacts
reasoning_paths
stock_exposures
stock_event_scores

Validation Tables
  ↓
event_validation_results
validation_summary

Audit Tables
  ↓
kg_change_logs
review_logs
```

---

## 数据库设计原则

1. Evidence 必须可追溯。
2. Candidate 与 Active 数据分离。
3. Confidence 与 Weight 分离。
4. 推理路径必须落库。
5. 分数必须保存 breakdown。
6. 验证结果必须可聚合。
7. 第一阶段兼容 SQLite。
8. 第二阶段平滑迁移 PostgreSQL。

---

## 与其他模块关系

```text
Evidence Collector -> evidence
LLM Extraction -> candidate_entities / candidate_relations
Knowledge Graph Service -> kg_entities / kg_relations
Reasoning Engine -> reasoning_paths / stock_exposures
Scoring Engine -> stock_event_scores
Validation Engine -> event_validation_results
Web API -> read optimized DTO
```

数据库是 V2 所有模块之间的稳定契约。