# 00 Overview

> 本文档定义 AStock V2 Knowledge Graph 的总体设计目标、边界和核心思想。

---

## 1. 为什么需要 Knowledge Graph

AStock V1 已经具备事件到股票的规则映射能力。

但事件驱动系统越往后发展，规则会越来越难维护。

例如：

```text
六氟化钨紧缺 -> 钨 -> 电子特气 -> 半导体材料 -> 中船特气
```

这不是单条规则，而是一条产业链关系路径。

如果每个事件都手工写成事件到股票映射，系统会出现：

- 重复规则。
- 无法复用中间节点。
- 无法解释关系来源。
- 无法进行多跳推理。
- 无法自动发现相邻产业链机会。

Knowledge Graph 的作用是把这些长期关系沉淀下来。

---

## 2. 图谱解决的问题

Knowledge Graph 主要解决五个问题：

### 2.1 股票涉及什么产业链

例如：

```text
中船特气 -> 六氟化钨 -> 电子特气 -> 半导体材料
```

### 2.2 事件影响哪些产业链节点

例如：

```text
供应紧张 -> 六氟化钨
```

### 2.3 产业链节点如何传播到股票

例如：

```text
六氟化钨 -> 生产商 -> 中船特气
```

### 2.4 一条关系来自哪里

例如：

```text
关系来源：年报、招股书、官网产品目录、公告
```

### 2.5 关系过去是否有效

例如：

```text
同类事件发生后，该股票 T+3 平均超额收益是否为正
```

---

## 3. 图谱不是标签系统

错误设计：

```text
股票：中船特气
标签：电子特气、半导体、钨
```

标签系统的问题是：

- 无法表达关系类型。
- 无法表达方向。
- 无法表达证据。
- 无法表达路径。
- 无法推理。

正确设计：

```text
中船特气 produces 六氟化钨
六氟化钨 belongs_to 电子特气
电子特气 used_in 半导体制造
```

图谱的核心不是“有哪些标签”，而是“实体之间是什么关系”。

---

## 4. 图谱实体范围

V2 第一阶段实体包括：

- Company。
- Stock。
- Product。
- Material。
- Commodity。
- Industry。
- Sector。
- Concept。
- EventType。
- EventInstance。
- Source。
- Evidence。

后续可扩展：

- Country。
- Region。
- Policy。
- Technology。
- Customer。
- Supplier。
- Capacity。
- Project。

---

## 5. 图谱关系范围

V2 第一阶段关系包括：

- listed_as。
- produces。
- supplies。
- uses。
- belongs_to。
- upstream_of。
- downstream_of。
- used_in。
- impacts。
- benefits。
- hurts。
- exposed_to。
- evidenced_by。
- aliases。

这些关系应支持方向和权重。

---

## 6. 图谱的输入来源

图谱可以从以下来源构建：

```text
YAML 规则库
年报
招股说明书
巨潮公告
公司官网产品目录
互动易
新闻与 RSS
LLM 抽取结果
人工维护
历史验证结果
```

不同来源对应不同基础置信度。

例如：

```text
年报：高
招股书：高
官网产品目录：较高
公告：较高
互动易：中
新闻：中低
社交讨论：低
```

---

## 7. 图谱的输出用途

Knowledge Graph 输出给：

- Reasoning Engine。
- Exposure Engine。
- Explanation Service。
- Web Dashboard。
- Validation Engine。

典型输出：

```text
实体邻居
多跳路径
关系权重
证据列表
路径置信度
候选股票集合
```

---

## 8. 图谱与 YAML 的关系

YAML 仍然保留，但定位变化。

V1：

```text
YAML = 运行规则
```

V2：

```text
YAML = 图谱种子数据
```

YAML 中的人工规则应通过 loader 写入图谱，并标记 source_type 为 `yaml_seed`。

---

## 9. 图谱与 LLM 的关系

LLM 不是图谱本身。

LLM 负责生成候选知识：

```text
Evidence Text
  ↓
LLM Extraction
  ↓
Candidate Entity / Candidate Relation
```

正式图谱只接受经过校验或审核的关系。

---

## 10. 图谱与验证闭环的关系

Validation Engine 会把市场表现回写到关系权重。

例如：

```text
六氟化钨 -> 中船特气
```

如果历史事件多次验证有效，关系权重提高。

如果多次无效，关系权重降低。

---

## 11. 结论

AStock V2 Knowledge Graph 的定位是：

```text
长期产业知识记忆层
```

它不直接做投资决策，而是为事件推理、股票暴露度、解释系统和验证闭环提供稳定的结构化知识基础。