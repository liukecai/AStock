# 01 Phase 1 KG Schema

> Phase 1 目标：建立 AStock V2 的 Knowledge Graph 最小数据库模型。

---

## 1. 阶段目标

Phase 1 不做复杂推理，只完成图谱基础表和最小数据写入能力。

目标产物：

```text
kg_entities
kg_relations
evidence
relation_evidence
candidate_entities
candidate_relations
```

---

## 2. 开发任务

新增 ORM Model：

```text
KGEntity
KGRelation
Evidence
RelationEvidence
CandidateEntity
CandidateRelation
```

新增 Repository：

```text
kg_entity_repository
kg_relation_repository
evidence_repository
candidate_repository
```

新增 Service：

```text
KnowledgeGraphService
EvidenceService
CandidateService
```

---

## 3. 最小字段

### kg_entities

```text
entity_id
entity_type
name
canonical_name
aliases_json
status
created_at
updated_at
```

### kg_relations

```text
relation_id
source_entity_id
target_entity_id
relation_type
weight
confidence
source_type
status
created_at
updated_at
```

### evidence

```text
evidence_id
source_type
title
source_url
raw_text
source_confidence
content_hash
status
created_at
updated_at
```

---

## 4. 最小 API

```text
GET /api/v2/graph/entities
GET /api/v2/graph/entities/{entity_id}
GET /api/v2/graph/entities/{entity_id}/neighbors
GET /api/v2/graph/relations/{relation_id}
```

---

## 5. 验收用例

手工插入：

```text
公司A -> produces -> 产品A
产品A -> belongs_to -> 材料A
材料A -> belongs_to -> 行业A
```

然后通过 API 查询实体邻居。

---

## 6. 验收标准

1. 数据库表创建成功。
2. 能插入实体和关系。
3. 能查询实体详情。
4. 能查询一跳邻居。
5. relation 能绑定 confidence 和 weight。
6. 不影响 V1 现有页面。

---

## 7. 风险控制

1. Phase 1 只实现最小字段。
2. Company 和 Stock 映射先保持简单。
3. JSON 字段先用 TEXT 保存。
4. 后续通过 migration 扩展。

---

## 8. 结论

Phase 1 是 V2 的地基。只有图谱基础表稳定，后续模块才能继续推进。