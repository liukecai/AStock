# 07 ADR

> 本文档记录 AStock V2 System Architecture 阶段的关键架构决策。

---

## ADR-001：采用目录式架构文档，而不是单个超长 Markdown

### 状态

Accepted

### 背景

V2 架构内容较多，如果写成单个 `01_System_Architecture.md`，文件会很长，不利于阅读、评审和后续维护。

### 决策

采用目录式文档：

```text
01_System_Architecture/
├── README.md
├── 00_Overview.md
├── 01_Current_State.md
├── 02_Target_Architecture.md
├── 03_Module_Responsibilities.md
├── 04_Data_Flow.md
├── 05_Runtime.md
├── 06_Deployment.md
└── 07_ADR.md
```

### 影响

优点：

- 单文件更短。
- 主题边界更清晰。
- 更容易 Code Review。
- 后续可以独立更新某个主题。

代价：

- 文件数量增加。
- 需要 README 维护阅读顺序。

---

## ADR-002：V2 不推翻 V1，而是在 V1 上叠加图谱与推理层

### 状态

Accepted

### 背景

V1 已经具备行情、新闻、公告、趋势评分、事件映射和 Web 展示能力。

这些能力仍然有价值，不应重写。

### 决策

V2 采用增量升级：

```text
V1 基础设施
  + Evidence Layer
  + Knowledge Graph
  + Reasoning Engine
  + Validation Loop
  + Explainability Layer
```

### 影响

优点：

- 降低重构风险。
- 保留已有功能。
- 可以阶段性交付。

代价：

- 需要兼容现有数据结构。
- 迁移期间会存在新旧模块并行。

---

## ADR-003：LLM 不作为最终决策模块

### 状态

Accepted

### 背景

LLM 适合文本理解和结构化抽取，但不适合作为不可审计的最终判断模块。

### 决策

LLM 只负责：

- 抽取实体。
- 抽取关系。
- 抽取事件。
- 生成候选知识。
- 生成解释文本草稿。

最终影响计算由：

```text
Knowledge Graph + Reasoning Engine + Market Validation
```

完成。

### 影响

优点：

- 降低幻觉风险。
- 提高系统可审计性。
- 保持结果稳定。

代价：

- 架构更复杂。
- 需要维护候选关系和审核流程。

---

## ADR-004：第一阶段不直接引入 Neo4j

### 状态

Accepted

### 背景

Neo4j 适合复杂图查询，但会增加部署、维护和迁移成本。

当前 V2 第一阶段的图谱规模尚可使用关系型数据库表达。

### 决策

V2 第一阶段采用关系型数据库图谱表：

```text
kg_entities
kg_relations
evidence
candidate_relations
```

未来当路径查询复杂度和数据规模增加后，再评估 Neo4j。

### 影响

优点：

- 降低部署复杂度。
- 复用现有数据库栈。
- 更容易与 API 和验证数据关联。

代价：

- 多跳查询能力有限。
- 后续可能需要迁移图数据库。

---

## ADR-005：第一阶段保留 YAML 作为种子知识来源

### 状态

Accepted

### 背景

V1 已经存在事件、商品、股票映射规则。

这些规则虽然不是最终形态，但具有较高人工置信度。

### 决策

YAML 不废弃，而是作为 Knowledge Graph 的 seed source。

```text
YAML
  ↓
yaml_to_kg_loader
  ↓
kg_entities / kg_relations
```

### 影响

优点：

- 复用已有规则资产。
- 快速初始化图谱。
- 保持规则可读性。

代价：

- 需要维护 YAML 到图谱的同步逻辑。
- 需要避免 YAML 和图谱长期双写冲突。

---

## ADR-006：验证闭环作为 V2 核心能力

### 状态

Accepted

### 背景

事件推理如果不验证市场表现，只能停留在概念相关。

系统需要知道哪些关系真的有效。

### 决策

V2 必须引入 Validation Engine，记录事件发生后的：

- T+1 表现。
- T+3 表现。
- T+5 表现。
- T+10 表现。
- 相对指数表现。
- 相对行业表现。

### 影响

优点：

- 可以评估事件类型有效性。
- 可以校准关系权重。
- 可以识别噪音关系。

代价：

- 需要可靠行情数据。
- 需要处理停牌、涨跌停、非交易日等情况。

---

## ADR-007：在线服务不执行重型任务

### 状态

Accepted

### 背景

LLM 抽取、PDF 解析、图谱批量更新和历史验证计算都可能耗时较长。

如果放在 API 请求中执行，会导致响应慢且不稳定。

### 决策

在线服务只查询已落库结果。

重型任务全部放入离线任务或 Worker。

### 影响

优点：

- API 响应稳定。
- 成本可控。
- 易于监控和重试。

代价：

- 数据存在延迟。
- 需要维护任务状态。

---

## ADR-008：V2 输出解释路径，而不是只输出分数

### 状态

Accepted

### 背景

事件驱动系统的用户需要理解结果来源。

仅有分数无法建立信任。

### 决策

V2 的核心输出必须包括：

- 事件。
- 影响实体。
- 图谱路径。
- 股票暴露度。
- 证据来源。
- 历史验证。
- 分数拆解。

### 影响

优点：

- 提高可解释性。
- 便于人工复核。
- 便于前端展示。

代价：

- API 返回结构更复杂。
- 前端展示复杂度增加。

---

## 结论

System Architecture 阶段的核心决策是：

```text
保留 V1
引入 Evidence
沉淀 Knowledge Graph
使用 Reasoning Engine
建立 Validation Loop
在线查询与离线计算解耦
```

这些决策构成 AStock V2 的架构基础。