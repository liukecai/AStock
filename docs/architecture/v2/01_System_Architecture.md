# 01 System Architecture

> AStock V2 总体系统架构。
>
> 本文档定义 V2 的架构目标、V1 现状与升级动因、目标架构分层、模块职责、数据流、运行时设计、部署演进和关键架构决策。

---

## 1. V1 现状与升级动因

### 1.1 V1 已有能力

AStock V1 已从脚本演进为可运行的量化研究平台，具备：

| 能力 | 说明 |
|---|---|
| 行情采集 | AKShare 多来源 A 股日线数据 |
| 趋势分析 | 均线结构、价格斜率、趋势评分、成交量变化 |
| 舆情聚合 | RSS 新闻、巨潮公告接入与情绪判断 |
| 事件映射 | 事件到商品、商品到股票的初步规则映射 |
| Web 展示 | 股票列表、详情页、Dashboard |
| Docker 部署 | Docker Compose 单机部署 |

V1 已完成 MVP 阶段目标。

### 1.2 V1 核心问题

| 问题 | 说明 |
|---|---|
| 规则膨胀 | 事件类型增加后，YAML/硬编码规则快速膨胀，难以审计和复用 |
| 缺少统一知识结构 | 映射面向具体事件，产业链关系无法跨事件复用 |
| 缺少证据追踪 | 无法知道一条关系来自年报、招股书还是新闻 |
| 缺少验证闭环 | 无法区分有效关系和噪音关系 |
| 可解释性不足 | 只输出股票列表，用户无法理解推理过程 |

### 1.3 为什么不能继续堆规则

规则系统适合 MVP，但事件驱动阶段会遇到扩展瓶颈：

1. 同一商品可能影响多个行业。
2. 同一公司可能涉及多个产品。
3. 同一事件可能通过多个路径影响股票。
4. 同一关系可能来自多个证据源。
5. 同一事件类型在不同市场环境下影响不同。

### 1.4 V1 可复用资产

以下能力继续作为 V2 基础设施复用：

- 行情、新闻、公告采集
- 调度系统（APScheduler）
- Web 基础框架与股票详情页
- 趋势评分（作为 V2 Scoring Engine 子因子）
- 事件 YAML（作为图谱种子数据）

---

## 2. V2 设计目标与原则

### 2.1 核心链路变化

```text
V1：行情 + 舆情 + 规则映射 → 趋势/舆情/事件评分 → 股票列表
V2：Evidence → Knowledge Graph → Reasoning Engine → Exposure / Score → Validation → Explainable Web
```

V2 的核心输出不再只是股票列表，而是事件影响路径 + 股票暴露度 + 证据来源 + 历史验证结果。

### 2.2 设计原则

| 原则 | 说明 |
|---|---|
| Evidence First | 任何图谱关系必须绑定可追溯证据，无证据只能作为候选 |
| LLM as Extractor | LLM 负责抽取和候选生成，不做最终决策 → 详见 [04_LLM_Integration.md](./04_LLM_Integration.md) |
| Graph as Memory | 知识图谱作为长期记忆，沉淀产业链关系 → 详见 [02_Knowledge_Graph_Design.md](./02_Knowledge_Graph_Design.md) |
| Validation as Feedback | 行情验证反向校准事件权重和关系权重 |

---

## 3. 目标架构

AStock V2 目标架构由九层组成：

```text
Data Sources            ← 行情、新闻、年报、招股书、公告、官网、互动易
  ↓
Evidence Collector      ← 将原始数据转为标准证据对象
  ↓
Extraction Layer        ← 规则 / 关键词 / LLM / 人工抽取候选结构
  ↓
Candidate Knowledge     ← 候选关系暂存，经校验审核后入正式图谱
  ↓
Knowledge Graph         ← 长期产业知识记忆层
  ↓
Reasoning Engine        ← 事件传播推理 + 路径搜索 + 暴露度计算
  ↓
Scoring & Validation    ← 多因子评分 + 市场表现验证
  ↓
API Layer               ← 对外暴露 V2 能力
  ↓
Web Dashboard           ← 可解释化推理结果展示
```

每一层只负责明确职责，避免 V1 中规则、数据、推理、展示混杂。

---

## 4. 模块职责

