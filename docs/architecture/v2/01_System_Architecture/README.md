# 01 System Architecture

> 本目录定义 AStock V2 的总体系统架构。
>
> 本章节目标不是描述某个单点功能，而是明确 V2 为什么从 V1 的“行情 + 舆情 + 规则选股系统”，升级为“产业知识图谱 + 事件推理引擎 + 验证闭环系统”。

---

## 文档范围

本目录包含以下文档：

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

---

## 阅读顺序

建议按以下顺序阅读：

1. `00_Overview.md`：理解 V2 的架构目标和总体设计。
2. `01_Current_State.md`：理解 V1 当前能力、问题和升级动因。
3. `02_Target_Architecture.md`：理解 V2 最终系统形态。
4. `03_Module_Responsibilities.md`：理解每个模块的职责边界。
5. `04_Data_Flow.md`：理解事件、图谱、行情、信号之间的数据流。
6. `05_Runtime.md`：理解离线任务、在线服务、调度任务如何协作。
7. `06_Deployment.md`：理解 V2 的部署拓扑和演进路径。
8. `07_ADR.md`：理解关键架构决策及其取舍。

---

## V2 核心变化

AStock V1 的核心链路是：

```text
行情数据 + 新闻舆情 + 规则映射
  ↓
趋势评分 / 舆情评分 / 事件评分
  ↓
股票列表与 Web 展示
```

AStock V2 的核心链路升级为：

```text
Evidence
  ↓
Knowledge Graph
  ↓
Reasoning Engine
  ↓
Exposure / Score
  ↓
Validation
  ↓
Explainable Web
```

---

## 架构关键词

### Evidence

证据，指来自年报、招股书、公告、官网产品目录、互动易、新闻、RSS、招聘、专利等来源的原始事实。

### Knowledge Graph

产业知识图谱，用于沉淀公司、产品、材料、商品、行业、概念、事件之间的长期关系。

### Reasoning Engine

事件推理引擎，用于将新闻事件映射到产业链节点，并沿图谱传播到可能受影响股票。

### Exposure

股票暴露度，用于表示某只股票和某个事件、商品、材料或产业链节点之间的相关强度。

### Validation

验证闭环，用于记录事件发生后 T+1、T+3、T+5、T+10 的收益表现，并反向校准关系权重。

### Explainability

可解释性，用于向用户说明“为什么这只股票与该事件相关”。

---

## V2 成功标准

V2 完成后，系统应能回答：

1. 某个事件会影响哪些商品、材料、行业和股票？
2. 某只股票为什么和某个事件相关？
3. 这条关系来自哪些证据？
4. 该关系的置信度是多少？
5. 同类事件过去是否产生过超额收益？
6. 用户能否在 Web 上看到完整推理路径？

---

## 非目标

V2 不解决以下问题：

- 自动交易下单。
- 高频事件交易。
- 完全无人审核的 LLM 图谱写入。
- 对所有新闻直接生成买卖建议。
- 使用大模型直接替代量化评分与行情验证。

V2 的目标是建立稳定、可解释、可验证、可持续积累的事件推理系统。