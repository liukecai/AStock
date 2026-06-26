# 08 Implementation Roadmap

> AStock V2 实施路线图。
>
> 将 V2 架构拆解为六个可执行、可验收、可持续迭代的开发阶段。
>
> 前置阅读：[01_System_Architecture.md](./01_System_Architecture.md) 第 2~3 节（V2 设计目标与架构分层）。

---

## 1. 实施原则

1. 先数据模型，后推理逻辑。
2. 先 YAML seed，后 LLM 自动抽取。
3. 先离线计算，后在线展示。
4. 先保存路径，后优化评分。
5. 先可解释，后复杂算法。
6. 每个阶段必须有可验收产物，且不破坏 V1 现有功能。

### 阶段总览

```text
Phase 1：KG Schema 与基础表          ← 数据基础
Phase 2：YAML 规则迁移到图谱          ← 知识初始化
Phase 3：Reasoning Engine MVP         ← 核心推理
Phase 4：LLM 抽取候选关系             ← 自动扩充
Phase 5：Validation Loop 验证闭环     ← 结果验证
Phase 6：Web Explainability 前端解释层 ← 产品展示
```

### 非目标

V2 第一轮实施不包含：自动交易、高频数据、完整 Neo4j 迁移、多 Agent 自动维护图谱、完全无人审核的 LLM 入库。

---

## 2. Phase 1：KG Schema 与基础表

**目标**：先不改变现有选股逻辑，只新增图谱数据模型。

### 交付物

| 类型 | 内容 |
|---|---|
| 数据库表 | `kg_entities` / `kg_relations` / `evidence` / `relation_evidence` / `candidate_entities` / `candidate_relations` |
| ORM 模型 | SQLAlchemy 模型，仅面向 PostgreSQL，彻底放弃 SQLite 兼容 |
| 数据库迁移 | 强制引入 Alembic 初始化数据库结构 |
| 基础服务 | Entity CRUD / Relation CRUD / Evidence CRUD |
| 测试 | 实体创建、关系创建、证据绑定的单元测试 |

### 验收标准

1. 能创建实体并按名称/别名查询。
2. 能创建关系并查询邻居。
3. 能绑定证据到关系。
4. **必须通过 Alembic 生成并执行初始建表脚本。**
5. 不影响 V1 现有功能。

→ 表结构详见 [05_Database_Design.md](./05_Database_Design.md)。

---

## 3. Phase 2：YAML 规则迁移

**目标**：将现有 commodity / event / stock mapping 从 YAML 迁入图谱。

### 交付物

| 类型 | 内容 |
|---|---|
| 迁移脚本 | `yaml_to_kg_loader.py`：解析 YAML → 归一化实体 → Upsert Entity → Upsert Relation → 标记 `source_type = yaml_seed`。<br>**明确映射规则**：在迁移前小幅重构 YAML 模板，或在脚本中硬编码将 `exact_stocks` 映射为 `produces`，`downstream_sectors` 映射为 `used_in` 等。 |
| 关系增强 | 关系置信度字段和来源字段填充 |
| 验证 | 迁移前后规则覆盖度对比 |

### 验收标准

1. 能从 YAML 加载实体和关系到图谱。
2. 加载后可通过 API 查询图谱。
3. 重复加载幂等（不产生重复实体/关系）。
4. 所有关系标记 `source_type = yaml_seed`。
5. 不影响 V1 现有事件系统。

→ 图谱构建详见 [02_Knowledge_Graph_Design.md](./02_Knowledge_Graph_Design.md) 第 5 节。

---

## 4. Phase 3：Reasoning Engine MVP

**目标**：实现事件到股票的图谱路径搜索。

### 交付物

| 类型 | 内容 |
|---|---|
| 推理模块 | 拆解现有 `event_engine.py` 臃肿代码，严格分离为 `event_extractor.py`, `graph_querier.py`, `exposure_calculator.py`，杜绝上帝类 (God Class) |
| 核心方法 | `find_impacted_stocks(event)` / `explain_stock_impact(event, stock)` |
| 事件引擎 | Event Extraction + Event Normalization |
| 暴露度 | `exposure_calculator.py` |
| 评分 | `scoring_engine.py`（初版多因子融合） |
| 数据库表 | `event_instances` / `event_impacts` / `reasoning_paths` / `stock_exposures` / `stock_event_scores` |

