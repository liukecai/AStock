# 05 Migration Strategy

> 本文档定义 AStock V2 数据库迁移策略。

---

## 1. 迁移目标

AStock V2 第一阶段允许继续使用 SQLite。

但数据库设计必须为 PostgreSQL 预留空间。

迁移目标：

```text
SQLite MVP
  ↓
SQLite + Alembic
  ↓
PostgreSQL
  ↓
PostgreSQL + pgvector / graph extension
```

---

## 2. Phase 1：SQLite MVP

适用场景：

- 单人开发。
- 小规模数据。
- 快速迭代。
- 本地部署。

要求：

- 使用 SQLAlchemy ORM。
- 避免 SQLite 专有语法。
- 所有表包含 created_at / updated_at。
- 所有迁移脚本可重复执行。

---

## 3. Phase 2：Alembic 管理 Schema

当 V2 表结构稳定后，引入 Alembic。

目标：

- 表结构版本化。
- 支持回滚。
- 支持开发和生产环境一致。
- 支持后续迁移 PostgreSQL。

迁移命名建议：

```text
001_create_core_tables
002_create_evidence_tables
003_create_kg_tables
004_create_reasoning_tables
005_create_validation_tables
```

---

## 4. Phase 3：PostgreSQL 迁移

触发条件：

- SQLite 写入锁频繁出现。
- 图谱数据量明显增加。
- 多任务并发写入。
- 需要更复杂索引。
- 需要更稳定备份。

迁移步骤：

```text
freeze schema
  ↓
create PostgreSQL schema
  ↓
export SQLite data
  ↓
transform data types
  ↓
import PostgreSQL
  ↓
verify row counts
  ↓
switch connection string
```

---

## 5. 类型兼容策略

避免使用不可移植类型。

JSON 字段第一阶段可用 TEXT 保存 JSON 字符串。

迁移 PostgreSQL 后可升级为 JSONB。

字段建议：

```text
aliases_json TEXT -> JSONB
score_breakdown_json TEXT -> JSONB
nodes_json TEXT -> JSONB
edges_json TEXT -> JSONB
```

---

## 6. ID 策略

建议同时使用：

```text
id: database primary key
business_id: external stable id
```

例如：

```text
id
entity_id
relation_id
event_id
path_id
evidence_id
```

数据库主键可自增，业务 ID 保持稳定。

---

## 7. 数据迁移校验

迁移后必须校验：

- 表数量。
- 行数量。
- 外键关系。
- 核心查询结果。
- 图谱路径查询。
- 事件推理结果。
- 验证结果。

---

## 8. 回滚策略

迁移前必须备份：

```text
SQLite database
raw evidence files
config files
migration logs
```

PostgreSQL 上线后，保留 SQLite 只读备份一段时间。

---

## 9. 环境配置

数据库连接通过环境变量配置：

```text
DATABASE_URL
```

示例：

```text
sqlite:///data/astock.db
postgresql://user:password@host:5432/astock
```

代码不得硬编码数据库类型。

---

## 10. 设计原则

1. 第一阶段保持 SQLite 简单可用。
2. 通过 SQLAlchemy 隔离数据库差异。
3. 所有 Schema 变化必须 migration 化。
4. JSON 字段先 TEXT 后 JSONB。
5. 迁移前必须备份。
6. 迁移后必须校验核心查询。

---

## 11. 结论

AStock V2 数据库迁移策略是渐进式的。

先保证功能落地，再通过 Schema 版本化和 PostgreSQL 迁移支撑更大规模数据与并发任务。