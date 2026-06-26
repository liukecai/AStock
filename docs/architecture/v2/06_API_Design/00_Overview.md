# 00 Overview

> 本文档定义 AStock V2 API 层总体设计。

---

## 1. API 层定位

API 层是后端领域能力与前端页面之间的稳定契约。

V2 API 不应只是数据库表的简单 CRUD，而应围绕业务语义组织：

```text
Graph API
Event API
Stock Explain API
Validation API
Job API
System API
```

---

## 2. API 设计目标

API 层需要支持：

- 图谱实体查询。
- 图谱路径查询。
- 事件列表查询。
- 事件详情查询。
- 事件影响股票查询。
- 个股知识卡查询。
- 个股解释查询。
- 验证结果查询。
- 后台任务状态查询。

---

## 3. API 不做什么

API 层不应执行：

- 外部数据采集。
- PDF 解析。
- 长文本 LLM 抽取。
- 大规模图谱更新。
- 批量验证计算。
- 实盘交易动作。

这些任务应由离线 Worker 或调度任务完成。

---

## 4. API 版本

V2 API 统一使用：

```text
/api/v2
```

示例：

```text
/api/v2/events
/api/v2/graph/entities/{entity_id}
/api/v2/stocks/{stock_code}/explain
```

未来如有破坏性变更，可新增 `/api/v3`。

---

## 5. 响应结构

所有 API 响应应使用统一结构：

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {}
}
```

失败响应：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Entity not found",
    "details": {}
  },
  "meta": {}
}
```

---

## 6. DTO 原则

API 返回 DTO，不直接返回 ORM 对象。

DTO 应满足：

- 字段稳定。
- 前端友好。
- 隐藏内部表结构。
- 包含必要解释信息。
- 支持版本演进。

---

## 7. 分页规范

列表接口应支持分页：

```text
page
page_size
sort_by
sort_order
```

响应 meta：

```json
{
  "page": 1,
  "page_size": 20,
  "total": 100
}
```

---

## 8. 查询过滤

常见过滤参数：

```text
status
event_type
stock_code
entity_type
start_date
end_date
min_score
min_confidence
```

过滤参数必须显式定义，避免任意 SQL 风险。

---

## 9. API 与 Service 层关系

API Controller 只负责：

- 参数校验。
- 调用 Service。
- 返回 DTO。

业务逻辑应在 Service 层。

```text
API Router
  ↓
Service Layer
  ↓
Repository / Database
```

---

## 10. API 性能原则

1. 高频接口必须使用索引。
2. 事件详情页避免 N+1 查询。
3. 图谱路径可读取缓存。
4. 长路径查询限制 max_depth。
5. 列表接口必须分页。
6. 前端解释接口应读取已计算结果。

---

## 11. 安全原则

第一阶段主要是自用系统，但仍应遵守：

- 不暴露环境变量。
- 不返回内部堆栈。
- 不允许任意 SQL 查询。
- 不在 API 中返回敏感配置。
- 写操作后续需要鉴权。

---

## 12. 结论

AStock V2 API 的目标是提供稳定的领域接口，而不是暴露数据库。

API 层应让前端专注展示事件、路径、证据和验证结果，而不关心后端内部数据结构。