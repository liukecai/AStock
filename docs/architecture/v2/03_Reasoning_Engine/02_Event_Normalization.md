# 02 Event Normalization

> 本文档定义 AStock V2 中事件标准化设计。

---

## 1. Event Normalization 目标

Event Extraction 产出的是候选事件。

Event Normalization 负责把候选事件转化为可用于推理的标准结构。

标准化需要解决：

- 事件类型归一。
- 实体名称归一。
- 事件方向归一。
- 事件强度归一。
- 时间窗口归一。
- 重复事件合并。

---

## 2. 标准事件结构

标准事件至少包含：

```text
event_id
event_type
subtype
target_entity_ids
target_entity_names
impact_direction
role_direction
intensity
confidence
time_window
source_evidence_ids
status
created_at
updated_at
```

---

## 3. Event Type 归一

不同文本可能表达同一类事件。

示例：

```text
缺货
供应紧张
断供
限产
库存不足
```

统一为：

```text
supply_shortage
```

事件类型必须使用枚举，避免自由文本。

---

## 4. Entity 归一

事件中的目标实体必须映射到 Knowledge Graph Entity。

示例：

```text
WF6
Tungsten Hexafluoride
六氟化钨气体
```

统一为：

```text
entity: 六氟化钨
entity_type: Product
```

如果无法映射到现有实体，则创建 candidate entity。

---

## 5. Direction 标准化

事件方向包括两个层次：

### 5.1 impact_direction

表示事件对目标实体价格或供需的方向。

可选值：

```text
positive
negative
neutral
uncertain
```

### 5.2 role_direction

表示不同产业链角色的影响方向。

可选值：

```text
positive_for_supplier
negative_for_supplier
positive_for_buyer
negative_for_buyer
positive_for_substitute
negative_for_substitute
```

示例：

```text
六氟化钨供应紧张
```

可能表示：

```text
positive_for_supplier
negative_for_downstream_user
```

---

## 6. Intensity 标准化

事件强度标准值：

```text
low
medium
medium_high
high
critical
```

强度计算参考：

- 来源质量。
- 多源确认数量。
- 事件规模。
- 影响范围。
- 新闻热度。
- 是否有官方公告。

---

## 7. Time Window 标准化

事件影响窗口用于后续验证。

默认窗口：

```text
T+1
T+3
T+5
T+10
```

不同事件类型可配置不同窗口。

例如：

```text
price_increase: T+1 / T+3
policy_support: T+5 / T+10
capacity_expansion: T+10 / T+20
```

---

## 8. Event Deduplication

同一事件可能被多个来源重复报道。

去重依据：

```text
event_type
target_entity_ids
time_bucket
similar_title_hash
```

重复事件应合并 evidence，而不是创建多个事件。

---

## 9. Event Confidence

事件置信度由以下因素决定：

```text
extraction_confidence
source_confidence
multi_source_confirmation
entity_mapping_confidence
```

简化计算：

```text
event_confidence = extraction_confidence * 0.4
                 + source_confidence * 0.4
                 + confirmation_score * 0.2
```

---

## 10. Normalization 输出

标准化后事件示例：

```json
{
  "event_type": "supply_shortage",
  "target_entities": [
    {"entity_id": "ent_wf6", "name": "六氟化钨", "type": "Product"}
  ],
  "impact_direction": "positive",
  "role_direction": ["positive_for_supplier", "negative_for_downstream_user"],
  "intensity": "medium_high",
  "confidence": 0.81,
  "time_window": ["T+1", "T+3", "T+5"]
}
```

---

## 11. 不可推理事件

以下事件不应进入核心推理：

- 无明确目标实体。
- 抽取置信度过低。
- 来源质量过低且无多源确认。
- 与已有事件重复但无新增信息。
- 事件方向无法判断且不适合观察。

这些事件可以保留为 candidate，但不进入正式推理。

---

## 12. 设计原则

1. 事件类型必须枚举化。
2. 目标实体必须映射到图谱实体。
3. 事件方向与股票涨跌判断分离。
4. 同一事件多源报道应合并。
5. 标准化事件必须可用于验证。
6. 低质量事件不能直接触发股票推荐。

---

## 13. 结论

Event Normalization 是事件从文本走向推理的关键步骤。

只有事件类型、目标实体、方向、强度和时间窗口都标准化后，Reasoning Engine 才能稳定工作。