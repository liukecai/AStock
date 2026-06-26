# 03 Stock Explain API

> 本文档定义解释类接口。该接口用于展示研究系统中的关联原因、路径、证据和分数拆解。

---

## 1. 目标

该接口回答：

```text
某个标的为什么与某个事件存在关联？
```

输出内容用于研究分析和系统解释。

---

## 2. API 分组

统一前缀：

```text
/api/v2/stocks
```

主要接口：

```text
GET /stocks/{stock_code}/knowledge
GET /stocks/{stock_code}/events
GET /stocks/{stock_code}/exposures
GET /stocks/{stock_code}/explain
GET /stocks/{stock_code}/evidence
```

---

## 3. knowledge

返回标的知识卡：

```text
stock_code
stock_name
company
products
materials
industries
concepts
key_relations
evidence_summary
last_updated_at
```

---

## 4. events

返回相关事件：

```text
event_id
event_type
title
occurred_at
final_score
exposure_score
confidence
label
```

---

## 5. exposures

返回实体暴露度：

```text
entity_id
entity_name
entity_type
exposure_score
confidence
primary_relation
primary_evidence
```

---

## 6. explain

请求参数：

```text
event_id
```

返回：

```text
stock_code
stock_name
event
final_score
confidence
score_breakdown
reason_paths
evidence_list
explanation_text
validation_summary
```

---

## 7. evidence

返回证据列表：

```text
evidence_id
source_type
title
source_url
published_at
extracted_text
related_relation
```

---

## 8. DTO 要求

解释 DTO 必须包含：

```text
event
score_breakdown
reason_paths
evidence_list
validation_summary
```

reason_paths 必须包含：

```text
path_id
nodes
edges
path_score
confidence
primary_evidence_ids
```

score_breakdown 至少包含：

```text
event_score
exposure_score
trend_score
sentiment_score
volume_score
validation_score
```

---

## 9. 设计原则

1. 返回路径，不只返回文本。
2. 解释文本只能基于已有路径和证据生成。
3. 证据必须可追溯。
4. 分数必须可拆解。
5. 低 confidence 必须明确返回。
6. 接口不输出操作建议。

---

## 10. 结论

Stock Explain API 是 V2 可解释能力的核心接口。