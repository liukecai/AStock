# 06 Indexing Performance

> 本文档定义 AStock V2 数据库索引与性能设计。

---

## 1. 性能目标

V2 数据库需要支持：

- 股票详情页快速查询。
- 事件详情页快速查询。
- 图谱邻居查询。
- 多跳路径查询。
- 验证结果聚合查询。
- 后台任务批量写入。

第一阶段目标不是极致性能，而是避免明显慢查询和不可维护结构。

---

## 2. 核心索引原则

索引优先服务高频查询。

高频查询包括：

```text
按 stock_code 查询
按 event_id 查询
按 entity_id 查询
按 relation source / target 查询
按 created_at 查询最新数据
按 status 查询待处理任务
```

---

## 3. Core Tables 索引

### stocks

建议索引：

```text
stock_code unique
stock_name
industry
sector
status
```

### companies

建议索引：

```text
company_name
short_name
stock_code
status
```

### job_runs

建议索引：

```text
job_name
job_type
status
started_at
```

---

## 4. Evidence 索引

### evidence

建议索引：

```text
evidence_id unique
source_type
related_stock_code
related_company
published_at
content_hash unique
status
```

### evidence_chunks

建议索引：

```text
evidence_id
content_hash
```

长文本搜索第一阶段可用简单 LIKE，后续迁移 PostgreSQL full-text search。

---

## 5. Knowledge Graph 索引

### kg_entities

建议索引：

```text
entity_id unique
entity_type
canonical_name
status
```

### kg_relations

建议索引：

```text
relation_id unique
source_entity_id
target_entity_id
relation_type
status
confidence
weight
```

唯一约束：

```text
source_entity_id + relation_type + target_entity_id
```

### relation_evidence

建议索引：

```text
relation_id
evidence_id
support_type
```

---

## 6. Candidate 索引

### candidate_entities

建议索引：

```text
name
entity_type
status
confidence
created_at
```

### candidate_relations

建议索引：

```text
subject_name
object_name
predicate
status
confidence
created_at
```

审核页面通常按 status 和 created_at 查询。

---

## 7. Reasoning 索引

### event_instances

建议索引：

```text
event_id unique
event_type
status
occurred_at
confidence
```

### reasoning_paths

建议索引：

```text
path_id unique
event_id
stock_code
start_entity_id
end_entity_id
path_score
```

### stock_exposures

建议索引：

```text
event_id
stock_code
entity_id
exposure_score
confidence
```

### stock_event_scores

建议索引：

```text
event_id
stock_code
final_score
rank
label
created_at
```

---

## 8. Validation 索引

### event_validation_results

建议索引：

```text
event_id
stock_code
path_id
window
hit
calculated_at
```

### validation_summary

建议索引：

```text
summary_type
summary_key
window
updated_at
```

---

## 9. 查询缓存

可缓存以下结果：

- 个股知识卡。
- 热门实体邻居。
- 事件推理路径。
- Why This Stock 解释。
- 验证聚合统计。

缓存失效条件：

```text
kg_relations 更新
evidence 更新
stock_event_scores 更新
validation_summary 更新
```

---

## 10. 批量写入优化

后台任务写入应采用批量处理。

适用场景：

- 批量导入 evidence。
- 批量写入 candidate_relations。
- 批量更新 validation results。
- 批量生成 reasoning paths。

避免逐条提交事务。

---

## 11. SQLite 注意事项

SQLite 阶段需要注意：

- 避免多 worker 并发写入。
- 写任务尽量串行。
- 大批量写入使用事务。
- 定期备份。
- 控制单表无限增长。

---

## 12. PostgreSQL 优化方向

迁移 PostgreSQL 后可增加：

- JSONB 索引。
- Full-text search。
- Materialized View。
- Partition。
- pgvector。
- 更复杂聚合查询。

---

## 13. 设计原则

1. 索引服务真实查询场景。
2. 图谱查询重点索引 source 和 target。
3. 审核流程重点索引 status。
4. 事件页面重点索引 event_id。
5. 个股页面重点索引 stock_code。
6. 验证聚合重点索引 summary_type 和 window。
7. SQLite 阶段控制并发写入。

---

## 14. 结论

Indexing Performance 的目标是保证 V2 在数据量增加后仍然可用。

第一阶段通过合理索引和缓存即可支撑核心功能，后续再通过 PostgreSQL 和专用索引能力扩展性能。