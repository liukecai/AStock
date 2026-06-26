# 00 Overview

> 本文档定义 AStock V2 的总体实施路线。

---

## 1. Roadmap 目标

AStock V2 不是一次性重写系统，而是在 V1 基础上逐步增加：

```text
Evidence Layer
Knowledge Graph
Reasoning Engine
Validation Loop
Explainable Web
```

Roadmap 的目标是降低重构风险，让每一步都有可运行成果。

---

## 2. 总体阶段

```text
Phase 1：KG Schema 与基础表
Phase 2：YAML 规则迁移到图谱
Phase 3：Reasoning Engine MVP
Phase 4：LLM 抽取候选关系
Phase 5：Validation Loop 验证闭环
Phase 6：Web Explainability 前端解释层
```

---

## 3. 阶段依赖

```text
Phase 1
  ↓
Phase 2
  ↓
Phase 3
  ↓
Phase 5
  ↓
Phase 6
```

Phase 4 可以在 Phase 2 之后并行启动，但 LLM 输出必须先进候选层。

---

## 4. 推荐节奏

```text
Sprint 1：数据库 schema 与 seed 数据
Sprint 2：YAML loader 与图谱查询
Sprint 3：事件推理 MVP
Sprint 4：候选关系与 LLM 抽取
Sprint 5：验证闭环
Sprint 6：前端解释页面
```

---

## 5. 优先级

最高优先级：

```text
kg_entities
kg_relations
relation_evidence
reasoning_paths
stock_exposures
```

中优先级：

```text
candidate_relations
validation_results
web explanation components
```

后续优先级：

```text
Neo4j
pgvector
GraphRAG
Agent 自动维护
```

---

## 6. 验收原则

每个 Phase 必须回答：

```text
新增了什么能力？
能否通过一个真实案例演示？
是否不破坏 V1？
是否可回滚？
是否有数据可观察？
```

---

## 7. 第一条验证用例

推荐使用：

```text
六氟化钨供应紧张 -> 中船特气 / 钨产业链
```

作为 V2 MVP 贯穿案例。

原因：

- 事件清晰。
- 商品实体明确。
- 图谱路径短。
- 公司关系可证据化。
- 适合验证供应链推理。

---

## 8. 结论

V2 实施路线应遵循：

```text
先建模
再迁移
再推理
再抽取
再验证
再展示
```

这样可以保证架构逐步落地，而不是停留在文档层。