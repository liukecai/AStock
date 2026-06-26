# 02 Knowledge Graph Design

> AStock V2 产业知识图谱设计。
>
> 本文档定义知识图谱的实体模型、关系模型、证据模型、构建流程、查询设计、更新机制和关键决策。
>
> 前置阅读：[01_System_Architecture.md](./01_System_Architecture.md) 第 3 节（目标架构）和第 4 节（模块职责）。

---

## 1. 为什么需要 Knowledge Graph

V1 的事件到股票映射是面向具体事件的规则（如 `六氟化钨紧缺 → 中船特气`），随着产业链节点增加会出现：重复规则、无法复用中间节点、无法解释来源、无法多跳推理、无法自动发现相邻机会。

Knowledge Graph 将这些规则升级为可查询、可追溯、可验证的长期知识：

```text
V1：六氟化钨紧缺 → 中船特气 / 中钨高新
V2：六氟化钨 →belongs_to→ 电子特气 →belongs_to→ 半导体材料
    中船特气 →produces→ 六氟化钨
    中钨高新 →exposed_to→ 钨材料
```

### 图谱不是标签系统

错误设计：`中船特气 tags = [电子特气, 半导体]` —— 无法表达关系类型、方向、证据和路径。

正确设计：用 Entity + Relation 建模，每条关系有方向、权重、置信度和证据来源。

---

## 2. 实体模型

### 2.1 基础字段

所有实体至少包含：

| 字段 | 说明 |
|---|---|
| entity_id | 全局唯一 ID（建议使用 `MD5(entity_type + canonical_name)` 确保幂等） |
| entity_type | 实体类型 |
| name | 展示名称 |
| canonical_name | 归一化名称（统一 `WF6` / `六氟化钨气体` → `六氟化钨`） |
| aliases | 别名列表（用于新闻匹配和 LLM 归一化） |
| description | 简要说明 |
| status | `active` / `inactive` / `candidate` / `rejected` / `merged` |
| created_at / updated_at | 时间戳 |

### 2.2 核心实体类型

| 类型 | 说明 | 示例 |
|---|---|---|
| Company | 上市/非上市公司主体 | 中船特气、中钨高新 |
| Stock | 股票代码（与 Company 分离，支持多市场扩展） | 688146.SH、000657.SZ |
| Product | 公司生产/销售的具体产品 | 六氟化钨、三氟化氮、硬质合金 |
| Material | 材料或中间品 | 电子特气、半导体材料、钨材料 |
| Commodity | 商品或资源品 | 钨、铜、锂、原油 |
| Industry | 行业（产业视角） | 半导体材料、有色金属、军工 |
| Sector | 板块（市场交易视角） | 半导体板块、中特估、低空经济 |
| Concept | 概念题材（变化快，置信度应低） | HBM、AI 算力、国产替代 |
| EventType | 事件类型（抽象） | supply_shortage、demand_growth、policy_support |
| EventInstance | 具体事件实例 | 2026-xx-xx 六氟化钨供应紧张 |
| Evidence | 可追溯来源 | 2025 年报、招股说明书、官网产品页 |

**后续可扩展**：Country、Region、Policy、Technology、Customer、Supplier、Capacity、Project。

### 2.3 实体设计原则

1. Company 和 Stock 分离（一个公司可能有多个证券代码）。
2. Product 和 Material 分离。
3. Industry 和 Sector 分离。
4. EventType 和 EventInstance 分离。
5. Evidence 作为一等实体保留。
6. 所有实体必须支持别名和归一化。
7. 合并后原实体标记为 `merged`，指向 canonical entity，不直接删除。

---

## 3. 关系模型

### 3.1 基础字段

| 字段 | 说明 |
|---|---|
| relation_id | 全局唯一关系 ID |
| source_entity_id / target_entity_id | 起点/终点实体 |
| relation_type | 关系类型 |
| direction | 方向（默认 directed） |
| weight | 推理权重（0.0~1.0，表示事件传播强度） |
| confidence | 置信度（0.0~1.0，表示关系真实性） |
| source_type | 关系来源类型 |
| evidence_ids | 支持证据列表 |
| status | `candidate` / `active` / `rejected` / `deprecated` / `validated` |
| valid_from / valid_to | 关系有效时间区间（构建时序图谱，防止历史回测出现未来函数） |
| created_at / updated_at | 时间戳 |

### 3.2 核心关系类型

