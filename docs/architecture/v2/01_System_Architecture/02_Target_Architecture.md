# 02 Target Architecture

> 本文档定义 AStock V2 的目标系统架构。

---

## 1. 目标架构概览

AStock V2 的目标架构由九层组成：

```text
Data Sources
  ↓
Evidence Collector
  ↓
Extraction Layer
  ↓
Candidate Knowledge Layer
  ↓
Knowledge Graph
  ↓
Reasoning Engine
  ↓
Scoring & Validation
  ↓
API Layer
  ↓
Web Dashboard
```

每一层只负责明确职责，避免 V1 中规则、数据、推理、展示混杂在一起。

---

## 2. Data Sources

数据源负责提供原始信息。

主要来源包括：

- 行情数据。
- 新闻数据。
- RSS 数据。
- 巨潮公告。
- 年报。
- 招股说明书。
- 公司官网产品目录。
- 互动易和上证 e 互动。
- 招聘信息。
- 专利信息。

数据源层不做复杂判断，只负责获取和归档原始数据。

---

## 3. Evidence Collector

Evidence Collector 负责把原始数据变成可追踪证据。

证据字段至少包括：

```text
evidence_id
source_type
source_url
source_title
published_at
collected_at
raw_text
related_company
related_stock_code
confidence_base
```

证据本身不等于知识。

证据只是说明：某个来源中出现了某些事实描述。

---

## 4. Extraction Layer

Extraction Layer 负责从证据中抽取结构化候选信息。

抽取方式包括：

- 规则抽取。
- 关键词抽取。
- LLM 抽取。
- 人工录入。

输出示例：

```json
{
  "subject": "中船特气",
  "predicate": "produces",
  "object": "六氟化钨",
  "evidence_id": "evi_001",
  "confidence": 0.86
}
```

这一层产出的是候选关系，不一定直接进入正式图谱。

---

## 5. Candidate Knowledge Layer

候选知识层用于暂存未确认关系。

候选关系需要经过：

- 来源可信度评估。
- 多证据合并。
- 规则校验。
- 人工审核或自动阈值审核。
- 历史验证结果校准。

只有满足条件的关系才进入 Knowledge Graph。

---

## 6. Knowledge Graph

知识图谱是 V2 的长期记忆层。

图谱负责存储稳定关系：

```text
Company -> Product
Product -> Material
Material -> Commodity
Commodity -> Industry
Industry -> Sector
Event -> Commodity
Event -> Industry
```

图谱关系必须支持：

- 方向。
- 权重。
- 置信度。
- 证据来源。
- 更新时间。
- 状态。

---

## 7. Reasoning Engine

Reasoning Engine 负责事件传播推理。

输入：

```text
事件文本或结构化事件
```

输出：

```text
影响实体
影响路径
候选股票
暴露度
解释文本
```

示例：

```text
六氟化钨供应紧张
  ↓
六氟化钨
  ↓
电子特气
  ↓
半导体材料
  ↓
中船特气
```

推理引擎只负责计算影响路径和暴露度，不直接做最终投资判断。

---

## 8. Scoring & Validation

Scoring Engine 负责综合评分。

评分来源包括：

- 事件强度。
- 图谱暴露度。
- 证据置信度。
- 趋势评分。
- 舆情评分。
- 成交量变化。
- 历史验证表现。

Validation Engine 负责在事件发生后计算真实市场表现：

- T+1。
- T+3。
- T+5。
- T+10。
- 相对指数表现。
- 相对行业表现。

---

## 9. API Layer

API Layer 负责对外提供 V2 能力。

主要 API 类型：

- 图谱查询 API。
- 事件推理 API。
- 股票解释 API。
- 证据查询 API。
- 验证结果 API。
- 任务状态 API。

API 层不得直接访问原始数据源，应通过服务层访问标准化数据。

---

## 10. Web Dashboard

Web 层负责展示推理结果。

核心页面包括：

- Event Dashboard。
- Supply Chain Explorer。
- Company Knowledge Card。
- Why This Stock。
- Event Impact Path。
- Validation Panel。

Web 的重点不是只展示分数，而是展示完整因果链。

---

## 11. 架构分层边界

### 数据源层

只负责采集。

### 证据层

只负责保留可追溯事实。

### 抽取层

只负责把文本转为候选结构。

### 图谱层

只负责长期关系存储。

### 推理层

只负责路径搜索和影响传播。

### 评分层

只负责综合评分和排序。

### 验证层

只负责结果反馈和权重校准。

### Web 层

只负责解释和展示。

---

## 12. 目标架构结论

AStock V2 的目标架构不是一个更复杂的规则系统，而是一个分层清晰的事件推理平台。

核心思想是：

```text
证据可追溯
关系可沉淀
推理可解释
结果可验证
权重可校准
```

这也是 V2 与 V1 的本质区别。