# 03 JSON Schema

> 本文档定义 AStock V2 中 LLM 输出 JSON Schema 的设计规范。

---

## 1. JSON Schema 目标

LLM 输出必须结构化，便于：

- 自动校验。
- 自动入库。
- 自动审核。
- 追踪 evidence。
- 生成 candidate relations。

禁止依赖自然语言解析 LLM 输出。

---

## 2. 通用输出结构

所有 LLM 抽取任务应使用统一外层结构：

```json
{
  "task_name": "annual_report_extraction",
  "task_version": "v1.0",
  "source_evidence_id": "evi_001",
  "language": "zh-CN",
  "entities": [],
  "relations": [],
  "events": [],
  "warnings": []
}
```

---

## 3. Entity Schema

实体结构：

```json
{
  "name": "六氟化钨",
  "entity_type": "Product",
  "canonical_name": "六氟化钨",
  "aliases": ["WF6", "Tungsten Hexafluoride"],
  "description": "电子特气产品",
  "evidence_text": "公司主要产品包括六氟化钨...",
  "confidence": 0.88
}
```

必填字段：

```text
name
entity_type
evidence_text
confidence
```

---

## 4. Relation Schema

关系结构：

```json
{
  "subject": "中船特气",
  "subject_type": "Company",
  "predicate": "produces",
  "object": "六氟化钨",
  "object_type": "Product",
  "evidence_text": "公司主要产品包括六氟化钨...",
  "confidence": 0.9,
  "support_type": "direct"
}
```

必填字段：

```text
subject
subject_type
predicate
object
object_type
evidence_text
confidence
support_type
```

---

## 5. Event Schema

事件结构：

```json
{
  "event_type": "supply_shortage",
  "subtype": "product_shortage",
  "target_entities": ["六氟化钨"],
  "trigger_words": ["供应紧张", "紧缺"],
  "impact_direction": "positive",
  "role_direction": ["positive_for_supplier", "negative_for_downstream_user"],
  "intensity": "medium_high",
  "evidence_text": "市场传出六氟化钨供应紧张...",
  "confidence": 0.78
}
```

必填字段：

```text
event_type
target_entities
trigger_words
evidence_text
confidence
```

---

## 6. Warning Schema

warnings 用于记录不确定性。

```json
{
  "type": "low_confidence",
  "message": "原文只间接提到该产品，建议人工审核。",
  "related_text": "相关片段"
}
```

warnings 不应导致任务失败，但应进入审核提示。

---

## 7. Entity Type 枚举

允许值：

```text
Company
Stock
Product
Material
Commodity
Industry
Sector
Concept
EventType
EventInstance
Project
Technology
Customer
Supplier
Evidence
```

不允许 LLM 自由创造 entity_type。

---

## 8. Predicate 枚举

允许值：

```text
listed_as
produces
supplies
uses
belongs_to
upstream_of
downstream_of
used_in
impacts
benefits
hurts
exposed_to
evidenced_by
aliases
plans
expands_capacity
wins_contract
has_risk
```

不允许 LLM 自由创造 predicate。

---

## 9. Confidence 类型

confidence 必须是 0 到 1 之间的小数。

不允许输出：

```text
高
中
低
可能
很确定
```

---

## 10. evidence_text 要求

每个 entity、relation、event 都必须包含 evidence_text。

如果 evidence_text 为空，该条结果应被丢弃或进入 rejected 状态。

---

## 11. JSON 校验

入库前必须校验：

- JSON 是否可解析。
- 必填字段是否存在。
- 枚举值是否合法。
- confidence 是否在范围内。
- evidence_text 是否非空。
- subject/object 是否为空。

---

## 12. 错误处理

LLM 输出不合法时：

1. 记录原始输出。
2. 标记任务 failed_validation。
3. 不写入 candidate 表。
4. 可选择重试一次。

---

## 13. 设计原则

1. 所有输出必须 JSON。
2. 枚举值必须受控。
3. evidence_text 必须存在。
4. confidence 必须数值化。
5. 不合法输出不得入库。
6. Schema 必须版本化。

---

## 14. 结论

JSON Schema 是 LLM Integration 的安全边界。

只有结构稳定、字段受控、证据明确的输出，才能进入 AStock V2 的候选知识层。