# 00 Overview

> 本文档定义 AStock V2 数据库设计总体原则。

---

## 1. 数据库在 V2 中的定位

AStock V2 的数据库不只是行情缓存，也不是简单业务表集合。

它需要承载：

```text
Evidence
Knowledge Graph
Reasoning Result
Scoring Result
Validation Result
Audit Log
```

数据库是 V2 从事件抽取到图谱推理再到市场验证的中枢。

---

## 2. 总体分层

V2 数据库按领域分为六层：

```text
Core Layer
Evidence Layer
Candidate Layer
Knowledge Graph Layer
Reasoning Layer
Validation Layer
```

每一层职责不同。

---

## 3. Core Layer

Core Layer 保存基础对象：

- 股票。
- 公司。
- 数据源。
- 任务运行记录。
- 系统配置。

这些数据被其他模块复用。

---

## 4. Evidence Layer

Evidence Layer 保存可追溯证据。

包括：

- 年报。
- 招股书。
- 公告。
- 官网文本。
- 新闻。
- RSS。
- 互动易回复。

Evidence 是所有图谱关系和推理解释的可信基础。

---

## 5. Candidate Layer

Candidate Layer 保存机器抽取或低置信来源生成的候选知识。

包括：

- candidate_entities。
- candidate_relations。
- candidate_events。

候选层隔离 LLM 和低质量来源风险。

---

## 6. Knowledge Graph Layer

Knowledge Graph Layer 保存正式实体和正式关系。

包括：

- kg_entities。
- kg_relations。
- relation_evidence。
- kg_change_logs。

正式图谱只保存经过审核、校验或高置信自动通过的关系。

---

## 7. Reasoning Layer

Reasoning Layer 保存事件推理结果。

包括：

- event_instances。
- event_impacts。
- reasoning_paths。
- stock_exposures。
- stock_event_scores。

这些表用于支持前端 Why This Stock、事件影响路径和候选股票列表。

---

## 8. Validation Layer

Validation Layer 保存市场验证结果。

包括：

- event_validation_results。
- validation_summary。

这些结果用于校准事件类型、路径和股票响应权重。

---

## 9. SQLite 与 PostgreSQL

V2 第一阶段可以继续使用 SQLite。

但所有表设计应避免 SQLite 专有特性。

后续可迁移到 PostgreSQL，以支持：

- 更好的并发写入。
- 更复杂索引。
- 更稳定备份。
- 后续 pgvector。
- 更大规模数据。

---

## 10. 数据库设计原则

1. 表结构按领域分层。
2. 原始证据长期保留。
3. 候选层和正式层分离。
4. 事实关系和交易验证分离。
5. 所有推理结果保存路径。
6. 所有评分结果保存 breakdown。
7. 所有自动化写入必须可审计。

---

## 11. 结论

AStock V2 的数据库设计核心是：

```text
可追溯证据
可维护图谱
可解释推理
可验证结果
可审计更新
```

这套数据库结构决定 V2 是否能长期演进。