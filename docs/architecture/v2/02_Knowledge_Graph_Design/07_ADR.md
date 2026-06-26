# 07 ADR

> 本文档记录 AStock V2 Knowledge Graph Design 阶段的关键架构决策。

---

## ADR-001：采用 Knowledge Graph 表达产业链关系

### 状态

Accepted

### 背景

V1 使用 YAML 或规则映射表达事件到股票的关系。

随着事件和产业链节点增加，规则难以复用和解释。

### 决策

V2 引入 Knowledge Graph，表达：

```text
Company
Product
Material
Commodity
Industry
Sector
Concept
Event
Evidence
```

之间的关系。

### 影响

优点：

- 支持多跳推理。
- 支持证据追踪。
- 支持关系复用。
- 支持前端解释路径。

代价：

- 数据模型更复杂。
- 需要实体归一化和关系维护。

---

## ADR-002：采用 Entity + Relation，而不是 Stock Tag

### 状态

Accepted

### 背景

简单标签无法表达关系方向和证据。

例如：

```text
中船特气 tags = [电子特气, 半导体]
```

无法说明公司到底是生产电子特气，还是客户在半导体行业。

### 决策

采用实体和关系建模：

```text
中船特气 produces 六氟化钨
六氟化钨 belongs_to 电子特气
电子特气 used_in 半导体制造
```

### 影响

优点：

- 关系语义明确。
- 可用于路径推理。
- 可解释性更强。

代价：

- 建模成本高于标签系统。
- 需要维护 relation_type。

---

## ADR-003：Company 和 Stock 分离建模

### 状态

Accepted

### 背景

股票代码并不等同于公司主体。

一个公司未来可能对应多个证券、多个市场或其他资产。

### 决策

分离：

```text
Company -> listed_as -> Stock
```

### 影响

优点：

- 更符合真实金融资产结构。
- 便于未来扩展港股、美股、债券、基金等资产。

代价：

- 查询时需要多一跳映射。

---

## ADR-004：Evidence 作为一等对象

### 状态

Accepted

### 背景

如果图谱只保存关系，不保存证据来源，后续无法审计关系可信度。

### 决策

Evidence 作为独立对象存在，并通过 relation_evidence 绑定到关系。

### 影响

优点：

- 关系可追溯。
- 置信度可解释。
- 前端可以展示证据来源。

代价：

- 存储和查询复杂度增加。

---

## ADR-005：LLM 输出进入 Candidate 层，而非直接进入正式图谱

### 状态

Accepted

### 背景

LLM 抽取可能出现错误或过度推断。

### 决策

LLM 输出只写入：

```text
candidate_entities
candidate_relations
```

经过校验或审核后才进入正式图谱。

### 影响

优点：

- 降低幻觉风险。
- 保持图谱可信。
- 支持人工复核。

代价：

- 需要候选层和审核流程。

---

## ADR-006：第一阶段使用关系型数据库实现图谱

### 状态

Accepted

### 背景

Neo4j 提供强图查询能力，但会显著增加部署和维护成本。

V2 第一阶段的图谱规模可用关系型数据库表达。

### 决策

第一阶段使用表结构：

```text
kg_entities
kg_relations
evidence
relation_evidence
candidate_entities
candidate_relations
```

后续再评估 Neo4j。

### 影响

优点：

- 复用现有数据库栈。
- 部署简单。
- 易于与行情、事件、验证结果关联。

代价：

- 多跳查询性能有限。
- 复杂图算法能力弱。

---

## ADR-007：confidence 与 weight 分离

### 状态

Accepted

### 背景

关系真实性和事件传播强度不是同一个概念。

例如：

```text
公司确实生产某产品：confidence 高
但该产品收入占比很低：weight 低
```

### 决策

每条关系同时保存：

```text
confidence
weight
```

### 影响

优点：

- 推理更准确。
- 可区分事实可信度和影响强度。

代价：

- 评分和更新逻辑更复杂。

---

## ADR-008：市场验证只校准 weight，不直接否定事实关系

### 状态

Accepted

### 背景

某公司生产某产品是事实关系。

但市场不一定每次都交易这条关系。

### 决策

Validation Engine 的结果主要回写 impact weight，而不是直接删除事实关系。

### 影响

优点：

- 避免把市场短期噪音误认为事实错误。
- 能区分产业事实和交易有效性。

代价：

- 需要维护两套权重含义。

---

## 结论

Knowledge Graph Design 阶段的关键决策是：

```text
用实体关系替代标签
用证据支撑关系
用候选层隔离 LLM 风险
用关系型数据库快速落地
用验证结果校准影响强度
```

这些决策共同保证图谱既能快速实现，又能长期演进。