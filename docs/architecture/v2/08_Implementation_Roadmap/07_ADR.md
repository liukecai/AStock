# 07 ADR

> 本文档记录 AStock V2 Implementation Roadmap 阶段的关键架构决策。

---

## ADR-001：采用分阶段增量实施

### 状态

Accepted

### 背景

V2 涉及图谱、推理、抽取、验证和前端解释，如果一次性重写风险过高。

### 决策

采用六阶段增量实施：

```text
KG Schema
YAML Migration
Reasoning MVP
Extraction
Validation Loop
Web Explainability
```

### 影响

优点：

- 风险可控。
- 每阶段可验收。
- 不破坏 V1。

代价：

- 阶段之间存在临时兼容逻辑。

---

## ADR-002：先图谱 Schema，后推理引擎

### 状态

Accepted

### 背景

Reasoning Engine 依赖稳定的实体和关系模型。

### 决策

先完成 kg_entities、kg_relations、evidence 等基础表，再开发推理引擎。

### 影响

优点：

- 推理输入稳定。
- 后续模块边界清晰。

代价：

- 初期看不到完整产品效果。

---

## ADR-003：YAML 作为图谱种子数据

### 状态

Accepted

### 背景

V1 中已有人工维护规则，具有复用价值。

### 决策

通过 yaml_to_kg_loader 将 YAML 迁移为图谱实体和关系。

### 影响

优点：

- 复用已有资产。
- 快速初始化图谱。

代价：

- 需要维护迁移脚本。

---

## ADR-004：抽取能力晚于图谱和推理 MVP

### 状态

Accepted

### 背景

如果过早引入自动抽取，会在图谱模型未稳定时产生大量噪音。

### 决策

先完成图谱和推理 MVP，再引入抽取候选层。

### 影响

优点：

- 图谱模型更稳定。
- 抽取结果有明确落点。

代价：

- 初期图谱扩充仍需手工 seed。

---

## ADR-005：验证闭环必须在前端大规模展示前完成

### 状态

Accepted

### 背景

如果只展示事件候选结果，没有历史验证，会降低可信度。

### 决策

在完整 Web Explainability 前完成 Validation Loop。

### 影响

优点：

- 前端展示更可信。
- 支持分数校准。

代价：

- 需要较完整行情数据。

---

## ADR-006：Web 最后集成完整解释链路

### 状态

Accepted

### 背景

Web 解释依赖图谱、推理、证据和验证结果。

### 决策

Web Explainability 作为第六阶段，整合前面阶段产物。

### 影响

优点：

- 前端数据结构稳定。
- 页面能一次性展示完整链路。

代价：

- 前期产品感知较弱。

---

## 结论

Implementation Roadmap 的核心决策是：

```text
增量实施
先图谱
再迁移
再推理
再抽取
再验证
最后展示
```

这条路线保证 AStock V2 能稳步从 V1 演进，而不是一次性高风险重写。