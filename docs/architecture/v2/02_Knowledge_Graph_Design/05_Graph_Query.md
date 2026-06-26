# 05 Graph Query

> 本文档定义 AStock V2 Knowledge Graph 的查询设计。

---

## 1. Graph Query 目标

图谱查询用于支持：

- 事件推理。
- 股票暴露度计算。
- 个股解释。
- 产业链探索。
- 证据追溯。
- 前端路径展示。

Graph Query 不只是简单查节点，而是要支持多跳路径查询和可解释路径返回。

---

## 2. 查询类型

V2 第一阶段支持以下查询：

```text
entity_lookup
neighbor_query
path_query
impact_query
stock_exposure_query
evidence_query
explain_query
```

---

## 3. Entity Lookup

用于根据名称、别名或代码查找实体。

输入示例：

```text
六氟化钨
WF6
688146
中船特气
```

输出：

```text
entity_id
entity_type
canonical_name
aliases
status
```

查询必须支持 aliases。

---

## 4. Neighbor Query

用于查询某个实体的一跳邻居。

示例：

```text
entity = 六氟化钨
```

返回：

```text
六氟化钨 -> belongs_to -> 电子特气
六氟化钨 -> used_in -> 半导体制造
中船特气 -> produces -> 六氟化钨
```

Neighbor Query 是前端 Supply Chain Explorer 的基础。

---

## 5. Path Query

用于查询两个实体之间的路径。

示例：

```text
source = 六氟化钨
target = 中船特气
max_depth = 4
```

输出：

```text
六氟化钨 <- produces <- 中船特气
```

或：

```text
六氟化钨 -> belongs_to -> 电子特气 -> belongs_to -> 半导体材料 -> related_to -> 中船特气
```

Path Query 必须返回：

- 节点列表。
- 关系列表。
- 每条关系权重。
- 每条关系置信度。
- 支持证据。

---

## 6. Impact Query

用于从事件影响对象向外扩散。

输入：

```text
event_type = supply_shortage
target_entity = 六氟化钨
```

输出：

```text
受影响材料
受影响行业
受影响公司
受影响股票
影响路径
```

Impact Query 是 Reasoning Engine 的核心查询。

---

## 7. Stock Exposure Query

用于查询某只股票对某个实体的暴露度。

输入：

```text
stock_code = 688146
entity = 六氟化钨
```

输出：

```text
exposure_score
confidence
reason_paths
evidence_list
```

示例：

```text
中船特气对六氟化钨暴露度高，因为公司直接生产六氟化钨，且该关系由招股书和官网产品目录支持。
```

---

## 8. Evidence Query

用于查询某条关系的证据来源。

输入：

```text
relation_id
```

输出：

```text
evidence_id
source_type
title
source_url
published_at
extracted_text
support_type
```

Evidence Query 是可解释性的基础。

---

## 9. Explain Query

用于生成前端解释路径。

输入：

```text
event_id
stock_code
```

输出：

```text
事件摘要
影响实体
图谱路径
股票暴露度
证据来源
历史验证
解释文本
```

Explain Query 不应重新执行重型推理，而应读取已落库的推理结果和图谱路径。

---

## 10. 查询约束

第一阶段建议限制最大路径深度。

推荐：

```text
max_depth = 4
```

原因：

- 超过 4 跳后路径解释性下降。
- 噪音关系增多。
- 查询成本上升。

---

## 11. 路径评分

路径评分应综合：

```text
relation_weight
relation_confidence
path_length_decay
evidence_quality
validation_score
```

简化公式：

```text
path_score = product(edge_weight * edge_confidence) * depth_decay
```

其中 depth_decay 用于惩罚过长路径。

---

## 12. 查询排序

候选路径排序依据：

1. 路径分数。
2. 路径长度。
3. 证据质量。
4. 历史验证表现。
5. 关系更新时间。

前端默认展示 Top N 路径，不展示所有路径。

---

## 13. 性能设计

关系型数据库阶段需要索引：

```text
kg_entities.canonical_name
kg_entities.entity_type
kg_relations.source_entity_id
kg_relations.target_entity_id
kg_relations.relation_type
kg_relations.status
relation_evidence.relation_id
```

多跳查询可以在服务层实现 BFS 或 DFS。

第一阶段不需要复杂图数据库。

---

## 14. 缓存策略

常用查询可以缓存：

- 股票知识卡。
- 热门实体邻居。
- 事件推理路径。
- 个股解释结果。

缓存失效条件：

- 图谱关系更新。
- Evidence 更新。
- Validation 结果更新。

---

## 15. Graph Query 设计原则

1. 所有查询应返回实体和关系，而不是只返回名称。
2. 路径查询必须带证据和置信度。
3. 默认限制路径深度。
4. 查询结果应可直接用于前端解释。
5. 查询不应修改图谱。
6. 重型路径计算应离线缓存。

---

## 16. 结论

Graph Query 是 Knowledge Graph 被系统使用的入口。

它不仅支持检索，更支持事件传播、股票暴露度和可解释展示。