# AStock V2 Architecture

> A股产业知识图谱（Knowledge Graph）+ 事件推理引擎（Reasoning Engine）升级设计文档总览。
>
> 本目录用于指导 AStock 从 V1 的“行情 + 舆情 + 规则选股系统”，升级为 V2 的“产业知识图谱 + 事件推理 + 影响验证闭环系统”。

---

## 1. V2 升级目标

AStock V1 已经具备基础行情、新闻舆情、公告聚合、趋势评分、事件映射和 Web 展示能力。V2 的核心升级目标是将系统从“规则驱动的选股看板”升级为：

```text
事件输入
  ↓
事件结构化
  ↓
商品 / 材料 / 技术 / 行业映射
  ↓
产业链知识图谱推理
  ↓
股票暴露度计算
  ↓
趋势、舆情、事件多因子融合
  ↓
收益验证与权重校准
  ↓
可解释化 Web 展示
```

V2 不追求让大模型直接给出投资结论，而是让大模型参与信息抽取和关系补全，让知识图谱负责稳定推理，让行情数据负责验证关系是否真的有效。

---

## 2. 核心设计原则

### 2.1 规则库不是废弃，而是升级为确定性底座

现有 YAML 规则库继续保留，作为高置信度、可审计、可回滚的确定性基础。

```text
YAML 规则库
  ↓
高置信度实体与关系
  ↓
写入 Knowledge Graph
```

### 2.2 LLM 不直接选股，只做结构化抽取与候选关系生成

LLM 的职责：

- 从年报、招股书、公告、官网产品目录中抽取产品、原材料、客户、下游行业。
- 从新闻中抽取事件类型、影响商品、影响方向、强度。
- 对未知产业链节点生成候选映射。
- 为前端生成“为什么这只股票受影响”的解释文本。

LLM 的输出必须进入候选池，经过置信度、来源、规则校验、市场验证后，才能进入正式图谱。

### 2.3 图谱存储长期知识，行情验证短期有效性

知识图谱解决：

```text
公司涉及什么产品？
产品属于哪条产业链？
事件影响哪些商品、材料、行业？
股票与事件之间的路径是什么？
```

行情验证解决：

```text
这条关系过去是否真的带来超额收益？
不同事件类型的有效窗口是多少？
哪些关系只是概念噪音？
```

---

## 3. 文档结构

本目录建议拆分为以下文档：

```text
docs/architecture/v2/
├── README.md
├── 01_System_Architecture.md
├── 02_Knowledge_Graph_Design.md
├── 03_Reasoning_Engine.md
├── 04_LLM_Integration.md
├── 05_Database_Design.md
├── 06_API_Design.md
├── 07_Web_Design.md
├── 08_Implementation_Roadmap.md
└── 09_Future_V3.md
```

---

## 4. 各文档职责

### 4.1 `01_System_Architecture.md`

描述 V2 总体架构，包括：

- 系统分层
- 数据流
- 模块边界
- V1 到 V2 的改造关系
- 离线任务与在线服务的职责划分

重点回答：

> AStock V2 的整体系统如何运转？

---

### 4.2 `02_Knowledge_Graph_Design.md`

描述 A股产业知识图谱设计，包括：

- Entity 类型
- Relation 类型
- 置信度模型
- 来源追踪
- YAML 到图谱的迁移方式
- 公司、产品、材料、商品、行业、概念、事件之间的关系建模

重点回答：

> 如何确定一只股票涉及某个供应链内容？

---

### 4.3 `03_Reasoning_Engine.md`

描述事件推理引擎，包括：

- 事件识别
- 事件标准化
- 图谱路径搜索
- 产业链传播
- 股票暴露度计算
- 事件影响方向判断
- 综合评分模型

重点回答：

> 当出现“六氟化钨紧缺”“中东冲突”“锂价上涨”这类事件时，系统如何推理到相关股票？

---

### 4.4 `04_LLM_Integration.md`

描述大模型接入方式，包括：

- 年报解析 Prompt
- 招股书解析 Prompt
- 公告解析 Prompt
- 官网产品目录解析 Prompt
- 新闻事件抽取 Prompt
- JSON 输出规范
- LLM 候选结果入库流程
- 幻觉控制与人工审核机制

重点回答：

> 大模型如何帮助自动构建产业链知识，而不是直接胡乱推荐股票？

---

### 4.5 `05_Database_Design.md`

描述数据库设计，包括：

- `kg_entities`
- `kg_relations`
- `company_profiles`
- `company_products`
- `event_instances`
- `event_impacts`
- `stock_exposures`
- `event_validation_results`
- 索引设计
- 迁移策略

重点回答：

> 图谱、事件、暴露度、验证结果如何落库？

---

### 4.6 `06_API_Design.md`

描述 API 设计，包括：

- 图谱查询 API
- 事件推理 API
- 个股解释 API
- 事件验证 API
- 后台任务 API

重点回答：

> 前端和外部系统如何调用 V2 能力？

---

### 4.7 `07_Web_Design.md`

描述 Web 产品设计，包括：

- Event Dashboard
- Supply Chain Explorer
- Company Knowledge Card
- Why This Stock 解释卡片
- Event Impact Path 事件传播路径图
- Validation Panel 收益验证面板

重点回答：

> 如何把“事件 → 产业链 → 股票”的推理过程展示给用户？

---

### 4.8 `08_Implementation_Roadmap.md`

