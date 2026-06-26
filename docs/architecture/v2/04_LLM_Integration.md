# 04 LLM Integration

> AStock V2 大模型接入方式。
>
> LLM 在 V2 中的定位是信息抽取、候选关系生成和解释辅助，不是最终选股决策模块。
>
> 前置阅读：[02_Knowledge_Graph_Design.md](./02_Knowledge_Graph_Design.md) 第 5 节（图谱构建）和 [03_Reasoning_Engine.md](./03_Reasoning_Engine.md) 第 2 节（事件抽取）。

---

## 1. LLM 定位

### 核心原则

```text
LLM as Extractor, not Decision Maker
```

```text
Evidence Text → LLM Extraction → Candidate Entity/Relation → Validation/Review → Knowledge Graph
```

### LLM 负责

| 任务 | 来源 |
|---|---|
| 抽取产品、原材料、下游行业 | 年报 |
| 抽取上下游、客户、竞争对手、募投项目 | 招股书 |
| 抽取新增产能、订单、风险事件 | 公告 |
| 抽取产品和应用场景 | 官网产品目录 |
| 抽取事件类型、目标实体、影响方向 | 新闻 |
| 生成解释文本草稿 | 推理结果 |

### LLM 不负责

- 直接给出买卖建议
- 直接修改正式知识图谱
- 直接决定股票最终评分
- 替代行情验证
- 替代人工审核高风险关系

---

## 2. 抽取任务

### 2.1 年报解析

抽取目标：公司主营产品、原材料、客户结构、下游应用、产能信息。

### 2.2 招股书解析

抽取目标：核心产品、上下游供应链、竞争对手、募投项目、技术路线。

### 2.3 公告解析

抽取目标：新增产能、重大订单、业务剥离、风险事件、关联交易。

### 2.4 官网产品目录解析

抽取目标：产品列表、产品分类、应用领域、技术参数。

### 2.5 新闻事件抽取

抽取目标：事件类型、受影响实体、影响方向、强度、时间范围。

---

## 3. Prompt 设计

### 3.1 设计原则

1. 输出必须是 JSON。
2. 每条结论必须包含 `confidence` 和 `evidence_text`。
3. 不输出自然语言投资建议。
4. 不直接输出股票推荐。
5. 明确要求输出 `entity_type` 和 `relation_type`。
6. Prompt 必须版本化管理。

### 3.2 Prompt 模板示例（年报抽取）

```text
请从以下年报文本中抽取公司主营产品、原材料和下游应用。

输出格式为 JSON：
{
  "entities": [{"name": "...", "type": "Product|Material|Industry", "aliases": []}],
  "relations": [
    {
      "source": "公司名",
      "relation": "produces|uses|used_in",
      "target": "实体名",
      "evidence_text": "原文片段",
      "confidence": 0.0~1.0
    }
  ]
}

注意：
- 只抽取原文明确提到的内容。
- 不要推测未明确提到的关系。
- evidence_text 必须是原文片段。
- 只输出 JSON，不要输出其他文本。
```

---

## 4. JSON 输出规范

### 4.1 实体输出 Schema

```json
{
  "name": "六氟化钨",
  "type": "Product",
  "aliases": ["WF6", "Tungsten Hexafluoride"],
  "evidence_text": "公司主要产品包括六氟化钨...",
  "confidence": 0.86
}
```

### 4.2 关系输出 Schema

```json
{
  "source": "中船特气",
  "relation": "produces",
  "target": "六氟化钨",
  "evidence_text": "公司主要产品包括六氟化钨...",
  "confidence": 0.86
}
```

### 4.3 事件输出 Schema

```json
{
  "event_type": "supply_shortage",
  "target_entity": "六氟化钨",
  "intensity": "high",
  "direction": "positive_for_supplier",
  "evidence_text": "市场传出六氟化钨供应紧张...",
  "confidence": 0.75
}
```

### 4.4 校验规则

