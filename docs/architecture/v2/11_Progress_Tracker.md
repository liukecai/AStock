# 11 Progress Tracker

> AStock V2 开发进度整体追踪看板。
> 
> 本文档基于 [08_Implementation_Roadmap.md](./08_Implementation_Roadmap.md) 和 [10_Interaction_Layer_Design.md](./10_Interaction_Layer_Design.md) 提取的具体执行项，用于记录开发进度、待办事项和完成日期。

---

## 总体进度 (Overall Progress)

- [x] **Phase 1: KG Schema 与基础表** (100%)
- [x] **Phase 2: YAML 规则迁移** (100%)
- [x] **Phase 3: Reasoning Engine MVP** (100%)
- [ ] **Phase 4: LLM 抽取候选关系** (0%)
- [ ] **Phase 5: Validation Loop 验证闭环** (0%)
- [ ] **Phase 6: Web Explainability 前端解释层** (0%)
- [ ] **Phase 7: Interaction Layer 交互层** (0%)

---

## 阶段明细 (Phase Details)

### Phase 1: KG Schema 与基础表 
*状态: 已完成 (Completed)*

- [x] **基础架构搭建**
  - [x] 引入 `SQLAlchemy` 及 `Alembic`
  - [x] 彻底移除旧版 SQLite 原生 SQL 脚本
- [x] **ORM 模型定义**
  - [x] `kg_entities` (实体表)
  - [x] `kg_relations` (关系表，含 valid_from/valid_to)
  - [x] `evidence` / `relation_evidence` (证据表)
  - [x] `candidate_entities` / `candidate_relations` (候选表)
- [x] **基础 CRUD 服务**
  - [x] Entity CRUD（含基于 hash 的实体 ID 生成）
  - [x] Relation CRUD
  - [x] Evidence CRUD
- [x] **测试与验收**
  - [x] 成功执行 Alembic `upgrade head` 完成 PostgreSQL 建表
  - [x] 基础单元测试通过（API容器验证正常启动）

---

### Phase 2: YAML 规则迁移 
*状态: 已完成 (Completed)*

- [x] **数据结构映射**
  - [x] 确定 `config/commodity_graph/` YAML 中 `exact_stocks`、`downstream` 等字段向标准图谱关系 (`produces`, `uses` 等) 的硬编码映射规则
- [x] **迁移脚本开发**
  - [x] 编写 `yaml_to_kg_loader.py`
  - [x] 解析所有 YAML，进行实体归一化
  - [x] 批量写入 PostgreSQL 实体表与关系表，标记 `source_type = yaml_seed`
- [x] **测试与验收**
  - [x] 验证迁移脚本的幂等性（重复执行不产生冗余数据）

---

### Phase 3: Reasoning Engine MVP 
*状态: 已完成 (Completed)*

- [x] **模块拆解与重构 (消灭 God Class)**
  - [x] 拆解 `app/services/event_engine.py`
  - [x] 建立 `event_extractor.py` (事件提取与标准化，含 lifecycle_stage)
  - [x] 建立 `graph_querier.py` (图谱查询，含 context_date 强约束)
  - [x] 建立 `exposure_calculator.py` (敞口计算)
- [x] **多因子评分机制**
  - [x] 编写初版 `scoring_engine.py`
- [x] **测试与验收**
  - [x] 输入特定事件（如“六氟化钨短缺”），成功输出候选股票列表及带置信度的解释路径

---

### Phase 4: LLM 抽取候选关系 
*状态: 已完成 (Completed)*

- [x] **抽取服务集成**
  - [x] 实现 `llm_extract_company_profile()` 和 `llm_extract_event()`
  - [x] 构建并管理基于场景的 Prompt 模板 (年报/公告/新闻)
- [x] **候选关系流转**
  - [x] 将 LLM JSON 提取结果校验并写入 `candidate_relations` 表
  - [x] 开发人工审核 API (Approve/Reject)
- [x] **测试与验收**
  - [x] 丢入一篇研报文本，成功在数据库候选表中生成结构化数据及超链接证据

---

### Phase 5: Validation Loop 验证闭环 
*状态: 待开始 (Pending)*

- [ ] **验证引擎开发**
  - [ ] 实现 `validation_engine.py` 与 `return_calculator.py`
  - [ ] 计算 T+1/3/5/10 的绝对与超额收益
- [ ] **结果统计与回写**
  - [ ] 实现 `validation_summary_service.py` 进行批处理聚合
  - [ ] 将高胜率/低胜率结果反馈到关系权重系数中
- [ ] **测试与验收**
  - [ ] 跑通某类历史事件的批量回溯，成功在表中生成有效统计记录

---

### Phase 6: Web Explainability 前端解释层 
*状态: 待开始 (Pending)*

- [ ] **API 适配**
  - [ ] `graphApi`, `eventApi`, `stockExplainApi`, `validationApi` 联调对接
- [ ] **UI 页面开发**
  - [ ] 事件看板 (Event Dashboard)
  - [ ] 供应链探索 (Supply Chain Explorer)
  - [ ] 推理逻辑卡 (Why This Stock)
  - [ ] 验证监控台 (Validation Panel)
- [ ] **状态与异常处理**
  - [ ] 骨架屏、低置信提醒、过期数据(Stale Data)强提示
- [ ] **测试与验收**
  - [ ] 页面端能够完整展示事件从发生到推理、最终影响股票及验证胜率的全链路

---

### Phase 7: Interaction Layer 交互层 
*状态: 待开始 (Pending)*

- [ ] **对话查询模块 (NL2Graph)**
  - [ ] 意图识别小模型接入，拦截直连数据库请求
- [ ] **纠错反馈与主动干预闭环**
  - [ ] Web 端实装报错、降权按钮
  - [ ] 低置信度数据的“审核工作流卡片”
- [ ] **动态监控预警系统**
  - [ ] 推送条件阈值判定引擎
  - [ ] 消息通道(Webhook)发送
- [ ] **即时主动喂入**
  - [ ] 支持用户在前端上传私有文本触发即时推理 (打上 `user_private` 标签)
- [ ] **测试与验收**
  - [ ] 自然语言转 API 成功；手工改判数据被锁定高置信。
