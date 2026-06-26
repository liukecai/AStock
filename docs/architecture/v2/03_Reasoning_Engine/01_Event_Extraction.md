# 01 Event Extraction

> 本文档定义 AStock V2 中事件抽取的设计。

---

## 1. Event Extraction 目标

Event Extraction 的目标是将非结构化文本转化为可推理的事件候选。

输入可能是：

- 新闻标题。
- 新闻正文。
- 公告标题。
- 公告摘要。
- RSS 条目。
- 用户手动输入文本。

输出是结构化事件候选。

---

## 2. 输入示例

```text
市场传出六氟化钨供应紧张，相关电子特气企业受到关注。
```

抽取结果：

```json
{
  "event_type": "supply_shortage",
  "target_entities": ["六氟化钨", "电子特气"],
  "intensity": "medium_high",
  "direction": "positive_for_supplier",
  "confidence": 0.78
}
```

---

## 3. 抽取字段

结构化事件至少包含：

```text
event_id
event_type
subtype
target_entities
trigger_words
intensity
direction
source_evidence_id
occurred_at
confidence
status
```

字段说明：

| 字段 | 说明 |
|---|---|
| event_type | 事件类型 |
| subtype | 事件子类型 |
| target_entities | 受影响实体 |
| trigger_words | 触发关键词 |
| intensity | 事件强度 |
| direction | 影响方向 |
| source_evidence_id | 来源证据 |
| occurred_at | 事件时间 |
| confidence | 抽取置信度 |
| status | candidate / active / rejected |

---

## 4. 事件类型

V2 第一阶段支持：

```text
supply_shortage
demand_growth
price_increase
price_decrease
capacity_expansion
export_control
import_restriction
policy_support
policy_restriction
geo_conflict
natural_disaster
technology_breakthrough
contract_award
earnings_surprise
risk_event
```

事件类型应保持有限，避免过细导致难以维护。

---

## 5. 抽取方式

### 5.1 Rule Extraction

适合明确关键词。

示例：

```text
紧缺 / 断供 / 供应紧张 -> supply_shortage
涨价 / 提价 / 价格上调 -> price_increase
出口管制 / 禁运 -> export_control
```

### 5.2 LLM Extraction

适合复杂文本。

LLM 应输出 JSON，不输出自然语言结论。

### 5.3 Hybrid Extraction

推荐默认使用混合方式：

```text
规则先召回
LLM 再结构化
图谱做实体归一
```

---

## 6. Trigger Words

trigger_words 用于解释事件为什么被抽取。

示例：

```text
供应紧张
缺货
断供
限产
价格上涨
出口管制
```

trigger_words 应保留到数据库，便于前端解释。

---

## 7. Target Entity Extraction

事件必须绑定影响对象。

示例：

```text
六氟化钨供应紧张
```

目标实体是：

```text
六氟化钨
```

如果事件只抽取出类型但没有目标实体，则不能进入核心推理。

---

## 8. Direction 判断

direction 表示事件对不同角色的影响方向。

示例：

```text
supply_shortage + commodity
```

可能表示：

```text
positive_for_supplier
negative_for_downstream_user
```

方向不是最终股票涨跌判断，只是产业影响方向。

---

## 9. Intensity 判断

intensity 表示事件强度。

可选值：

```text
low
medium
medium_high
high
critical
```

强度来源：

- 关键词。
- 来源等级。
- 新闻热度。
- 多源确认。
- 事件规模。

---

## 10. Extraction Confidence

抽取置信度与事件真实性不是同一个概念。

抽取置信度表示系统是否正确识别了事件。

事件真实性需要 Evidence 和多源验证。

---

## 11. 候选事件状态

事件状态：

```text
candidate
active
rejected
duplicate
expired
```

默认新闻抽取事件进入 candidate。

多源确认或高质量来源可进入 active。

---

## 12. 去重

事件去重依据：

```text
event_type
target_entities
occurred_at window
source cluster
```

同一事件被多个新闻重复报道，应合并为一个 EventInstance，并追加 evidence。

---

## 13. 设计原则

1. 事件必须有类型和目标实体。
2. LLM 只输出结构化候选。
3. 触发词必须保留。
4. 新闻事件默认候选状态。
5. 多源重复新闻应合并。
6. 事件抽取不直接推理股票。

---

## 14. 结论

Event Extraction 是 Reasoning Engine 的入口。

只有事件被正确结构化，后续商品映射、图谱推理和股票暴露度计算才有稳定基础。