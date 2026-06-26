# 00 Overview

> 本文档定义 AStock V2 Reasoning Engine 的总体设计。

---

## 1. 为什么需要 Reasoning Engine

AStock V1 可以通过规则将事件映射到股票。

但真实市场事件通常不是直接影响股票，而是沿产业链传播：

```text
事件
  ↓
商品 / 材料
  ↓
行业 / 应用
  ↓
公司 / 股票
```

例如：

```text
六氟化钨供应紧张
  ↓
六氟化钨
  ↓
电子特气
  ↓
半导体材料
  ↓
中船特气
```

Reasoning Engine 的作用是把这种传播过程系统化。

---

## 2. Reasoning Engine 的核心问题

Reasoning Engine 需要回答：

1. 这个新闻描述的是什么事件？
2. 事件影响的初始实体是什么？
3. 初始实体属于哪些商品、材料或行业？
4. 哪些公司和股票与这些实体存在关系？
5. 哪些路径更短、更强、更可信？
6. 哪些股票暴露度更高？
7. 推理结果是否能被历史行情验证？

---

## 3. 推理输入

Reasoning Engine 的输入可以是：

### 3.1 原始事件文本

```text
市场传出六氟化钨供应紧张。
```

### 3.2 结构化事件

```json
{
  "event_type": "supply_shortage",
  "target_entities": ["六氟化钨"],
  "intensity": "high",
  "direction": "positive_for_supplier"
}
```

### 3.3 已入库事件实例

```text
event_id = evt_20260627_001
```

在线服务应优先使用已结构化事件。

---

## 4. 推理输出

Reasoning Engine 的输出包括：

```text
event_id
target_entities
impacted_entities
impact_paths
candidate_stocks
exposure_scores
confidence
explanation
```

示例：

```json
{
  "event_id": "evt_001",
  "paths": [
    {
      "stock_code": "688146",
      "path": ["六氟化钨", "电子特气", "中船特气"],
      "path_score": 0.76,
      "exposure_score": 0.82,
      "confidence": 0.78
    }
  ]
}
```

---

## 5. 推理阶段

Reasoning Engine 分为六个阶段：

```text
Event Extraction
  ↓
Event Normalization
  ↓
Initial Entity Mapping
  ↓
Graph Traversal
  ↓
Exposure Calculation
  ↓
Result Explanation
```

---

## 6. 推理模式

### 6.1 Batch Reasoning

用于盘后批量处理当天新增事件。

特点：

- 可处理更多路径。
- 可写入数据库。
- 可供前端快速查询。

### 6.2 On-demand Reasoning

用于用户手动输入事件进行临时推理。

特点：

- 响应应较快。
- 路径深度应限制。
- 不应执行重型 LLM 长文本抽取。

---

## 7. 推理边界

Reasoning Engine 不做：

- 外部数据采集。
- PDF 解析。
- 长文本 LLM 抽取。
- 图谱事实关系维护。
- 实盘交易建议。

Reasoning Engine 只做：

```text
事件 -> 图谱路径 -> 股票暴露度
```

---

## 8. 推理依赖

Reasoning Engine 依赖：

- Knowledge Graph。
- Event Engine。
- Evidence Model。
- Market Data。
- Scoring Engine。
- Validation Engine。

其中 Knowledge Graph 是最核心依赖。

---

## 9. 推理质量指标

推理质量可通过以下指标评估：

- 命中股票数量是否合理。
- 路径是否可解释。
- 路径证据是否充分。
- 暴露度排序是否符合常识。
- 历史验证是否有效。
- 噪音股票比例是否可控。

---

## 10. 结论

Reasoning Engine 是 AStock V2 从“规则选股”升级为“事件推演”的核心。

它的目标不是预测市场，而是构建一条可解释、可验证的影响路径：

```text
事件为什么可能影响这只股票？
```