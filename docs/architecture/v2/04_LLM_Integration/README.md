# 04 LLM Integration

> 本目录定义 AStock V2 中大模型的接入方式。
>
> LLM 在 V2 中的定位是信息抽取、候选关系生成和解释辅助，不是最终选股决策模块。

---

## 文档范围

```text
04_LLM_Integration/
├── README.md
├── 00_Overview.md
├── 01_Extraction_Tasks.md
├── 02_Prompt_Design.md
├── 03_JSON_Schema.md
├── 04_Candidate_Relations.md
├── 05_Review_Workflow.md
├── 06_Risk_Control.md
└── 07_ADR.md
```

---

## 阅读顺序

1. `00_Overview.md`：理解 LLM 在 V2 中的定位和边界。
2. `01_Extraction_Tasks.md`：理解 LLM 负责哪些抽取任务。
3. `02_Prompt_Design.md`：理解 Prompt 如何设计。
4. `03_JSON_Schema.md`：理解 LLM 输出结构规范。
5. `04_Candidate_Relations.md`：理解 LLM 输出如何进入候选关系层。
6. `05_Review_Workflow.md`：理解候选关系如何审核并进入图谱。
7. `06_Risk_Control.md`：理解幻觉、错误抽取和低质量来源如何控制。
8. `07_ADR.md`：理解 LLM Integration 的关键架构决策。

---

## LLM 的定位

LLM 负责：

- 从年报中抽取产品、原材料、下游行业。
- 从招股书中抽取上下游、客户、竞争对手、募投项目。
- 从公告中抽取新增产能、订单、风险事件。
- 从官网产品目录中抽取产品和应用场景。
- 从新闻中抽取事件类型、目标实体和影响方向。
- 为前端生成解释文本草稿。

LLM 不负责：

- 直接给出买卖建议。
- 直接修改正式知识图谱。
- 直接决定股票最终评分。
- 替代行情验证。
- 替代人工审核高风险关系。

---

## 核心原则

```text
LLM as Extractor, not Decision Maker
```

即：

```text
Evidence Text
  ↓
LLM Extraction
  ↓
Candidate Entity / Candidate Relation
  ↓
Validation / Review
  ↓
Knowledge Graph
```

---

## 输出要求

LLM 输出必须满足：

- JSON 格式。
- 字段固定。
- 可追溯 evidence。
- 不输出自然语言投资建议。
- 不直接输出最终股票推荐。
- 每条结论必须包含 confidence。
- 每条关系必须包含 evidence_text。

---

## 与 Knowledge Graph 的关系

LLM 输出不会直接写入正式图谱。

LLM 输出先进入：

```text
candidate_entities
candidate_relations
candidate_events
```

通过审核、规则校验或多证据确认后，才能进入：

```text
kg_entities
kg_relations
```

---

## 与 Reasoning Engine 的关系

LLM 不参与实时推理链路。

正确链路：

```text
离线 LLM 抽取
  ↓
候选知识
  ↓
图谱更新
  ↓
Reasoning Engine 查询图谱
```

错误链路：

```text
用户打开页面
  ↓
实时调用 LLM
  ↓
让 LLM 推荐股票
```

---

## 成功标准

LLM Integration 完成后，系统应能：

1. 自动从年报抽取公司主营产品。
2. 自动从招股书抽取上下游产业链。
3. 自动从公告抽取产能、订单、风险事件。
4. 自动从新闻抽取结构化事件。
5. 将抽取结果写入候选关系层。
6. 保留 evidence_text 供人工审核。
7. 降低手工维护 YAML 的成本。
8. 不让 LLM 直接污染正式图谱。