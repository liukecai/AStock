# V2 实现审查记录（2026-06-27）

## 审查范围

- 设计基线：`docs/architecture/v2/README.md`
- 代码范围：`26cd72f6..HEAD`
- 审查目标：
  - 检查 V2 实现是否与架构设计一致
  - 识别会导致运行时报错、数据不可读、链路失真或回归的问题
  - 为后续修复、验证、再次审查提供基线

## 结论摘要

当前这版 V2 已完成较大范围的纵向接入，包括：

- V2 API 路由骨架
- 事件推理引擎 MVP
- 候选实体/关系抽取
- 前端 V2 入口页面
- 模型服务中的 LLM 结构化抽取端点

但现阶段仍存在多项严重问题，主要集中在：

- V1/V2 schema 混用
- 新旧表名、列名不一致
- 上传输入链路方向枚举不兼容
- 本地 SQLite 启动路径不稳定
- 缺少覆盖 `/api/v2/*` 的回归测试

在这些问题修复前，不建议将该版本视为“可稳定验收”的 V2 实现。

## 严重问题

### P0. V2 读接口仍大量查询 V1 表，导致写入后的 V2 数据无法正常读取

现象：

- V2 写入链路已写入 `event_instances`、`event_impacts`、`stock_event_scores`
- 但 `/api/v2/events`、`/api/v2/stocks/*` 仍在读取 `events`、`commodity_impacts`、`event_stock_scores`

影响：

- V2 推理结果无法通过 V2 API 正常读出
- 前端 V2 页面可能为空、数据错乱，或在运行时直接报错

涉及文件：

- `backend/app/api_v2/events.py`
- `backend/app/api_v2/stocks.py`
- `backend/app/services/event_engine.py`
- `backend/app/models/v2_kg.py`

修复建议：

- 明确 V2 API 的唯一数据源，统一改为 V2 表
- 对事件详情、事件股票、股票解释链路统一字段语义
- 避免 V2 接口再依赖旧版 `events` / `event_stock_scores`

### P0. `/api/v2/validation` 查询了不存在的表名

现象：

- 代码查询 `validation_results`、`validation_summaries`
- 实际模型和迁移中的表名为 `event_validation_results`、`validation_summary`

影响：

- `/api/v2/validation/*` 路由当前不可用
- 实际请求会触发数据库错误

本地复现：

- 使用 `TestClient` 请求 `/api/v2/validation/summary?summary_type=relation`
- 触发 `sqlite3.OperationalError: no such table: validation_summaries`

涉及文件：

- `backend/app/api_v2/validation.py`
- `backend/app/models/v2_kg.py`

修复建议：

- 统一 API 查询表名与 ORM/迁移表名
- 补充最小 API 回归测试覆盖 validation 路由

### P0. 私有文本上传链路的方向枚举与表约束不兼容

现象：

- `model_service /extract/event` 返回方向值：`positive|negative`
- `/api/v2/input/upload` 将该值直接写入旧版 `events.direction`
- 旧版 `events.direction` 只接受 `benefit|harm`

影响：

- 一旦模型服务返回真实结构化结果，上传链路会在插入事件时失败
- “主动知识喂入”主路径当前不可靠

涉及文件：

- `model_service/app.py`
- `backend/app/api_v2/input.py`
- `backend/app/db.py`

修复建议：

- 在接入层统一方向标准
- 明确 V2 方向枚举，并在模型服务/API/DB 三层保持一致
- 若上传入口属于 V2，建议直接落到 V2 事件表而非旧版 `events`

## 高优先级问题

### P1. 旧版 `/api/events` 商品过滤已被破坏

现象：

- 查询条件改为 `event_impacts WHERE commodity=?`
- 但 `event_impacts` 实际只有 `entity_id`，没有 `commodity`

影响：

- `/api/events?commodity=copper` 会直接触发 SQL 错误
- 旧版事件驱动页面产生回归

本地复现：

- `GET /api/events?commodity=copper`
- 报错 `sqlite3.OperationalError: no such column: commodity`

涉及文件：

- `backend/app/api.py`
- `backend/app/models/v2_kg.py`

修复建议：

- 若旧接口要兼容 V2 数据，应通过 `event_impacts -> kg_entities.name` 关联过滤
- 同时处理 SQLite / PostgreSQL 的兼容 SQL

### P1. `/api/events` 的方向过滤对 SQLite 不兼容

现象：

- 代码直接使用 PostgreSQL 风格的 `jsonb_extract_path_text(...)`

影响：

- SQLite 测试/本地环境下查询可能失败
- 当前实现丢失了双后端兼容性

涉及文件：

- `backend/app/api.py`

修复建议：

- 在 DB 适配层处理 JSON 提取差异
- 或避免在列表过滤阶段依赖数据库 JSON 方言函数

### P1. SQLite / 本地启动路径存在重复建表风险

现象：

- `db.init_db()` 先执行 `Base.metadata.create_all()`
- 随后又执行手写 `SCHEMA`
- `Base.metadata` 已包含 V1 同名表

影响：

- 使用带 lifespan 的应用启动路径时，本地环境可能直接在启动阶段失败
- 不利于本地 Docker、测试、开发环境稳定性

本地复现：

- 通过 `TestClient(app)` 进入 lifespan
- 触发 `table stocks already exists` / `table news_items already exists`

涉及文件：

- `backend/app/db.py`
- `backend/app/models/__init__.py`

修复建议：

- 明确 SQLite 初始化策略：
  - 要么只走 ORM `create_all`
  - 要么只走手写 `SCHEMA`
- 避免两套同名建表机制同时生效

## 测试与验证观察

已验证：

- `PYTHONPATH=backend backend/.venv312/bin/pytest backend/tests/test_api.py -q`
- 结果：`2 passed`

说明：

- 现有测试未覆盖 `/api/v2/*`
- 现有测试也未覆盖完整 app lifespan 初始化
- 因此无法拦截本次 V2 引入的严重问题

## 修复优先级建议

建议按以下顺序处理：

1. 统一 V2 API 的读写表模型
2. 修复 validation API 表名错误
3. 修复上传文本链路的方向枚举与落表目标
4. 修复旧 `/api/events` 的兼容回归
5. 修复 SQLite 初始化冲突
6. 为 `/api/v2/events`、`/api/v2/validation`、上传链路补最小回归测试
7. 完成本地 Docker 部署验证

## 后续处理方式

本轮审查后续将按以下闭环推进：

1. 由子代理修复首批严重问题
2. 主线程集成修改并执行本地 Docker 验证
3. 再次进行实现审查
4. 若仍存在严重问题，继续修复与复审，直到无严重问题为止
