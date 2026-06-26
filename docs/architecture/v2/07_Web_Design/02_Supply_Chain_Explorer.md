# 02 Supply Chain Explorer

> 本文档定义 AStock V2 Supply Chain Explorer 页面设计。

---

## 1. 页面目标

Supply Chain Explorer 用于展示 Knowledge Graph 中的产业链实体与关系。

该页面回答：

```text
某个商品、材料、行业或公司与哪些节点有关？
关系方向是什么？
关系证据是什么？
哪些股票暴露在这些节点上？
```

---

## 2. 页面结构

```text
Search Bar
Entity Detail Panel
Graph Canvas
Relation Detail Panel
Related Stocks Panel
Evidence Panel
```

---

## 3. Search Bar

搜索支持：

```text
公司名称
股票代码
产品名称
材料名称
商品名称
行业名称
概念名称
别名
```

搜索结果应展示：

```text
entity_name
entity_type
aliases
confidence
```

---

## 4. Entity Detail Panel

实体详情展示：

```text
entity_name
entity_type
canonical_name
aliases
description
status
last_updated_at
```

如果实体是公司，应展示股票代码。

如果实体是产品，应展示所属材料或行业。

---

## 5. Graph Canvas

图谱画布展示邻居节点和关系。

节点类型：

```text
Company
Stock
Product
Material
Commodity
Industry
Sector
Concept
Event
```

边展示：

```text
relation_type
weight
confidence
```

默认展示一跳关系，可手动展开二跳。

---

## 6. Relation Detail Panel

点击边后展示关系详情：

```text
source_entity
target_entity
relation_type
weight
confidence
source_type
status
valid_from
valid_to
```

并展示关联证据摘要。

---

## 7. Related Stocks Panel

对于商品、材料、行业实体，展示相关股票：

```text
stock_code
stock_name
exposure_score
confidence
primary_path
```

支持按 exposure_score 排序。

---

## 8. Evidence Panel

展示当前实体或关系的证据：

```text
source_type
title
published_at
extracted_text
source_url
support_type
```

证据可折叠展示，避免页面过长。

---

## 9. 交互设计

支持操作：

- 搜索实体。
- 点击节点切换中心实体。
- 展开邻居节点。
- 点击关系查看证据。
- 点击股票进入个股详情。
- 点击事件进入事件详情。

---

## 10. 图谱范围控制

避免一次展示过多节点。

默认限制：

```text
max_depth = 1
max_neighbors = 30
```

用户可手动展开，但需要限制总节点数。

---

## 11. 低置信关系展示

低置信关系应使用明显标记。

示例：

```text
候选关系
弱证据
待审核
冲突证据
```

低置信关系默认可隐藏或折叠。

---

## 12. 设计原则

1. 图谱默认展示少量高质量关系。
2. 支持逐层展开，不一次性全量展示。
3. 关系详情必须能看到证据。
4. 节点和边都必须有类型。
5. 低置信关系不能与高置信关系混淆。

---

## 13. 结论

Supply Chain Explorer 是 V2 知识图谱的可视化入口。

它让用户能够从任意实体出发，理解产业链关系和股票暴露。