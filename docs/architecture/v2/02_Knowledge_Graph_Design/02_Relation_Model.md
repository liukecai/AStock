# 02 Relation Model

> 本文档定义 AStock V2 Knowledge Graph 的关系模型。

---

## 1. Relation 设计目标

Relation 用于表达实体之间的有向关系。

V2 的关系模型必须支持：

- 产业链上下游关系。
- 公司与产品关系。
- 产品与材料关系。
- 商品与行业关系。
- 事件与受影响实体关系。
- 关系权重。
- 关系置信度。
- 证据来源。
- 历史验证结果回写。

---

## 2. Relation 基础字段

所有关系至少包含：

```text
relation_id
source_entity_id
target_entity_id
relation_type
direction
weight
confidence
source_type
evidence_ids
status
created_at
updated_at
```

字段说明：

| 字段 | 说明 |
|---|---|
| relation_id | 全局唯一关系 ID |
| source_entity_id | 起点实体 |
| target_entity_id | 终点实体 |
| relation_type | 关系类型 |
| direction | 方向，一般为 directed |
| weight | 推理权重 |
| confidence | 置信度 |
| source_type | 关系来源类型 |
| evidence_ids | 支持证据列表 |
| status | candidate / active / rejected |
| created_at | 创建时间 |
| updated_at | 更新时间 |

---

## 3. 核心关系类型

### 3.1 listed_as

表示公司与股票代码之间的上市关系。

```text
Company -> listed_as -> Stock
```

示例：

```text
中船特气 -> listed_as -> 688146.SH
```

---

### 3.2 produces

表示公司生产某个产品。

```text
Company -> produces -> Product
```

示例：

```text
中船特气 -> produces -> 六氟化钨
```

该关系通常来自年报、招股书、官网产品目录，置信度较高。

---

### 3.3 supplies

表示公司供应某个产品或服务。

```text
Company -> supplies -> Product / Industry
```

示例：

```text
公司A -> supplies -> 半导体客户
```

supplies 比 produces 更宽泛，置信度通常低于 produces。

---

### 3.4 uses

表示产品、公司或行业使用某种材料或商品。

```text
Product -> uses -> Material
Industry -> uses -> Commodity
```

示例：

```text
硬质合金 -> uses -> 钨
```

---

### 3.5 belongs_to

表示实体归属上级分类。

```text
Product -> belongs_to -> Material
Material -> belongs_to -> Industry
Industry -> belongs_to -> Sector
```

示例：

```text
六氟化钨 -> belongs_to -> 电子特气
电子特气 -> belongs_to -> 半导体材料
```

---

### 3.6 upstream_of

表示产业链上游关系。

```text
EntityA -> upstream_of -> EntityB
```

示例：

```text
钨 -> upstream_of -> 六氟化钨
```

---

### 3.7 downstream_of

表示产业链下游关系。

```text
EntityA -> downstream_of -> EntityB
```

通常可以由 upstream_of 反向推导，但必要时可显式存储。

---

### 3.8 used_in

表示某个产品、材料或商品用于某个行业或应用。

```text
Product -> used_in -> Industry
```

示例：

```text
六氟化钨 -> used_in -> 半导体制造
```

---

### 3.9 impacts

表示事件类型影响某个实体。

```text
EventType -> impacts -> Commodity / Material / Industry
```

示例：

```text
supply_shortage -> impacts -> 六氟化钨
```

---

### 3.10 benefits

表示某事件或实体变化对目标实体正向影响。

```text
EventType -> benefits -> Company / Industry
```

该关系应谨慎使用，优先通过推理路径和评分计算得出。

---

### 3.11 hurts

表示某事件或实体变化对目标实体负向影响。

```text
EventType -> hurts -> Company / Industry
```

同样应谨慎使用，避免过度主观。

---

### 3.12 exposed_to

表示股票或公司对某个产品、商品、行业有暴露。

```text
Company / Stock -> exposed_to -> Entity
```

exposed_to 可以由其他关系推导，也可以作为验证后的显式关系沉淀。

---

### 3.13 evidenced_by

表示关系或实体由某条证据支持。

```text
Relation -> evidenced_by -> Evidence
```

在关系型数据库中可通过 relation_evidence 表实现。

---

### 3.14 aliases

表示别名关系。

```text
AliasEntity -> aliases -> CanonicalEntity
```

示例：

```text
WF6 -> aliases -> 六氟化钨
```

---

## 4. 关系方向

关系默认有方向。

例如：

```text
中船特气 -> produces -> 六氟化钨
```

不等价于：

```text
六氟化钨 -> produces -> 中船特气
```

但查询时可以允许反向遍历。

---

## 5. 关系权重

weight 用于推理传播。

取值范围建议：

```text
0.0 - 1.0
```

示例：

```text
produces: 0.9
belongs_to: 0.8
used_in: 0.7
news_related: 0.4
```

权重表示该关系在事件传播中的强度，不等于可信度。

---

## 6. 关系置信度

confidence 表示关系真实性可信程度。

取值范围：

```text
0.0 - 1.0
```

来源建议：

```text
年报：0.90 - 0.98
招股书：0.90 - 0.98
官网产品目录：0.80 - 0.95
公告：0.75 - 0.95
互动易：0.55 - 0.80
新闻：0.40 - 0.70
社交讨论：0.20 - 0.50
LLM 候选：按证据源调整
```

---

## 7. Relation 状态

关系状态包括：

```text
candidate
active
rejected
deprecated
validated
```

说明：

| 状态 | 说明 |
|---|---|
| candidate | 候选关系 |
| active | 正式关系 |
| rejected | 已拒绝 |
| deprecated | 已过期 |
| validated | 已通过市场验证强化 |

---

## 8. 关系合并

当多个来源支持同一关系时，不创建多条重复关系。

应合并为一条关系，并追加 evidence。

示例：

```text
中船特气 -> produces -> 六氟化钨
```

可能由以下证据共同支持：

- 招股书。
- 年报。
- 官网产品目录。

合并后提高 confidence。

---

## 9. Relation 设计原则

1. 关系必须有类型。
2. 关系必须有方向。
3. 关系必须有置信度。
4. 关系应尽可能绑定证据。
5. 关系权重和置信度分离。
6. 候选关系不能直接参与核心推理。
7. 多来源关系应合并，不应重复创建。

---

## 10. 结论

Relation Model 是 Knowledge Graph 能否用于推理的关键。

如果只保存标签，系统无法推理。

如果保存有方向、有权重、有证据、有置信度的关系，系统才能回答：

```text
为什么某个事件会影响某只股票？
这条路径有多可信？
这条路径过去是否有效？
```