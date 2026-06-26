# 04 Exposure Calculation

> 本文档定义 AStock V2 中股票暴露度计算设计。

---

## 1. Exposure 的定义

Exposure 表示某只股票与某个事件、商品、材料、行业或产业链节点之间的相关强度。

Exposure 不是简单的相关或不相关，而是一个连续分数。

推荐取值范围：

```text
0.0 - 1.0
```

---

## 2. Exposure 解决的问题

系统不应只回答：

```text
这只股票是否相关？
```

而应回答：

```text
这只股票有多相关？
相关路径是什么？
关系有多可信？
历史上是否有效？
```

---

## 3. Exposure 输入

Exposure Engine 的输入包括：

```text
structured_event
target_entities
impact_paths
kg_relations
evidence_confidence
company_profile
validation_results
```

---

## 4. Exposure 输出

输出结构：

```text
stock_code
stock_name
event_id
exposure_score
confidence
reason_paths
score_breakdown
```

示例：

```json
{
  "stock_code": "688146",
  "stock_name": "中船特气",
  "event_id": "evt_001",
  "exposure_score": 0.82,
  "confidence": 0.78,
  "reason_paths": [
    ["六氟化钨", "produced_by", "中船特气"]
  ]
}
```

---

## 5. 暴露度来源

Exposure 由多个因素组成：

1. 图谱路径强度。
2. 路径长度。
3. 关系置信度。
4. 证据质量。
5. 公司主营相关度。
6. 产品收入占比。
7. 历史事件验证表现。
8. 当前趋势状态。

---

## 6. Path Exposure

路径暴露度表示事件目标实体到股票之间路径的强度。

简化公式：

```text
path_exposure = product(edge_weight * edge_confidence) * depth_decay
```

depth_decay 示例：

```text
1 hop: 1.00
2 hops: 0.85
3 hops: 0.70
4 hops: 0.55
```

路径越长，暴露度越低。

---

## 7. 多路径合并

同一股票可能存在多条路径。

示例：

```text
六氟化钨 -> 中船特气
六氟化钨 -> 电子特气 -> 中船特气
钨 -> 钨材料 -> 中船特气
```

多路径合并不应简单相加，避免重复放大。

推荐：

```text
combined_exposure = 1 - product(1 - path_exposure_i)
```

这样多条路径会提高暴露度，但不会超过 1。

---

## 8. Evidence Adjustment

证据质量影响 confidence。

高质量证据提高 confidence：

- 年报。
- 招股书。
- 公告。
- 官网产品目录。

低质量证据降低 confidence：

- 普通新闻。
- 社交讨论。
- 未确认传闻。

Exposure Score 和 Confidence 应分离。

---

## 9. Business Relevance

如果能获得产品收入占比或主营业务权重，应纳入计算。

示例：

```text
公司确实生产某产品，但收入占比只有 1%，则 exposure 不应过高。
```

业务相关度字段：

```text
revenue_share
capacity_share
business_importance
management_focus
```

第一阶段可缺省为中性值。

---

## 10. Validation Adjustment

历史事件验证结果用于校准暴露度权重。

如果同类事件过去多次触发该股票超额表现，则提高 validation_score。

如果多次无效，则降低 validation_score。

注意：

Validation 调整的是交易有效性，不是否定产业事实。

---

## 11. Exposure Score 公式

第一阶段推荐公式：

```text
exposure_score = 0.45 * path_score
               + 0.25 * evidence_score
               + 0.15 * business_relevance
               + 0.15 * validation_score
```

如果部分数据缺失，则使用默认中性值并标记数据缺失。

---

## 12. Confidence 公式

confidence 用于表示该暴露度结论可信程度。

推荐：

```text
confidence = 0.50 * evidence_confidence
           + 0.30 * entity_mapping_confidence
           + 0.20 * relation_consistency
```

confidence 不直接代表上涨概率。

---

## 13. 输出解释

Exposure 输出必须能解释：

```text
为什么这只股票相关？
路径是什么？
哪条关系最关键？
证据来自哪里？
哪些数据缺失？
```

---

## 14. 低暴露过滤

建议过滤条件：

```text
exposure_score < 0.15 -> 过滤
confidence < 0.30 -> 进入观察，不进入正式候选
```

阈值可配置。

---

## 15. 设计原则

1. Exposure 是连续分数，不是布尔判断。
2. 路径越短、证据越强，暴露度越高。
3. 多路径合并要防止重复放大。
4. Exposure Score 和 Confidence 分离。
5. 历史验证只校准交易有效性。
6. 所有暴露度必须能解释路径。

---

## 16. 结论

Exposure Calculation 是 Reasoning Engine 到 Scoring Engine 的关键桥梁。

它把图谱路径转化为可排序、可解释、可验证的股票相关强度。