### 4.1 模块总览

| 模块 | 职责 | 不负责 |
|---|---|---|
| Data Source Adapter | 连接外部数据源，输出原始文本/JSON/PDF | 不做实体抽取、事件分类、股票判断 |
| Evidence Collector | 将原始数据转为标准 Evidence | 不判断事件方向、不修改图谱 |
| Extraction Service | 从 Evidence 抽取候选实体/关系/事件 | 不直接进入正式图谱 |
| Knowledge Graph Service | 维护正式产业知识图谱 | 不采集数据、不调用 LLM |
| Event Engine | 将新闻/公告标准化为结构化事件 | 不计算暴露度、不写入长期图谱 |
| Reasoning Engine | 基于事件和图谱进行路径推理 | 不采集数据、不调用外部新闻源 |
| Exposure Engine | 计算股票对事件/商品/产业节点的暴露度 | — |
| Scoring Engine | 综合多因子形成最终分数 | 不解释路径、不维护图谱 |
| Validation Engine | 记录和评估事件后的市场表现 | — |
| Explanation Service | 将推理结果转化为可理解的解释 | 不改变推理结果 |
| API Service | 暴露后端能力给前端 | 不直接运行批处理、不访问外部数据源 |
| Web Frontend | 展示系统结果 | 不执行推理、不计算分数、不直接访问数据库 |

### 4.2 职责边界总结

```text
采集归采集 → 证据归证据 → 抽取归抽取 → 图谱归图谱
推理归推理 → 评分归评分 → 验证归验证 → 展示归展示
```

---

## 5. 数据流

### 5.1 总体数据流

```text
Raw Data → Evidence → Candidate Knowledge → Knowledge Graph
                                                  ↓
                    Event → Reasoning → Exposure → Score → Validation
                                                              ↓
                                                        API / Web
```

### 5.2 各阶段说明

| 阶段 | 输入 | 输出 | 关键约束 |
|---|---|---|---|
| Raw Data | 外部数据源 | 原始文本/JSON/PDF | 保留原文，不丢失信息 |
| Evidence | 原始数据 | 标准 Evidence 对象 | 记录来源、时间、标题、正文 |
| Extraction | Evidence | Candidate Entity/Relation/Event | 候选结果不直接进入正式图谱 |
| Knowledge Graph | 审核后的候选知识 | 实体/关系/路径/置信度 | 每条关系保留来源、置信度、权重、状态 |
| Event | 新闻/公告/手工输入 | 结构化 Event | event_type + target + intensity + direction |
| Reasoning | 结构化事件 + 图谱 | 影响路径 + 候选股票 + 暴露度 | 只负责路径搜索，不做最终判断 |
| Scoring | 暴露度 + 趋势 + 舆情 + 验证 | Final Score + Breakdown | 必须保留 breakdown |
| Validation | 事件结果 + 行情 | T+1/3/5/10 收益 + 超额收益 | 结果回写事件/关系权重 |

### 5.3 数据生命周期

| 数据 | 保留策略 |
|---|---|
| Raw Data | 长期保留，可归档 |
| Evidence | 长期保留，可追溯依据 |
| Candidate Knowledge | 保留审核状态，定期清理无效候选 |
| Knowledge Graph | 长期保留，持续更新 |
| Reasoning Result | 按事件保留，用于复盘 |
| Validation Result | 长期保留，用于校准 |

---

## 6. 运行时设计

### 6.1 离线与在线分离

```text
Offline：数据采集 / 证据构建 / LLM 抽取 / 图谱更新 / 批量推理 / 验证计算
Online ：API 查询 / Web 展示 / 用户交互 / 解释查询
```

在线服务只读取已落库结果，不执行 LLM 调用、PDF 解析、批量图谱更新等重型任务。

### 6.2 调度任务

V2 继续使用 APScheduler 作为第一阶段调度器。推荐任务：

```text
market_data_update / news_update / announcement_update / evidence_build
llm_extraction / kg_update / event_reasoning / validation_update / backup
```

每个任务记录名称、开始/结束时间、状态、错误信息、处理数量。

### 6.3 LLM 运行时

LLM 调用属于离线任务，正确链路为：