- JSON 格式合法性。
- 必填字段完整性（`evidence_text` 为强制字段）。
- `entity_type` 和 `relation_type` 属于预定义范围。
- `confidence` 在 0.0~1.0 范围内。
- 不合法输出直接拒绝，不做宽容解析。

---

## 5. 候选关系入库

### 5.1 流程

```text
LLM JSON Output → Schema Validate → Entity Normalize → Dedup Check
  → Write candidate_entities / candidate_relations → Mark status=candidate
```

### 5.2 候选关系字段

```text
subject / predicate / object / evidence_id / confidence / extractor_type / prompt_version / status
```

### 5.3 关键约束

- LLM 输出不直接写入正式图谱（`kg_entities` / `kg_relations`）。
- 候选关系只进入 `candidate_entities` / `candidate_relations`。
- 候选层与正式图谱物理隔离 → 详见 [05_Database_Design.md](./05_Database_Design.md)。

---

## 6. 审核流程

### 6.1 自动通过条件

```text
来源为年报 / 招股书 / 公告
且抽取置信度 >= 0.85
且实体归一化成功
且不存在冲突关系
```

### 6.2 必须人工审核

- 新闻、RSS、互动易来源的关系。
- 低置信度抽取结果。
- 存在冲突关系的候选。
- 概念题材类关系。
- 涉及未来计划（非已有事实）的关系。

### 6.3 审核状态

```text
candidate → approved → 写入正式图谱
candidate → rejected → 归档，不进入图谱
candidate → needs_more_evidence → 等待更多来源确认
```

---

## 7. 风险控制

### 7.1 幻觉控制

| 策略 | 说明 |
|---|---|
| evidence_text 强制 | 没有原文依据不入库 |
| Schema 校验 | 不合法输出直接拒绝 |
| 候选层隔离 | LLM 输出不直接进入正式图谱 |
| 来源标记 | 每条候选关系标记 `extractor_type=llm` |

### 7.2 常见误抽取

| 类型 | 说明 |
|---|---|
| 过度泛化 | 将模糊描述理解为确定关系 |
| 计划当事实 | 将规划/在建项目理解为已有能力 |
| 概念膨胀 | 将热点概念过度关联 |
| 行业混淆 | 将相似行业混为同一关系 |

### 7.3 成本控制

- 文档分块处理。
- 增量抽取，已处理的 `content_hash` 不重复调用。
- 缓存抽取结果。
- 优先处理高价值文档。

### 7.4 审计要求

每次 LLM 调用记录：`prompt_name` / `prompt_version` / `model_name` / `input_hash` / `output_hash` / `source_evidence_id` / `created_at` / `status`。

---

## 8. 解释生成

LLM 可辅助生成 Why This Stock 的解释文本，但输入必须包含：

```text
event / stock / reason_path / evidence_list / score_breakdown
```

LLM 只能基于这些输入生成说明，不能自由发挥添加不存在的关系。

---

## 9. 架构决策记录（ADR）

### ADR-001：LLM 作为抽取器，不作为决策器

最终推理和评分由 Knowledge Graph + Reasoning Engine + Scoring Engine + Validation Engine 完成。降低幻觉风险，保持系统可审计。

### ADR-002：LLM 输出必须进入候选层

不直接写入正式图谱，防止图谱被污染，支持审核和回滚。

### ADR-003：所有 LLM 输出必须是 JSON

通过 Schema 校验，易于自动化处理和失败重试。

### ADR-004：evidence_text 为强制字段

缺少 evidence_text 的结果不得进入候选层。结果可追溯，审核更高效。

### ADR-005：LLM 不进入实时查询链路

LLM 抽取作为离线任务执行。在线 API 只读取已入库结果。API 响应稳定，成本可控。

### ADR-006：Prompt 必须版本化

抽取结果记录 `prompt_version`，便于回溯和效果对比。

### ADR-007：高质量来源可自动通过，低质量来源必须审核

平衡效率和质量，降低低质量来源污染图谱的风险。

### ADR-008：解释生成只能基于已知路径和证据

LLM 生成解释时不能添加不存在的关系，解释更可信。
