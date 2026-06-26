# 02 Event API

> 本文档定义 AStock V2 的事件 API。

---

## 1. Event API 目标

Event API 用于支持：

- 事件列表。
- 事件详情。
- 事件影响实体。
- 事件推理路径。
- 事件相关股票。
- 事件评分结果。

Event API 是 Event Dashboard 的核心数据来源。

---

## 2. API 分组

统一前缀：

```text
/api/v2/events
```

主要接口：

```text
GET /events
GET /events/{event_id}
GET /events/{event_id}/impacts
GET /events/{event_id}/paths
GET /events/{event_id}/stocks
POST /events/reason
```

---

## 3. GET /events

查询事件列表。

参数：

```text
event_type
status
start_date
end_date
min_confidence
keyword
page
page_size
```

返回字段：

```text
event_id
event_type
title
summary
intensity
confidence
occurred_at
status
candidate_stock_count
```

---

## 4. GET /events/{event_id}

查询事件详情。

返回：

```text
event_id
event_type
subtype
title
summary
target_entities
impact_direction
role_direction
intensity
confidence
source_evidence
occurred_at
status
```

用途：

- 事件详情页。
- 推理结果入口。
- 验证面板入口。

---

## 5. GET /events/{event_id}/impacts

查询事件影响实体。

返回：

```text
entity_id
entity_name
entity_type
impact_direction
impact_weight
confidence
path_from_event
```

用途：

- 展示事件影响到哪些商品、材料、行业。

---

## 6. GET /events/{event_id}/paths

查询事件推理路径。

参数：

```text
stock_code
min_path_score
limit
```

返回：

```text
path_id
stock_code
nodes
edges
path_depth
path_score
confidence
evidence_summary
```

用途：

- Event Impact Path。
- Why This Stock。

---

## 7. GET /events/{event_id}/stocks

查询事件相关股票。

参数：

```text
min_score
min_confidence
label
page
page_size
```

返回：

```text
stock_code
stock_name
rank
final_score
exposure_score
trend_score
sentiment_score
validation_score
confidence
label
primary_reason_path
```

该接口是事件候选股票列表的主要数据源。

---

## 8. POST /events/reason

临时事件推理接口。

请求体：

```json
{
  "text": "市场传出六氟化钨供应紧张",
  "max_depth": 4,
  "dry_run": true
}
```

返回：

```text
normalized_event
impacted_entities
candidate_stocks
reason_paths
```

说明：

- 该接口用于手工输入事件进行轻量推理。
- 不应执行长文本 LLM 抽取。
- dry_run 默认 true，不写入正式事件表。

---

## 9. Event DTO

标准 Event DTO：

```json
{
  "event_id": "evt_001",
  "event_type": "supply_shortage",
  "title": "六氟化钨供应紧张",
  "target_entities": [],
  "intensity": "medium_high",
  "confidence": 0.81,
  "occurred_at": "2026-06-27T00:00:00",
  "status": "active"
}
```

---

## 10. 设计原则

1. 事件列表必须分页。
2. 事件详情必须包含来源证据。
3. 股票列表必须包含 score_breakdown 关键字段。
4. 路径接口必须返回节点和边。
5. 临时推理接口不应默认写库。
6. 事件 API 不直接采集新闻。

---

## 11. 结论

Event API 是 V2 事件驱动体验的核心。

它把事件、产业影响路径、候选股票和评分结果组织成前端可直接展示的数据结构。