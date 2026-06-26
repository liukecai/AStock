# 06 Deployment

> 本文档描述 AStock V2 的部署架构与演进路径。

---

## 1. 部署目标

V2 部署架构需要满足：

- 支持现有 FastAPI + Web 前端。
- 支持离线任务调度。
- 支持图谱数据存储。
- 支持任务状态监控。
- 支持后续从 SQLite 演进到 PostgreSQL。
- 支持未来拆分 Worker 和队列。

第一阶段不追求复杂微服务，优先保持可部署、可维护、可备份。

---

## 2. Phase 1 部署形态

Phase 1 推荐继续采用单机 Docker Compose。

```text
Docker Compose
├── backend
├── frontend
├── database
└── nginx
```

其中 backend 同时承担：

- API 服务。
- APScheduler 调度。
- 轻量离线任务。

这是 V2 初期最简单、最稳定的方式。

---

## 3. Phase 1 服务职责

### backend

负责：

- FastAPI。
- API 路由。
- 服务层逻辑。
- APScheduler。
- 图谱查询。
- 推理计算。
- 验证计算。

### frontend

负责：

- Web 页面。
- Dashboard。
- 事件路径展示。
- 个股解释页。

### database

第一阶段可继续使用 SQLite。

但需要为 PostgreSQL 迁移预留：

- SQLAlchemy 模型。
- Alembic migration。
- 避免 SQLite 专有语法。

### nginx

负责：

- 静态资源服务。
- API 反向代理。
- HTTPS 入口。

---

## 4. Phase 2 部署形态

当任务变重后，需要将 Worker 拆出。

```text
Docker Compose
├── backend-api
├── backend-worker
├── frontend
├── postgres
├── redis
└── nginx
```

### backend-api

只负责在线查询。

### backend-worker

负责：

- 行情更新。
- 新闻更新。
- 文档抽取。
- 图谱更新。
- 事件推理。
- 验证计算。

### redis

用于：

- 任务队列。
- 缓存。
- 分布式锁。

---

## 5. Phase 3 部署形态

当系统进入多任务、多数据源、多用户阶段，可进一步拆分服务。

```text
api-service
worker-service
extraction-service
graph-service
validation-service
web-service
postgres
redis
object-storage
```

Phase 3 不是 V2 必须目标，只作为演进方向。

---

## 6. 数据库演进

### 6.1 SQLite 阶段

适合：

- 个人部署。
- MVP。
- 小规模数据。
- 单任务写入。

限制：

- 并发写入弱。
- 数据量大后维护困难。
- 图谱查询能力有限。

### 6.2 PostgreSQL 阶段

适合：

- 多任务写入。
- 更复杂索引。
- 更稳定备份。
- 后续向量检索。

### 6.3 Neo4j 阶段

Neo4j 不作为 V2 第一阶段目标。

只有当图谱路径查询和关系规模明显超过关系型数据库能力后，再考虑引入。

---

## 7. 文件存储

V2 会产生更多原始材料：

- 年报 PDF。
- 招股书 PDF。
- 公告 PDF。
- 官网产品目录。
- 抽取结果。

建议采用本地文件目录作为 Phase 1 存储：

```text
data/
├── raw/
├── evidence/
├── reports/
├── announcements/
├── extraction_outputs/
└── backups/
```

后续可迁移到对象存储。

---

## 8. 配置管理

配置应统一放在：

```text
config/
├── data_sources.yaml
├── scheduler.yaml
├── graph.yaml
├── reasoning.yaml
├── scoring.yaml
└── extraction.yaml
```

敏感配置通过环境变量管理，不应写入仓库。

---

## 9. 备份策略

必须备份：

- 数据库。
- 图谱关系。
- Evidence。
- 抽取结果。
- 配置文件。

推荐每日盘后备份。

备份文件命名：

```text
backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## 10. 健康检查

系统至少提供：

```text
/health
/api/jobs/status
/api/system/version
```

健康检查应覆盖：

- API 是否可用。
- 数据库是否可连接。
- 最近任务是否正常。
- 数据是否过期。

---

## 11. 部署原则

1. 第一阶段保持简单。
2. API 与 Worker 可逐步拆分。
3. 数据库先兼容 SQLite，再迁移 PostgreSQL。
4. 抽取任务不进入实时请求链路。
5. 所有任务必须可观测。
6. 所有数据必须可备份和恢复。

---

## 12. 结论

AStock V2 部署不应一开始就复杂化。

推荐路径是：

```text
单体 Docker Compose
  ↓
API + Worker 拆分
  ↓
PostgreSQL + Redis
  ↓
独立图谱服务 / 抽取服务
```

这样可以在保持系统可运行的同时，为未来扩展预留空间。