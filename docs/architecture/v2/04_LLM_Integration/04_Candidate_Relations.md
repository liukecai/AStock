# 04 Candidate Relations

> 本文档定义 AStock V2 中 LLM 输出如何进入候选关系层。

---

## 1. Candidate Relation 定位

Candidate Relation 是正式 Knowledge Graph 之前的缓冲层。

LLM、规则抽取、新闻抽取、人工草稿都应先进入候选层。

候选层用于隔离：

- 抽取错误。
- LLM 幻觉。
- 低质量来源。
- 未确认关系。
- 冲突信息。

---

## 2. 为什么需要候选层

如果 LLM 输出直接进入正式图谱，会导致：

- 错误关系污染图谱。
- 推理结果不可信。
- 前端解释出现虚假路径。
- 后续难以回滚。

因此所有机器生成关系必须先进入候选层。

---

## 3. Candidate Relation 字段

建议字段：

```text
candidate_id
subject_name
subject_type
predicate
object_name
object_type
evidence_id
evidence_text
source_type
extractor_type
extractor_version
confidence
status
review_reason
created_at
updated_at
```

---

## 4. Candidate 状态

状态包括：

```text
pending
auto_approved
manual_approved
rejected
needs_review
duplicate
conflicted
```

说明：

| 状态 | 说明 |
|---|---|
| pending | 等待审核 |
| auto_approved | 自动通过 |
| manual_approved | 人工通过 |
| rejected | 已拒绝 |
| needs_review | 需要复核 |
| duplicate | 重复候选 |
| conflicted | 与已有关系冲突 |

---

## 5. 自动通过规则

候选关系可以自动通过，但必须满足严格条件。

示例：

```text
source_type in [annual_report, prospectus, announcement, company_website]
confidence >= 0.85
evidence_text 非空
实体归一化成功
predicate 合法
不存在冲突关系
```

通过后写入正式图谱。

---

## 6. 必须人工审核的情况

以下情况需要人工审核：

- 来源是新闻、RSS、互动易、招聘、社交讨论。
- confidence 低于阈值。
- 关系涉及热点概念。
- 关系与已有关系冲突。
- 实体无法归一。
- evidence_text 太短或含糊。
- LLM 给出推断性关系。

---

## 7. 重复检测

候选关系去重依据：

```text
subject_name + predicate + object_name + evidence_id
```

进入正式图谱前，还需要与正式关系去重：

```text
source_entity_id + relation_type + target_entity_id
```

如果正式关系已存在，则追加 evidence，而不是创建新关系。

---

## 8. 冲突检测

冲突示例：

```text
候选关系：公司 produces 产品A
已有关系：公司已剥离 产品A
```

处理：

- 标记 conflicted。
- 不自动通过。
- 进入人工审核。
- 保留冲突证据。

---

## 9. 实体归一化

候选关系中的 subject 和 object 必须映射到正式实体或候选实体。

示例：

```text
WF6 -> 六氟化钨
Tungsten Hexafluoride -> 六氟化钨
```

无法归一的实体进入 candidate_entities。

---

## 10. Promotion 到正式图谱

候选关系通过审核后：

```text
candidate_relation
  ↓
resolve subject entity
  ↓
resolve object entity
  ↓
upsert kg_relation
  ↓
append relation_evidence
  ↓
mark candidate as approved
```

---

## 11. Rejection

被拒绝的候选关系不应删除。

应保留：

```text
rejected status
review_reason
reviewed_at
reviewed_by
```

这样可以避免同一错误反复出现。

---

## 12. Candidate Relation 设计原则

1. LLM 输出不能直接进入正式图谱。
2. 候选关系必须绑定 evidence_text。
3. 高质量来源可自动通过。
4. 低质量来源必须人工审核或多源确认。
5. 被拒绝候选不删除。
6. 候选到正式图谱的过程必须可追踪。

---

## 13. 结论

Candidate Relation 是 LLM 自动化能力和图谱可信度之间的安全隔离层。

没有候选层，LLM 会污染图谱。

有了候选层，系统可以在自动化和可信度之间取得平衡。