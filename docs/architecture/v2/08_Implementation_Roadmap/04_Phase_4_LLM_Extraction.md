# 04 Phase 4 Extraction

> Phase 4 目标：建设文本结构化抽取管道。

---

## 1. 阶段目标

从 Evidence 文本中抽取候选实体、候选关系和候选事件。

抽取结果只进入候选层，不直接进入正式图谱。

---

## 2. 目标链路

```text
Evidence Text
  ↓
Extraction
  ↓
Schema Validation
  ↓
Candidate Tables
  ↓
Review
  ↓
Knowledge Graph
```

---

## 3. 开发任务

新增模块：

```text
extraction_service.py
schema_validator.py
candidate_review_service.py
prompt_registry.py
```

新增配置：

```text
config/extraction.yaml
config/prompts/
```

---

## 4. 优先任务

```text
annual_report_extraction
prospectus_extraction
announcement_extraction
company_website_extraction
news_event_extraction
```

---

## 5. 输出要求

抽取结果必须包含：

```text
subject
predicate
object
evidence_text
confidence
source_type
```

---

## 6. 入库规则

写入：

```text
candidate_entities
candidate_relations
candidate_events
```

审核通过后再写入：

```text
kg_entities
kg_relations
```

---

## 7. 验收标准

1. 能读取 evidence 文本。
2. 能生成结构化 JSON。
3. 能通过 schema 校验。
4. 能写入候选表。
5. 能审核候选关系。
6. 审核通过后能写入正式图谱。

---

## 8. 风险控制

1. 不进入在线请求链路。
2. 不直接写正式图谱。
3. 无 evidence_text 的结果拒绝。
4. 低质量来源不得自动通过。
5. 所有抽取配置必须版本化。

---

## 9. 结论

Phase 4 用候选层隔离抽取风险，为图谱持续补充新知识。