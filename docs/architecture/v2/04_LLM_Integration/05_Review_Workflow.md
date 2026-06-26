# 05 Review Workflow

> 本文档定义 AStock V2 中 LLM 候选结果的审核流程。

---

## 1. Review Workflow 目标

Review Workflow 的目标是控制 LLM 抽取结果进入正式图谱的质量。

候选结果必须经过：

- 自动校验。
- 实体归一化。
- 关系去重。
- 来源质量判断。
- 冲突检测。
- 自动通过或人工审核。

---

## 2. 审核流程总览

```text
LLM Output
  ↓
JSON Validation
  ↓
Candidate Relation
  ↓
Entity Normalization
  ↓
Rule Check
  ↓
Conflict Check
  ↓
Auto Approval / Manual Review
  ↓
Knowledge Graph
```

---

## 3. JSON Validation

首先校验输出结构。

校验项：

- 是否是合法 JSON。
- 必填字段是否存在。
- 枚举值是否合法。
- confidence 是否为 0 到 1。
- evidence_text 是否非空。

失败结果不进入 candidate 表。

---

## 4. Entity Normalization

对 subject 和 object 进行实体归一。

处理结果：

```text
matched_existing_entity
created_candidate_entity
failed_to_match
```

无法归一的关系不能自动通过。

---

## 5. Rule Check

规则校验包括：

- predicate 是否允许。
- subject_type 与 predicate 是否匹配。
- object_type 与 predicate 是否匹配。
- 来源类型是否允许自动通过。
- confidence 是否达到阈值。

示例：

```text
Company -> produces -> Product 合法
Product -> produces -> Company 不合法
```

---

## 6. Conflict Check

冲突检测用于识别与正式图谱已有关系矛盾的候选。

冲突类型：

- 业务已剥离。
- 产品已停产。
- 公司否认相关业务。
- 同名实体误匹配。
- 关系方向相反。

冲突候选进入 needs_review 或 conflicted。

---

## 7. Auto Approval

自动通过适用于高质量、低风险关系。

条件示例：

```text
source_type in [annual_report, prospectus, announcement, company_website]
confidence >= 0.85
evidence_text 非空
entity matched
no conflict
predicate valid
```

自动通过后写入正式图谱，并记录操作来源。

---

## 8. Manual Review

人工审核适用于：

- 热点概念关系。
- 新闻来源关系。
- 互动易关系。
- 招聘关系。
- 专利关系。
- 低置信度关系。
- 冲突关系。

人工审核动作：

```text
approve
reject
merge_entity
edit_relation
mark_needs_more_evidence
```

---

## 9. Review UI 要求

审核页面应展示：

- subject。
- predicate。
- object。
- evidence_text。
- source_type。
- source_url。
- confidence。
- 已有相似关系。
- 冲突提示。

审核人员不应只看到 LLM 结论，必须看到证据片段。

---

## 10. 审核日志

每次审核必须记录：

```text
candidate_id
action
old_status
new_status
review_reason
reviewed_by
reviewed_at
```

这用于后续追踪和质量复盘。

---

## 11. Rejected Learning

被拒绝的候选应保留。

用途：

- 避免重复生成同类错误。
- 优化 Prompt。
- 优化规则校验。
- 识别低质量来源。

---

## 12. 设计原则

1. 高质量来源可自动通过。
2. 低质量来源必须审核。
3. evidence_text 是审核核心。
4. 冲突候选不能自动通过。
5. 审核过程必须留痕。
6. 被拒绝候选不删除。

---

## 13. 结论

Review Workflow 是 LLM 自动化和图谱可信度之间的控制阀。

没有审核流程，LLM 抽取会带来不可控噪音。

有了审核流程，系统才能在效率和可信度之间取得平衡。