| 关系 | 模式 | 示例 |
|---|---|---|
| listed_as | Company → Stock | 中船特气 → 688146.SH |
| produces | Company → Product | 中船特气 → 六氟化钨 |
| supplies | Company → Product/Industry | 公司A → 半导体客户 |
| uses | Product/Industry → Material/Commodity | 硬质合金 → 钨 |
| belongs_to | Product → Material → Industry → Sector | 六氟化钨 → 电子特气 → 半导体材料 |
| upstream_of | EntityA → EntityB | 钨 → 六氟化钨 |
| downstream_of | EntityA → EntityB | （可由 upstream_of 反向推导） |
| used_in | Product → Industry | 六氟化钨 → 半导体制造 |
| impacts | EventType → Commodity/Material/Industry | supply_shortage → 六氟化钨 |
| benefits / hurts | EventType → Company/Industry | 谨慎使用，优先通过推理路径计算 |
| exposed_to | Company/Stock → Entity | 可由其他关系推导，也可显式沉淀 |
| evidenced_by | Relation → Evidence | 通过 relation_evidence 表实现 |
| aliases | AliasEntity → CanonicalEntity | WF6 → 六氟化钨 |

### 3.3 Weight 与 Confidence 的区别

```text
某公司确实生产某产品 → confidence 高
但该产品收入占比很小 → weight 低
```

- **confidence**：关系真实性可信度。
- **weight**：关系在事件传播中的强度。

两者独立更新，独立用于不同计算。

### 3.4 置信度参考范围

| 来源 | confidence 参考值 |
|---|---:|
| 年报 / 招股书 | 0.90 ~ 0.98 |
| 官网产品目录 | 0.80 ~ 0.95 |
| 公告 | 0.75 ~ 0.95 |
| 互动易 | 0.55 ~ 0.80 |
| 新闻 | 0.40 ~ 0.70 |
| 社交讨论 | 0.20 ~ 0.50 |
| LLM 候选 | 按原始来源调整 |

### 3.5 关系设计原则

1. 关系必须有类型和方向。
2. 关系必须有置信度，应尽可能绑定证据。
3. weight 和 confidence 分离。
4. 候选关系不能直接参与核心推理。
5. 多来源关系应合并（追加 evidence + 更新 confidence），不重复创建。
6. 唯一键：`source_entity_id + relation_type + target_entity_id`。

---

## 4. 证据模型

### 4.1 Evidence 基础字段

| 字段 | 说明 |
|---|---|
| evidence_id | 证据唯一 ID |
| source_type | 来源类型（`annual_report` / `prospectus` / `announcement` / `company_website` / `news` / `yaml_seed` / `llm_extraction` 等） |
| source_name / source_url | 来源名称和链接 |
| title / raw_text | 标题和原文 |
| published_at / collected_at | 发布/采集时间 |
| related_company / related_stock_code | 相关公司和股票 |
| source_confidence | 来源基础可信度 |
| content_hash | 去重 hash（`source_type + source_url + title + raw_text`） |
| status | `active` / `archived` / `rejected` |

### 4.2 Relation-Evidence 绑定

一条关系可有多个证据支持，通过 `relation_evidence` 中间表绑定：

| 字段 | 说明 |
|---|---|
| relation_id | 关系 ID |
| evidence_id | 证据 ID |
| support_type | `direct` / `indirect` / `weak` / `contradictory` |
| extracted_text | 与关系相关的证据片段 |
| confidence_delta | 该证据对关系置信度的贡献 |

### 4.3 证据设计原则

1. **没有证据的关系只能是候选关系。**
2. LLM 不是证据来源。LLM 只是抽取方式。如果 LLM 从年报中抽取信息，证据来源是 `annual_report`。
3. 多来源证据应合并提高置信度。
4. 弱证据不能单独生成高置信关系。
5. 使用 `content_hash` 去重，避免重复转载放大权重。
6. 证据可设置 `valid_from` / `valid_to` 管理时效性。

---

## 5. 图谱构建

### 5.1 总体流程

```text
Raw Source → Evidence Collector → Extractor → Candidate Entity/Relation
  → Normalize / Deduplicate → Review / Auto Approval → Write Knowledge Graph → Validation Feedback
```

### 5.2 构建来源

| 来源 | 说明 | 可信度 |
|---|---|---|
| YAML 种子 | V1 人工确认规则，通过 `yaml_to_kg_loader` 写入 | 高 |
| 年报 / 招股书 / 公告 | 文档类，经 LLM 或规则抽取 | 高 |
| 官网产品目录 | 网页抽取 | 较高 |
| 新闻 / RSS | 事件发现，不直接生成高置信供应链关系 | 中低 |
| LLM 抽取 | 候选层，结构化 JSON 输出 → 详见 [04_LLM_Integration.md](./04_LLM_Integration.md) | 取决于原始来源 |

### 5.3 自动审核规则

满足以下条件的候选关系可自动进入正式图谱：

```text
来源为年报 / 招股书 / 公告
且抽取置信度 >= 0.85
且实体归一化成功
且不存在冲突关系
```

其他关系进入人工审核或候选池。

### 5.4 冲突处理

```text
来源 A：公司生产某产品
来源 B：公司已剥离该产品业务
→ 保留两条 evidence，关系标记 needs_review，降低 confidence，等待确认
```

### 5.5 构建原则