描述开发路线，包括：

- Sprint 1：图谱最小数据模型
- Sprint 2：YAML 规则库迁移
- Sprint 3：事件推理引擎
- Sprint 4：LLM 抽取管道
- Sprint 5：收益验证闭环
- Sprint 6：前端解释页

重点回答：

> 如何从当前 V1 平滑升级到 V2？

---

### 4.9 `09_Future_V3.md`

描述未来演进方向，包括：

- PostgreSQL + pgvector
- Neo4j
- GraphRAG
- Agent 自动维护图谱
- 事件权重自学习
- 多市场扩展

重点回答：

> V2 之后如何继续演进为真正的市场事件推演平台？

---

## 5. V2 核心模块

### 5.1 Knowledge Graph

知识图谱保存长期稳定关系：

```text
Company
  ↓ produces
Product
  ↓ belongs_to
Material
  ↓ belongs_to
Commodity
  ↓ impacts
Industry
  ↓ contains
Sector
```

示例：

```text
中船特气
  ↓ produces
六氟化钨
  ↓ belongs_to
电子特气
  ↓ belongs_to
半导体材料
  ↓ used_in
半导体制造
```

---

### 5.2 Reasoning Engine

推理引擎将事件映射到股票：

```text
六氟化钨紧缺
  ↓ event_type = supply_shortage
六氟化钨
  ↓ graph traversal
电子特气
  ↓ graph traversal
中船特气
  ↓ exposure scoring
候选股票
```

输出结构：

```json
{
  "event": "六氟化钨供应紧张",
  "event_type": "supply_shortage",
  "affected_entities": ["六氟化钨", "电子特气", "半导体材料"],
  "candidate_stocks": [
    {
      "code": "688146",
      "name": "中船特气",
      "exposure_score": 0.82,
      "reason_path": ["六氟化钨", "电子特气", "中船特气"],
      "confidence": 0.78
    }
  ]
}
```

---

### 5.3 Validation Loop

事件验证闭环用于确认推理是否有效：

```text
事件发生
  ↓
系统推理候选股票
  ↓
记录 T+1 / T+3 / T+5 / T+10 收益
  ↓
计算超额收益、胜率、平均收益
  ↓
更新关系权重和事件权重
```

这一步让系统从“规则判断”升级为“可学习的事件库”。

---

## 6. 数据源优先级

### 6.1 高置信度来源

- 年报
- 招股说明书
- 巨潮公告
- 公司官网产品目录

### 6.2 中置信度来源

- 互动易 / 上证 e 互动
- 新闻媒体
- RSS 聚合源
- 公司公众号

### 6.3 低置信度但有发现价值的来源

- 股吧
- 雪球讨论
- 招聘信息
- 非正式传闻

---

## 7. V1 到 V2 的最小升级路径

### Phase 1：图谱数据模型

目标：先不改变现有选股逻辑，只新增图谱表。

交付：

- `kg_entities`
- `kg_relations`
- `stock_exposures`
- YAML seed 脚本

---

### Phase 2：YAML 规则库迁移

目标：将现有 commodity / event / stock mapping 从硬编码或 YAML 迁入图谱。

交付：

- `yaml_to_kg_loader.py`
- 关系置信度字段
- 来源字段

---

### Phase 3：事件推理引擎

目标：实现事件到股票的图谱路径搜索。

交付：

- `reasoning_engine.py`
- `find_impacted_stocks(event)`
- `explain_stock_impact(event, stock)`

---

### Phase 4：LLM 抽取管道

目标：让 LLM 从公告、年报、招股书、新闻中提取结构化候选关系。

交付：

- `llm_extract_company_profile()`
- `llm_extract_event()`
- `candidate_relations` 表
- 人工审核接口

---

### Phase 5：收益验证闭环

目标：验证事件推理是否真的产生市场反应。

交付：

- `event_validation_results`
- T+1 / T+3 / T+5 收益计算
- 事件胜率统计
- 关系权重回写

---

### Phase 6：Web 解释层

目标：让用户看懂为什么某只股票被推荐。

交付：

- Why This Stock 卡片
- Event Impact Path 图
- Company Knowledge Card
- Validation Panel

---

## 8. V2 成功标准

V2 完成后，系统应能回答以下问题：

1. 某只股票为什么和某个事件相关？
2. 某个事件会影响哪些商品、材料、行业、股票？
3. 某条产业链关系来自哪里，置信度多少？
4. 同类事件过去是否真的带来超额收益？
5. 哪些关系是规则库确认的，哪些是 LLM 候选的，哪些经过市场验证？
6. 用户能否在 Web 页面看到完整推理路径？

---

## 9. 非目标

V2 暂不追求：

- 自动交易
- 实盘下单
- 高频分钟级事件交易
- 完全无人审核的 LLM 图谱写入
- 对所有传闻直接生成买卖建议

V2 的重点是：

> 建立稳定、可解释、可验证、可持续积累的 A股产业知识图谱与事件推理能力。

---

## 10. 总结

AStock V2 的核心不是增加更多技术指标，而是建立一套能够持续积累产业知识和事件经验的系统。

最终形态：

```text
LLM 负责理解和抽取
Knowledge Graph 负责记忆和推理
行情数据负责验证和校准
Web 前端负责解释和展示
```

这四层组合起来，才能真正实现：

> 供应链扰动 → 资源重估 → 板块定价重构 → 股票影响推理。
