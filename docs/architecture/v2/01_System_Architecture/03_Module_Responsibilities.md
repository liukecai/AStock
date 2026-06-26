# 03 Module Responsibilities

> 本文档定义 AStock V2 各核心模块的职责边界。

---

## 1. 模块设计目标

V2 模块划分的目标是避免以下问题：

- 数据采集模块承担业务判断。
- LLM 直接参与最终评分。
- 图谱层混入实时行情逻辑。
- API 层直接读取原始数据源。
- Web 层承担推理逻辑。

每个模块必须职责单一、输入输出明确。

---

## 2. Data Source Adapter

### 职责

负责连接外部数据源。

### 输入

- 数据源配置。
- 股票代码。
- 日期范围。
- URL 或 API 参数。

### 输出

- 原始文本。
- 原始 JSON。
- 原始表格。
- 原始 PDF 元数据。

### 不负责

- 不做实体抽取。
- 不做事件分类。
- 不做股票影响判断。
- 不写入图谱正式表。

---

## 3. Evidence Collector

### 职责

负责将原始数据转为标准证据对象。

### 输入

- 原始新闻。
- 原始公告。
- 年报文本。
- 招股书文本。
- 官网产品页文本。

### 输出

标准 Evidence：

```text
evidence_id
source_type
source_title
source_url
raw_text
related_company
related_stock_code
published_at
collected_at
```

### 不负责

- 不判断事件影响方向。
- 不直接修改图谱关系。
- 不生成最终信号。

---

## 4. Extraction Service

### 职责

负责从 Evidence 中抽取结构化候选知识。

### 抽取类型

- 公司产品。
- 公司原材料。
- 公司客户。
- 公司供应商。
- 下游应用。
- 事件类型。
- 受影响商品。
- 受影响行业。

### 输出

Candidate Relation：

```text
subject
predicate
object
evidence_id
confidence
extractor_type
status
```

### 不负责

- 不直接进入正式图谱。
- 不计算最终评分。
- 不覆盖人工确认关系。

---

## 5. Knowledge Graph Service

### 职责

负责维护正式产业知识图谱。

### 主要能力

- 创建实体。
- 合并实体。
- 创建关系。
- 更新关系权重。
- 查询邻居节点。
- 查询多跳路径。
- 追踪证据来源。

### 输入

- 已审核候选关系。
- YAML 种子数据。
- 人工维护关系。
- 验证结果回写。

### 输出

- 实体集合。
- 关系集合。
- 路径集合。
- 关系置信度。

### 不负责

- 不采集外部数据。
- 不调用 LLM。
- 不做行情计算。

---

## 6. Event Engine

### 职责

负责将新闻或公告内容标准化为事件。

### 输入

- 新闻标题。
- 新闻正文。
- 公告标题。
- 公告摘要。
- 手动输入事件文本。

### 输出

结构化 Event：

```text
event_id
event_type
subtype
entities
intensity
direction
time_window
source_evidence_id
```

### 不负责

- 不计算股票暴露度。
- 不写入长期图谱。
- 不生成前端展示文本。

---

## 7. Reasoning Engine

### 职责

负责基于事件和图谱进行路径推理。

### 输入

- 结构化事件。
- 图谱实体。
- 图谱关系。
- 推理参数。

### 输出

- 受影响实体。
- 传播路径。
- 候选股票。
- 路径权重。
- 暴露度。

### 不负责

- 不采集数据。
- 不直接调用外部新闻源。
- 不决定前端样式。

---

## 8. Exposure Engine

### 职责

负责计算股票对事件、商品、行业或产业链节点的暴露度。

### 暴露度来源

- 图谱路径长度。
- 关系权重。
- 证据置信度。
- 公司主营相关度。
- 历史事件表现。

### 输出

```text
stock_code
entity_id
event_id
exposure_score
confidence
reason_path
```

---

## 9. Scoring Engine

### 职责

负责综合多个因子形成最终分析分数。

### 输入因子

- Exposure Score。
- Trend Score。
- Sentiment Score。
- Volume Score。
- Event Intensity。
- Validation Score。

### 输出

```text
stock_code
event_id
final_score
score_breakdown
rank
```

### 不负责

- 不解释路径。
- 不维护图谱。
- 不采集行情。

---

## 10. Validation Engine

### 职责

负责记录和评估事件发生后的市场表现。

### 验证窗口

- T+1。
- T+3。
- T+5。
- T+10。

### 输出

- 绝对收益。
- 相对指数超额收益。
- 相对行业超额收益。
- 命中率。
- 平均表现。
- 关系权重调整建议。

---

## 11. Explanation Service

### 职责

负责将推理结果转化为用户可理解的解释。

### 输出示例

```text
该股票与事件相关，是因为公司产品涉及六氟化钨，六氟化钨属于电子特气，电子特气属于半导体材料链。本关系由招股书和官网产品目录支持。
```

### 不负责

- 不改变推理结果。
- 不新增图谱关系。
- 不生成行情数据。

---

## 12. API Service

### 职责

负责将后端能力暴露给前端。

### API 类型

- Graph API。
- Event API。
- Reasoning API。
- Stock Explain API。
- Validation API。
- Job API。

### 不负责

- 不直接运行批处理任务。
- 不直接访问外部数据源。
- 不包含业务推理逻辑。

---

## 13. Web Frontend

### 职责

负责展示系统结果。

### 重点页面

- 事件看板。
- 个股详情。
- 产业链路径。
- 公司知识卡。
- 验证结果。

### 不负责

- 不执行推理。
- 不计算分数。
- 不直接访问数据库。

---

## 14. 模块边界总结

```text
采集归采集
证据归证据
抽取归抽取
图谱归图谱
推理归推理
评分归评分
验证归验证
展示归展示
```

清晰的职责边界是 V2 可维护性的核心。