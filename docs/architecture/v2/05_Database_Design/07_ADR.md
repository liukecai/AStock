# 07 ADR

> 本文档记录 AStock V2 Database Design 阶段的关键架构决策。

---

## ADR-001：第一阶段继续支持 SQLite

### 状态

Accepted

### 背景

AStock 当前更适合快速迭代和单机部署。

直接引入 PostgreSQL 会增加部署复杂度。

### 决策

V2 第一阶段继续支持 SQLite，但所有表设计必须兼容 PostgreSQL。

### 影响

优点：

- 部署简单。
- 开发速度快。
- 适合 MVP。

代价：

- 并发写入能力有限。
- 大数据量后需要迁移。

---

## ADR-002：使用 SQLAlchemy 隔离数据库差异

### 状态

Accepted

### 背景

系统后续需要从 SQLite 迁移到 PostgreSQL。

### 决策

数据库访问统一使用 SQLAlchemy ORM 或 SQLAlchemy Core。

### 影响

优点：

- 降低迁移成本。
- 表结构统一管理。
- 便于引入 Alembic。

代价：

- 需要遵守 ORM 模型规范。

---

## ADR-003：Evidence 独立建表并长期保留

### 状态

Accepted

### 背景

图谱关系如果没有证据来源，无法审计和解释。

### 决策

Evidence 独立建表，relation_evidence 用于绑定关系和证据。

### 影响

优点：

- 关系可追溯。
- 前端可展示证据。
- 支持多来源合并。

代价：

- 存储量增加。
- 查询路径更复杂。

---

## ADR-004：Candidate 与正式图谱分表

### 状态

Accepted

### 背景

LLM 和低质量来源可能生成错误关系。

### 决策

候选实体和候选关系分别进入 candidate_entities 和 candidate_relations。

正式图谱只使用 kg_entities 和 kg_relations。

### 影响

优点：

- 隔离噪音。
- 支持审核。
- 支持回滚。

代价：

- 数据流更长。
- 需要审核流程。

---

## ADR-005：推理路径必须落库

### 状态

Accepted

### 背景

如果只保存候选股票和分数，无法解释股票为什么相关。

### 决策

使用 reasoning_paths 保存完整路径。

### 影响

优点：

- 支持 Why This Stock。
- 支持路径级验证。
- 支持人工复核。

代价：

- 存储结构更复杂。
- 需要保存 nodes_json 和 edges_json。

---

## ADR-006：评分必须保存 breakdown

### 状态

Accepted

### 背景

单一 final_score 无法解释分数来源。

### 决策

stock_event_scores 必须保存各子因子和 score_breakdown_json。

### 影响

优点：

- 前端可解释。
- 便于调参。
- 便于复盘。

代价：

- 表字段更多。

---

## ADR-007：Validation 结果单独建表

### 状态

Accepted

### 背景

历史验证是 V2 校准权重和识别噪音的重要能力。

### 决策

使用 event_validation_results 和 validation_summary 保存验证结果。

### 影响

优点：

- 支持事件级复盘。
- 支持路径级统计。
- 支持权重回写。

代价：

- 需要行情数据完整性。
- 需要处理非交易日、停牌、缺失数据。

---

## ADR-008：JSON 字段先以 TEXT 兼容，后续迁移 JSONB

### 状态

Accepted

### 背景

SQLite 对 JSON 支持有限，PostgreSQL 支持 JSONB。

### 决策

第一阶段 JSON 字段以 TEXT 存储 JSON 字符串。

迁移 PostgreSQL 后可升级为 JSONB。

### 影响

优点：

- 兼容 SQLite。
- 迁移路径清晰。

代价：

- SQLite 阶段 JSON 查询能力有限。

---

## 结论

Database Design 阶段的核心决策是：

```text
SQLite 先行
SQLAlchemy 抽象
Evidence 独立
Candidate 隔离
Reasoning Path 落库
Score Breakdown 落库
Validation 独立聚合
```

这些决策保证 V2 能快速落地，同时具备长期迁移和扩展能力。