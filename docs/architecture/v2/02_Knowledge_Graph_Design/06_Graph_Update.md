# 06 Graph Update

> 本文档定义 AStock V2 Knowledge Graph 的更新、合并、过期和校准机制。

---

## 1. Graph Update 目标

Knowledge Graph 不是一次性构建完成的静态数据，而是持续更新的长期知识库。

更新来源包括：

- 新年报。
- 新公告。
- 新招股书。
- 官网产品变化。
- 新新闻事件。
- 新 LLM 抽取结果。
- 人工修正。
- 市场验证反馈。

Graph Update 的目标是让图谱长期保持：

```text
可追溯
可合并
可回滚
可校准
可解释
```

---

## 2. 更新类型

V2 第一阶段支持以下更新类型：

```text
entity_upsert
relation_upsert
evidence_append
confidence_update
weight_update
status_update
alias_merge
validation_feedback
```

---

## 3. Entity Upsert

实体更新应采用 upsert。

判断重复实体时使用：

- canonical_name。
- aliases。
- entity_type。
- stock_code。
- external_id。

示例：

```text
WF6
Tungsten Hexafluoride
六氟化钨
```

应合并为同一实体。

---

## 4. Relation Upsert

关系唯一键建议：

```text
source_entity_id + relation_type + target_entity_id
```

如果关系已存在：

- 不创建重复关系。
- 追加 evidence。
- 更新 confidence。
- 更新 weight。
- 更新 updated_at。

如果关系不存在：

- 创建 candidate 或 active relation。

---

## 5. Evidence Append

新证据支持已有关系时，追加到 relation_evidence。

示例：

```text
已有关系：中船特气 produces 六氟化钨
新证据：2025 年报再次披露该产品
```

处理：

```text
追加 evidence
提高 confidence
更新 relation updated_at
```

---

## 6. Confidence Update

confidence 表示关系真实性可信度。

更新依据：

- 新增高质量证据。
- 多来源交叉验证。
- 证据过期。
- 冲突证据。
- 人工审核。

建议规则：

```text
高质量新增证据 -> 提高 confidence
低质量重复新闻 -> 不明显提高 confidence
冲突证据 -> 降低 confidence
业务剥离公告 -> 标记 deprecated 或降低 confidence
```

---

## 7. Weight Update

weight 表示关系在事件传播中的强度。

weight 不等于 confidence。

例如：

```text
某公司确实生产某产品：confidence 高
但该产品收入占比很小：weight 低
```

weight 可由以下信息更新：

- 主营收入占比。
- 产品产能。
- 行业地位。
- 历史事件验证结果。
- 市场反应强弱。

---

## 8. Status Update

关系状态包括：

```text
candidate
active
rejected
deprecated
validated
needs_review
```

状态转换：

```text
candidate -> active
candidate -> rejected
active -> deprecated
active -> needs_review
active -> validated
```

状态变更必须记录原因。

---

## 9. Alias Merge

Alias Merge 用于处理重复实体。

流程：

```text
detect alias
  ↓
choose canonical entity
  ↓
move aliases
  ↓
redirect relations
  ↓
mark old entity as merged
```

合并不能直接删除旧实体，否则会破坏历史关系和证据追溯。

---

## 10. Conflict Handling

冲突来源示例：

```text
证据 A：公司生产某产品
证据 B：公司已出售该业务
```

处理方式：

1. 保留两条证据。
2. 将关系标记为 needs_review。
3. 降低 confidence。
4. 前端解释中展示冲突提示。
5. 等待人工或新公告确认。

---

## 11. Validation Feedback

市场验证结果可回写图谱。

示例：

```text
事件：六氟化钨供应紧张
候选股票：中船特气
结果：多次 T+3 超额收益显著
```

处理：

```text
提高相关路径 weight
标记 relation 为 validated
更新 event_type impact weight
```

如果多次验证无效：

```text
降低 weight
保留 confidence
标记 weak_market_response
```

注意：

市场表现只能校准 impact weight，不能直接否定事实关系。

---

## 12. 幂等性

Graph Update 必须幂等。

同一 evidence 重复处理时：

- 不重复创建实体。
- 不重复创建关系。
- 不重复追加 evidence。
- 不重复提高 confidence。

依赖：

```text
content_hash
evidence_id
relation unique key
```

---

## 13. 审计日志

图谱更新必须记录日志。

日志字段：

```text
operation_type
entity_id
relation_id
old_value
new_value
reason
operator
created_at
```

operator 可以是：

```text
system
llm_extractor
yaml_loader
manual_admin
validation_engine
```

---

## 14. Graph Update 设计原则

1. 更新优先合并，不重复创建。
2. confidence 和 weight 分离更新。
3. 市场验证只校准影响权重，不直接改写事实。
4. 冲突关系不删除，应进入审核状态。
5. 所有重要更新必须保留审计日志。
6. 图谱更新必须幂等。

---

## 15. 结论

Graph Update 决定知识图谱是否能长期维护。

没有更新机制，图谱会变成一次性规则库。

有了更新、合并、证据、验证和审计，图谱才能成为 AStock 的长期核心资产。