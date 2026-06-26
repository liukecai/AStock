# 02 Knowledge Graph Tables

> 本文档定义 AStock V2 Knowledge Graph 相关数据库表。

---

## 1. 表设计目标

Knowledge Graph Tables 用于保存：

- 图谱实体。
- 图谱关系。
- 关系证据。
- 候选实体。
- 候选关系。
- 图谱变更日志。

这些表是 V2 图谱推理和可解释能力的核心。

---

## 2. kg_entities

正式实体表。

```text
kg_entities
```

建议字段：

```text
id
entity_id
entity_type
name
canonical_name
aliases_json
description
external_ids_json
status
created_at
updated_at
```

entity_type 示例：

```text
Company
Stock
Product
Material
Commodity
Industry
Sector
Concept
EventType
EventInstance
Evidence
```

---

## 3. kg_relations

正式关系表。

```text
kg_relations
```

建议字段：

```text
id
relation_id
source_entity_id
target_entity_id
relation_type
weight
confidence
source_type
status
valid_from
valid_to
created_at
updated_at
```

唯一约束建议：

```text
source_entity_id + relation_type + target_entity_id
```

---

## 4. relation_evidence

关系证据绑定表。

```text
relation_evidence
```

建议字段：

```text
id
relation_id
evidence_id
support_type
extracted_text
confidence_delta
created_at
```

support_type：

```text
direct
indirect
weak
contradictory
```

---

## 5. evidence

证据表。

```text
evidence
```

建议字段：

```text
id
evidence_id
source_type
source_name
source_url
title
raw_text
published_at
collected_at
related_company
related_stock_code
source_confidence
content_hash
status
created_at
updated_at
```

Evidence 是图谱可信度基础，应长期保留。

---

## 6. evidence_chunks

证据片段表。

```text
evidence_chunks
```

建议字段：

```text
id
evidence_id
chunk_index
chunk_text
section_title
page_number
char_start
char_end
content_hash
created_at
```

适用于年报、招股书、长公告和 PDF 文本。

---

## 7. candidate_entities

候选实体表。

```text
candidate_entities
```

建议字段：

```text
id
name
entity_type
canonical_name
aliases_json
evidence_id
evidence_text
extractor_type
extractor_version
confidence
status
review_reason
created_at
updated_at
```

状态：

```text
pending
auto_approved
manual_approved
rejected
duplicate
merged
```

---

## 8. candidate_relations

候选关系表。

```text
candidate_relations
```

建议字段：

```text
id
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

候选关系通过审核后写入 kg_relations。

---

## 9. kg_change_logs

图谱变更日志表。

```text
kg_change_logs
```

建议字段：

```text
id
operation_type
entity_id
relation_id
old_value_json
new_value_json
reason
operator
created_at
```

operation_type 示例：

```text
create_entity
update_entity
merge_entity
create_relation
update_relation
reject_candidate
promote_candidate
```

---

## 10. 关系权重与置信度

kg_relations 必须同时保存：

```text
weight
confidence
```

含义：

- confidence 表示事实可信度。
- weight 表示推理传播强度。

两者不能混用。

---

## 11. 设计原则

1. 正式实体和候选实体分表。
2. 正式关系和候选关系分表。
3. Evidence 独立保存。
4. Relation 与 Evidence 多对多绑定。
5. 图谱变更必须记录日志。
6. 关系唯一键防止重复写入。
7. confidence 与 weight 分离。

---

## 12. 结论

Knowledge Graph Tables 是 AStock V2 的长期知识存储层。

这组表决定系统能否实现可追溯、可解释、可验证的产业链推理。