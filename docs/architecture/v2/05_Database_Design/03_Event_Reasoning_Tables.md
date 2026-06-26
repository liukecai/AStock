# 03 Event Reasoning Tables

> 本文档定义 AStock V2 事件推理相关数据库表。

---

## 1. 表设计目标

Event Reasoning Tables 用于保存：

- 标准化事件。
- 事件影响实体。
- 推理路径。
- 股票暴露度。
- 股票事件评分。

这些表用于支持事件看板、个股解释、路径展示和后续验证。

---

## 2. event_instances

事件实例表。

```text
event_instances
```

建议字段：

```text
id
event_id
event_type
subtype
title
summary
target_entities_json
impact_direction
role_direction_json
intensity
confidence
source_evidence_ids_json
occurred_at
status
created_at
updated_at
```

status：

```text
candidate
active
rejected
duplicate
expired
validated
```

---

## 3. event_impacts

事件影响实体表。

```text
event_impacts
```

建议字段：

```text
id
event_id
entity_id
entity_type
impact_direction
impact_weight
confidence
path_from_event_json
created_at
updated_at
```

该表保存事件初始影响和扩散后的中间实体。

---

## 4. reasoning_paths

推理路径表。

```text
reasoning_paths
```

建议字段：

```text
id
path_id
event_id
stock_code
start_entity_id
end_entity_id
nodes_json
edges_json
path_depth
path_score
confidence
created_at
```

nodes_json 保存路径节点。

edges_json 保存关系、权重、置信度和 evidence_ids。

---

## 5. stock_exposures

股票暴露度表。

```text
stock_exposures
```

建议字段：

```text
id
event_id
stock_code
stock_name
entity_id
exposure_score
confidence
primary_path_id
reason_paths_json
score_breakdown_json
status
created_at
updated_at
```

exposure_score 取值范围建议为 0 到 1。

---

## 6. stock_event_scores

股票事件综合评分表。

```text
stock_event_scores
```

建议字段：

```text
id
event_id
stock_code
final_score
rank
label
event_score
exposure_score
trend_score
sentiment_score
volume_score
validation_score
confidence
score_breakdown_json
created_at
updated_at
```

final_score 建议使用 0 到 100。

---

## 7. event_source_links

事件来源绑定表。

```text
event_source_links
```

建议字段：

```text
id
event_id
evidence_id
source_role
created_at
```

source_role：

```text
primary
supporting
duplicate
contradictory
```

---

## 8. path_evidence_cache

路径证据缓存表。

```text
path_evidence_cache
```

建议字段：

```text
id
path_id
evidence_ids_json
evidence_summary
created_at
updated_at
```

用于加速前端 Why This Stock 页面。

---

## 9. 数据写入流程

```text
Event Normalization
  ↓
event_instances
  ↓
Reasoning Engine
  ↓
event_impacts / reasoning_paths
  ↓
Exposure Engine
  ↓
stock_exposures
  ↓
Scoring Engine
  ↓
stock_event_scores
```

---

## 10. 查询场景

### 10.1 事件详情页

读取：

```text
event_instances
event_impacts
stock_event_scores
reasoning_paths
```

### 10.2 个股解释页

读取：

```text
stock_exposures
reasoning_paths
path_evidence_cache
```

### 10.3 验证任务

读取：

```text
event_instances
stock_event_scores
stock_exposures
```

---

## 11. 设计原则

1. 事件实例必须标准化后入库。
2. 推理路径必须保存完整节点和边。
3. 股票暴露度与综合评分分离。
4. 分数必须保存 breakdown。
5. 事件来源必须可追溯。
6. 路径证据可以缓存以提升前端性能。

---

## 12. 结论

Event Reasoning Tables 是 V2 事件推理结果的落地层。

它们让系统不仅能计算候选股票，还能解释路径、展示分数、支持验证。