```text
离线任务 → LLM 抽取 → 候选关系入库 → 审核/校验 → 图谱更新 → 在线查询
```

错误链路：

```text
用户打开页面 → API → LLM → 返回结果    ← 禁止
```

### 6.4 事件推理模式

| 模式 | 场景 | 约束 |
|---|---|---|
| Batch Reasoning | 每天盘后批量处理新增事件 | 完整推理流程 |
| On-demand Reasoning | 用户手动输入事件文本 | 轻量图谱查询，不执行 LLM 抽取 |

### 6.5 运行时演进

```text
Phase 1：APScheduler + FastAPI 单体
Phase 2：拆出 Worker
Phase 3：引入 Redis Queue / Celery
Phase 4：LLM 抽取、图谱更新、验证计算独立服务
```

---

## 7. 部署架构

### 7.1 Phase 1（单机 Docker Compose）

```text
Docker Compose
├── backend     ← FastAPI + APScheduler + 离线任务
├── frontend    ← Web 页面
├── postgres    ← PostgreSQL（V2 标准存储底座）
└── nginx       ← 静态资源 + API 反向代理
```

### 7.2 Phase 2（API + Worker 拆分）

```text
Docker Compose
├── backend-api    ← 只负责在线查询
├── backend-worker ← 行情/新闻/抽取/图谱/推理/验证
├── frontend
├── postgres
├── redis          ← 任务队列 + 缓存
└── nginx
```

### 7.3 数据库演进

| 阶段 | 数据库 | 适合场景 |
|---|---|---|
| PostgreSQL | V2 标准存储底座，多任务写入、复杂索引、向量检索 | 必须使用 SQLAlchemy + Alembic 管理模型与迁移 |
| Neo4j | 图谱路径查询规模超过关系型能力时 | 部署成本高，第一阶段暂不强制 |

彻底抛弃 V1 中的裸写 SQL 和 SQLite，统一使用 SQLAlchemy ORM 和 Alembic，保障多跳图谱查询和多表关联的可维护性 → 详见 [05_Database_Design.md](./05_Database_Design.md)。

### 7.4 文件存储

```text
data/
├── raw/              ← 原始数据
├── evidence/         ← 证据文件
├── reports/          ← 年报/招股书 PDF
├── announcements/    ← 公告 PDF
├── extraction_outputs/
└── backups/
```

### 7.5 健康检查

```text
/health
/api/jobs/status
/api/system/version
```

---

## 8. 架构决策记录（ADR）

### ADR-001：V2 不推翻 V1，增量叠加

V2 采用增量升级：V1 基础设施 + Evidence Layer + Knowledge Graph + Reasoning Engine + Validation Loop + Explainability Layer。降低重构风险，保留已有功能，可阶段性交付。

### ADR-002：LLM 不作为最终决策模块

LLM 只负责抽取实体/关系/事件和生成候选知识。最终影响计算由 Knowledge Graph + Reasoning Engine + Market Validation 完成。降低幻觉风险，提高系统可审计性。

### ADR-003：抛弃 SQLite，强制 PostgreSQL 作为图谱底座

图谱数据存在大量自关联和复杂查询，继续维护兼容 SQLite 的裸写 SQL 是维护灾难。V2 强制统一使用 PostgreSQL 和 SQLAlchemy ORM（配合 Alembic）。在路径查询复杂度明显超载前，暂不强制引入 Neo4j。

### ADR-004：YAML 保留为种子知识来源

YAML 不废弃，通过 `yaml_to_kg_loader` 写入图谱，标记 `source_type = yaml_seed`，快速初始化图谱。

### ADR-005：验证闭环作为核心能力

V2 必须引入 Validation Engine，记录 T+1/T+3/T+5/T+10 表现和相对指数/行业表现，校准关系权重和事件权重。

### ADR-006：在线服务不执行重型任务

在线服务只查询已落库结果。重型任务（LLM 抽取、PDF 解析、图谱批量更新、验证计算）全部放入离线任务或 Worker。

### ADR-007：V2 输出解释路径

V2 核心输出包括：事件 + 影响实体 + 图谱路径 + 股票暴露度 + 证据来源 + 历史验证 + 分数拆解。

### ADR-008：目录式架构文档

各主题独立成文，便于 Code Review 和独立更新。