1. 先证据，后关系。
2. LLM 输出只进入候选层。
3. 关系合并优先于重复创建。
4. 冲突关系不删除，应进入审核状态。
5. 图谱构建必须幂等（同一证据重复处理不产生重复实体/关系）。
6. 必须支持增量构建，不得每次全量重建。
7. YAML 是种子，不是长期唯一维护方式。

---

## 6. 图谱查询

### 6.1 查询类型

| 查询 | 用途 | 使用方 |
|---|---|---|
| entity_lookup | 根据名称/别名/代码查找实体 | 全局搜索 |
| neighbor_query | 查询实体一跳邻居 | Supply Chain Explorer |
| path_query | 查询两实体间路径（含节点、关系、权重、置信度、证据） | 事件推理 |
| impact_query | 从事件影响对象向外扩散（必须带有 `context_date` 约束） | Reasoning Engine 核心查询 |
| stock_exposure_query | 查询股票对实体的暴露度 | 个股解释 |
| evidence_query | 查询某关系的证据来源 | 可解释性 |
| explain_query | 生成前端解释路径（读取已落库结果） | Why This Stock |

### 6.2 路径评分

```text
path_score = ∏(edge_weight × edge_confidence) × depth_decay
```

- `depth_decay` 惩罚过长路径。
- 默认 `max_depth = 4`，超过 4 跳后路径解释性下降且噪音增多。
- **防未来函数约束**：所有进行历史事件推理和验证的图谱查询必须传入 `context_date`，只搜索满足 `valid_from <= context_date` 且 `(valid_to >= context_date 或为 null)` 的活动边。

### 6.3 查询排序

候选路径排序依据：路径分数 → 路径长度 → 证据质量 → 历史验证表现 → 关系更新时间。前端默认展示 Top N。

### 6.4 性能设计

关系型数据库阶段核心索引 → 详见 [05_Database_Design.md](./05_Database_Design.md)：

```text
kg_entities.canonical_name / entity_type
kg_relations.source_entity_id / target_entity_id / relation_type / status
relation_evidence.relation_id
```

多跳查询在服务层实现 BFS/DFS。常用查询（股票知识卡、热门实体邻居、事件推理路径）可缓存。

---

## 7. 图谱更新

### 7.1 更新类型

| 操作 | 说明 |
|---|---|
| entity_upsert | 按 canonical_name + aliases + entity_type 判重，合并重复实体 |
| relation_upsert | 已存在则追加 evidence + 更新 confidence/weight，否则创建 |
| evidence_append | 新证据支持已有关系时追加 |
| confidence_update | 新增高质量证据 → 提高；冲突证据 → 降低 |
| weight_update | 根据主营占比、产能、历史验证结果调整 |
| status_update | `candidate → active → deprecated → validated`，变更必须记录原因 |
| alias_merge | 选择 canonical entity → 迁移别名 → 重定向关系 → 标记旧实体为 merged |
| validation_feedback | 市场验证结果回写 weight（多次有效 → 提高；多次无效 → 降低） |

### 7.2 验证反馈规则

```text
市场验证只校准 impact weight，不直接否定事实关系。
```

某公司确实生产某产品是事实关系。市场不一定每次都交易这条关系。

### 7.3 幂等性与审计

- 同一 evidence 重复处理不产生重复实体/关系/evidence。
- 图谱更新必须记录审计日志：`operation_type` / `entity_id` / `relation_id` / `old_value` / `new_value` / `reason` / `operator`（system / llm_extractor / yaml_loader / manual_admin / validation_engine）。

---

## 8. 架构决策记录（ADR）

### ADR-001：采用 Knowledge Graph 表达产业链关系

用实体关系替代标签。支持多跳推理、证据追踪、关系复用、前端路径解释。

### ADR-002：Entity + Relation，而不是 Stock Tag

关系语义明确，可用于路径推理，可解释性更强。

### ADR-003：Company 和 Stock 分离建模

`Company → listed_as → Stock`。更符合真实金融资产结构，便于扩展港股、美股、债券等。

### ADR-004：Evidence 作为一等对象

Evidence 独立存在，通过 `relation_evidence` 绑定到关系。关系可追溯，置信度可解释。

### ADR-005：LLM 输出进入 Candidate 层

LLM 输出只写入 `candidate_entities` / `candidate_relations`，经校验或审核后才入正式图谱。降低幻觉风险。

### ADR-006：第一阶段使用关系型数据库实现图谱

`kg_entities` / `kg_relations` / `evidence` / `relation_evidence` / `candidate_entities` / `candidate_relations`。复用现有栈，部署简单，后续再评估 Neo4j。

### ADR-007：confidence 与 weight 分离

推理更准确，可区分事实可信度和影响强度。

### ADR-008：市场验证只校准 weight，不否定事实关系

避免把市场短期噪音误认为事实错误，能区分产业事实和交易有效性。