### 验收标准

1. 输入一个事件文本，能输出候选股票列表。
2. 每只候选股票有推理路径。
3. 路径含节点、关系、权重、置信度。
4. 暴露度可拆解。
5. 分数保留 breakdown。
6. 能通过 API 查询推理结果。

→ 推理设计详见 [03_Reasoning_Engine.md](./03_Reasoning_Engine.md)。

---

## 5. Phase 4：LLM 抽取候选关系

**目标**：让 LLM 从公告、年报、招股书、新闻中提取结构化候选关系。

### 交付物

| 类型 | 内容 |
|---|---|
| 抽取服务 | `llm_extract_company_profile()` / `llm_extract_event()` |
| Prompt 库 | 年报/招股书/公告/新闻 Prompt 模板（版本化管理） |
| JSON Schema | 输出格式校验 |
| 候选层 | `candidate_relations` 表写入 + 审核流程 |
| 审核接口 | 人工审核候选关系的 API |

### 验收标准

1. 能从一篇年报抽取产品、材料、下游行业。
2. 抽取结果为合法 JSON 且包含 `evidence_text`。
3. 结果写入 `candidate_relations`。
4. 高质量来源可自动通过。
5. 低质量来源进入审核队列。
6. 不影响正式图谱稳定性。

→ LLM 集成详见 [04_LLM_Integration.md](./04_LLM_Integration.md)。

---

## 6. Phase 5：Validation Loop

**目标**：建立事件推理结果的市场验证闭环。

### 交付物

| 类型 | 内容 |
|---|---|
| 验证引擎 | `validation_engine.py` / `return_calculator.py` / `benchmark_service.py` |
| 聚合服务 | `validation_summary_service.py` |
| 数据库表 | `event_validation_results` / `validation_summary` |
| 回写机制 | 验证结果回写 event_type_weight / relation_weight |

### 验收标准

1. 能读取事件推理结果并定位 T0 交易日。
2. 能计算 T+1 / T+3 / T+5 / T+10 多窗口收益。
3. 能计算相对指数和行业的超额收益。
4. 能写入验证结果并生成聚合统计。
5. 停牌/缺失数据有明确 status 标记。
6. Web 或 API 能查询验证结果。

→ 验证设计详见 [03_Reasoning_Engine.md](./03_Reasoning_Engine.md) 第 7 节。

---

## 7. Phase 6：Web Explainability

**目标**：实现 V2 Web 解释层，展示事件、路径、证据、分数和验证结果。

### 交付物

| 类型 | 内容 |
|---|---|
| 前端模块 | EventDashboard / EventDetail / ReasonPathGraph / StockExplainPanel / EvidenceList / ValidationPanel / CompanyKnowledgeCard / JobMonitor |
| API Client | graphApi / eventApi / stockExplainApi / validationApi / jobApi |
| UI 状态 | loading / empty / error / low_confidence / stale_data / missing_data / pending_review |

### 验收标准

1. 能查看事件列表和事件详情。
2. 能查看候选标的和推理路径图。
3. 能查看证据来源和分数拆解。
4. 能查看验证统计。
5. 能查看任务状态。
6. 低置信/数据缺失/过期有明确提示。

→ Web 设计详见 [07_Web_Design.md](./07_Web_Design.md)。

---

## 8. 架构决策记录（ADR）

### ADR-001：采用分阶段增量实施

六阶段增量实施，风险可控，每阶段可验收，不破坏 V1。

### ADR-002：先图谱 Schema，后推理引擎

Reasoning Engine 依赖稳定的实体和关系模型，先完成基础表。

### ADR-003：YAML 作为图谱种子数据

通过 `yaml_to_kg_loader` 复用已有规则资产，快速初始化图谱。

### ADR-004：抽取能力晚于图谱和推理 MVP

避免在图谱模型未稳定时引入大量噪音。先手工 seed，后自动抽取。

### ADR-005：验证闭环在前端大规模展示前完成

前端展示更可信，支持分数校准。

### ADR-006：Web 最后集成完整解释链路

Web 依赖图谱、推理、证据和验证结果，作为第六阶段整合前面产物。
