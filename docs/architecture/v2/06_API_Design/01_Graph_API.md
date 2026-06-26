# 01 Graph API

> 本文档定义 AStock V2 的 Knowledge Graph 查询 API。

---

## 1. Graph API 目标

Graph API 用于支持：

- 实体查询。
- 关系查询。
- 邻居查询。
- 路径查询。
- 证据查询。
- 产业链浏览。

Graph API 是 Supply Chain Explorer 和 Reasoning Engine 可视化的基础。

---

## 2. API 分组

统一前缀：

```text
/api/v2/graph
```

主要接口：

```text
GET /entities
GET /entities/{entity_id}
GET /entities/{entity_id}/neighbors
GET /relations/{relation_id}
GET /relations/{relation_id}/evidence
POST /paths
GET /search
```

---

## 3. GET /graph/entities

查询实体列表。

参数：

```text
entity_type
keyword
status
page
page_size
```

返回字段：

```text
entity_id
entity_type
name
canonical_name
aliases
status
```

用途：

- 实体搜索。
- 后台审核。
- 前端图谱浏览入口。

---

## 4. GET /graph/entities/{entity_id}

查询实体详情。

返回字段：

```text
entity_id
entity_type
name
canonical_name
aliases
description
status
created_at
updated_at
```

如果实体是 Company 或 Stock，可返回基础映射信息。

---

## 5. GET /graph/entities/{entity_id}/neighbors

查询实体一跳邻居。

参数：

```text
relation_type
neighbor_type
direction
min_confidence
limit
```

返回：

```json
{
  "entity": {},
  "neighbors": [
    {
      "relation": {},
      "neighbor": {},
      "evidence_count": 2
    }
  ]
}
```

用途：

- Supply Chain Explorer。
- Company Knowledge Card。
- 产业链上下游展示。

---

## 6. GET /graph/relations/{relation_id}

查询关系详情。

返回字段：

```text
relation_id
source_entity
target_entity
relation_type
weight
confidence
source_type
status
valid_from
valid_to
```

---

## 7. GET /graph/relations/{relation_id}/evidence

查询关系证据。

返回：

```text
evidence_id
source_type
title
source_url
published_at
extracted_text
support_type
confidence_delta
```

用途：

- Why This Stock。
- 人工审核。
- 图谱可信度展示。

---

## 8. POST /graph/paths

查询两个实体之间的路径。

请求体：

```json
{
  "source_entity_id": "ent_wf6",
  "target_entity_id": "ent_cssc_special_gas",
  "max_depth": 4,
  "relation_types": ["produces", "belongs_to", "used_in"],
  "min_confidence": 0.3
}
```

返回：

```json
{
  "paths": [
    {
      "path_id": "path_001",
      "nodes": [],
      "edges": [],
      "path_score": 0.76,
      "confidence": 0.82
    }
  ]
}
```

---

## 9. GET /graph/search

图谱搜索接口。

参数：

```text
q
entity_type
limit
```

支持：

- canonical_name。
- aliases。
- stock_code。
- company_name。

---

## 10. Path DTO

路径 DTO 必须包含：

```text
nodes
edges
path_score
confidence
evidence_summary
```

edge 字段：

```text
relation_id
source_entity_id
target_entity_id
relation_type
weight
confidence
evidence_ids
```

---

## 11. 查询限制

默认限制：

```text
max_depth <= 4
limit <= 50
min_confidence >= 0.0
```

避免图谱查询扩散过大。

---

## 12. 设计原则

1. Graph API 只读为主。
2. 路径接口必须限制深度。
3. 所有关系必须返回 confidence 和 weight。
4. 证据查询必须可追溯到 source_url。
5. 搜索必须支持 aliases。
6. API 不直接返回数据库内部主键作为唯一业务标识。

---

## 13. 结论

Graph API 是 V2 图谱能力的外部接口。

它必须同时服务推理、解释、审核和前端探索。