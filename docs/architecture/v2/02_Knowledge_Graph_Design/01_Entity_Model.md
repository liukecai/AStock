# 01 Entity Model

> 本文档定义 AStock V2 Knowledge Graph 的实体模型。

---

## 1. Entity 设计目标

Entity 用于表达图谱中的节点。

V2 的实体模型必须满足：

- 能表达 A股上市公司。
- 能表达股票代码。
- 能表达产品、材料、商品、行业、概念。
- 能表达事件类型和事件实例。
- 能绑定证据来源。
- 能支持别名和归一化。
- 能支持后续扩展。

---

## 2. Entity 基础字段

所有实体至少包含：

```text
entity_id
entity_type
name
canonical_name
aliases
description
status
created_at
updated_at
```

字段说明：

| 字段 | 说明 |
|---|---|
| entity_id | 全局唯一 ID |
| entity_type | 实体类型 |
| name | 展示名称 |
| canonical_name | 归一化名称 |
| aliases | 别名列表 |
| description | 简要说明 |
| status | active / inactive / candidate |
| created_at | 创建时间 |
| updated_at | 更新时间 |

---

## 3. 核心 Entity 类型

### 3.1 Company

上市公司或非上市公司主体。

示例：

```text
中船特气
中钨高新
厦门钨业
```

核心字段：

```text
company_name
legal_name
short_name
stock_code
exchange
website
```

Company 用于承载公司画像。

---

### 3.2 Stock

股票实体。

示例：

```text
688146.SH
000657.SZ
600160.SH
```

核心字段：

```text
stock_code
stock_name
exchange
list_date
company_entity_id
```

Company 和 Stock 分离的原因是：

- 一个公司可能有多个证券代码。
- 后续可扩展港股、美股、债券等资产。

---

### 3.3 Product

公司生产或销售的具体产品。

示例：

```text
六氟化钨
三氟化氮
高纯氨
硬质合金
APT
```

Product 是公司与产业链之间最重要的连接点。

---

### 3.4 Material

材料或中间品。

示例：

```text
电子特气
半导体材料
钨材料
光刻胶
电池级碳酸锂
```

Material 可以是 Product 的上级抽象，也可以是 Commodity 的下级节点。

---

### 3.5 Commodity

商品或资源品。

示例：

```text
钨
铜
锂
原油
天然气
黄金
```

Commodity 常用于宏观事件、供需冲击和价格变化推理。

---

### 3.6 Industry

行业。

示例：

```text
半导体材料
有色金属
军工
航运
光伏
新能源汽车
```

Industry 用于连接公司和宏观产业链。

---

### 3.7 Sector

市场板块或交易层面的板块分类。

示例：

```text
有色金属板块
半导体板块
军工板块
中特估
低空经济
```

Sector 更接近市场交易视角，Industry 更接近产业视角。

---

### 3.8 Concept

概念题材。

示例：

```text
HBM
AI 算力
机器人
液冷
国产替代
```

Concept 通常变化更快，置信度应低于 Product 和 Industry。

---

### 3.9 EventType

事件类型。

示例：

```text
supply_shortage
demand_growth
policy_support
export_control
geo_conflict
price_increase
capacity_expansion
```

EventType 是抽象类型，不代表某一次具体事件。

---

### 3.10 EventInstance

具体事件实例。

示例：

```text
2026-xx-xx 六氟化钨供应紧张
2026-xx-xx 中东冲突升级
```

EventInstance 应包含：

```text
event_type
occurred_at
source_evidence_id
intensity
direction
```

---

### 3.11 Evidence

证据实体。

Evidence 代表一条可追溯来源。

示例：

```text
2025 年报
招股说明书
官网产品页面
公告 PDF
互动易回复
```

Evidence 不一定参与所有推理，但必须能支持关系追溯。

---

## 4. Entity 命名规范

### 4.1 canonical_name

必须使用统一规范名称。

示例：

```text
六氟化钨
WF6
Tungsten Hexafluoride
```

统一到：

```text
六氟化钨
```

### 4.2 aliases

别名必须保留：

```text
WF6
Tungsten Hexafluoride
六氟化钨气体
```

别名用于新闻匹配和 LLM 抽取归一化。

---

## 5. Entity 状态

实体状态包括：

```text
candidate
active
inactive
rejected
merged
```

说明：

| 状态 | 说明 |
|---|---|
| candidate | 候选实体 |
| active | 正式实体 |
| inactive | 暂不使用 |
| rejected | 已拒绝 |
| merged | 已合并到其他实体 |

---

## 6. Entity 合并

实体合并用于处理同义词和重复节点。

示例：

```text
WF6 -> 六氟化钨
Tungsten Hexafluoride -> 六氟化钨
```

合并后原实体不删除，而是标记为 merged，并指向 canonical entity。

---

## 7. Entity 设计原则

1. Company 和 Stock 分离。
2. Product 和 Material 分离。
3. Industry 和 Sector 分离。
4. EventType 和 EventInstance 分离。
5. Evidence 作为一等实体保留。
6. 所有实体必须支持别名和归一化。

---

## 8. 结论

Entity Model 的核心目标是为事件推理提供稳定节点。

只有实体边界清晰，Relation Model、Reasoning Engine 和 Exposure Engine 才能稳定工作。