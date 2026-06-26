# 04 Data Flow

> 本文档描述 AStock V2 中数据从采集、证据、图谱、推理到展示的完整流转过程。

---

## 1. 总体数据流

AStock V2 的核心数据流如下：

```text
Raw Data
  ↓
Evidence
  ↓
Candidate Knowledge
  ↓
Knowledge Graph
  ↓
Event Reasoning
  ↓
Exposure Result
  ↓
Score Result
  ↓
Validation Result
  ↓
API / Web
```

---

## 2. Raw Data Flow

原始数据来自多个来源：

```text
AKShare
巨潮公告
RSS 新闻
年报 / 招股书
公司官网
互动易
招聘 / 专利
```

Raw Data 必须保留原文或原始结构，避免在采集阶段丢失信息。

---

## 3. Evidence Flow

Raw Data 进入 Evidence Collector 后，转换为标准 Evidence。

```text
raw_news
raw_announcement
raw_pdf_text
raw_website_text
  ↓
evidence
```

Evidence 记录来源、时间、标题、正文、相关公司和采集时间。

Evidence 是所有后续关系的可追溯来源。

---

## 4. Extraction Flow

Extraction Layer 从 Evidence 中抽取候选结构。

```text
Evidence
  ↓
Rule Extractor / LLM Extractor
  ↓
Candidate Entity
Candidate Relation
Candidate Event
```

候选结果不会直接进入正式图谱。

候选结果需要经过置信度校验、来源校验和必要的人工审核。

---

## 5. Knowledge Graph Flow

通过审核的候选知识写入 Knowledge Graph。

```text
Candidate Relation
  ↓
Review / Merge / Deduplicate
  ↓
KG Entity / KG Relation
```

图谱中每条关系都应保留：

- 来源证据。
- 置信度。
- 权重。
- 创建时间。
- 更新时间。
- 状态。

---

## 6. Event Flow

新闻、公告或用户输入可以生成事件。

```text
News / Announcement / Manual Input
  ↓
Event Engine
  ↓
Structured Event
```

结构化事件示例：

```text
event_type = supply_shortage
target_entity = 六氟化钨
intensity = high
direction = positive_for_supplier
```

---

## 7. Reasoning Flow

Reasoning Engine 使用事件和图谱进行推理。

```text
Structured Event
  ↓
Find Target Entities
  ↓
Graph Traversal
  ↓
Find Related Companies / Stocks
  ↓
Calculate Path Weight
```

推理输出包括：

- 事件实体。
- 影响路径。
- 候选股票。
- 路径权重。
- 暴露度。

---

## 8. Scoring Flow

Scoring Engine 将推理结果与行情和舆情因子融合。

```text
Exposure Result
Trend Factor
Sentiment Factor
Volume Factor
Validation Factor
  ↓
Final Score
```

Score 必须保留 breakdown，便于前端解释。

---

## 9. Validation Flow

事件发生后，Validation Engine 记录市场表现。

```text
Event Result
  ↓
Wait T+1 / T+3 / T+5 / T+10
  ↓
Calculate Return
  ↓
Calculate Excess Return
  ↓
Update Validation Result
```

验证结果可用于：

- 更新事件类型权重。
- 更新关系权重。
- 更新股票暴露度置信度。
- 标记噪音事件。

---

## 10. API Flow

API 层从标准服务读取结果。

```text
Frontend Request
  ↓
API Layer
  ↓
Service Layer
  ↓
Database / Graph Query
  ↓
Response DTO
```

API 不应直接读取 Raw Data。

API 不应直接运行 LLM。

---

## 11. Web Flow

Web 展示依赖 API 输出。

典型页面数据流：

```text
Event Page
  ↓
/api/events/{id}
/api/events/{id}/paths
/api/events/{id}/stocks
/api/events/{id}/validation
```

```text
Stock Page
  ↓
/api/stocks/{code}
/api/stocks/{code}/knowledge
/api/stocks/{code}/events
/api/stocks/{code}/explain
```

---

## 12. 数据生命周期

### 12.1 Raw Data

长期保留，但可归档。

### 12.2 Evidence

长期保留，是可追溯依据。

### 12.3 Candidate Knowledge

保留审核状态，可定期清理无效候选。

### 12.4 Knowledge Graph

长期保留，持续更新。

### 12.5 Reasoning Result

按事件保留，用于复盘。

### 12.6 Validation Result

长期保留，用于模型校准。

---

## 13. 数据流设计原则

1. Raw Data 不直接进入推理。
2. Evidence 必须可追溯。
3. Candidate Knowledge 不直接等于正式知识。
4. Graph 只保存长期关系。
5. Reasoning Result 必须保存路径。
6. Score Result 必须保存 breakdown。
7. Validation Result 必须可反向校准权重。

---

## 14. 结论

V2 的数据流核心是：

```text
先保留证据
再形成知识
再执行推理
再记录验证
最后展示解释
```

这个顺序保证系统不是简单关键词匹配，而是可追溯、可验证、可持续迭代的事件推理系统。