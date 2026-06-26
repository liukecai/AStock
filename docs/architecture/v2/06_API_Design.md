# 06 API Design

> AStock V2 API 设计。
>
> API 层的目标是将 Evidence、Knowledge Graph、Reasoning Engine、Validation Loop 的能力稳定地暴露给 Web 前端和外部调用方。
>
> 前置阅读：[05_Database_Design.md](./05_Database_Design.md)（理解底层数据结构），[03_Reasoning_Engine.md](./03_Reasoning_Engine.md)（理解推理输出）。

---

## 1. 总体设计

### 1.1 API 分组

```text
/api/v2/graph       ← 图谱实体、关系、路径查询
/api/v2/events      ← 事件列表、详情、推理结果
/api/v2/stocks      ← 个股知识、解释、暴露度
/api/v2/validation  ← 历史验证结果
/api/v2/jobs        ← 后台任务状态
/api/v2/system      ← 系统健康
```

### 1.2 设计原则

| 原则 | 说明 |
|---|---|
| 版本化 | 统一使用 `/api/v2` 前缀，与 V1 隔离 |
| DTO 输出 | 不直接返回 ORM 对象，屏蔽数据库结构 |
| 统一响应 | 所有接口使用统一 `success/data/error/meta` 结构 |
| 重任务离线 | API 只查询已落库结果，不执行 LLM/批处理 |
| 可解释 | 解释接口返回路径、证据和分数拆解 |
| 分页 | 所有列表接口支持 `page` + `page_size` |
| 路径限深 | Graph Path 查询默认 `max_depth ≤ 4` |

---

## 2. Graph API

### GET /api/v2/graph/entities/{entity_id}

返回实体详情（名称、类型、别名、状态、描述）。

### GET /api/v2/graph/entities/{entity_id}/neighbors

返回一跳邻居（关系列表 + 邻居实体），支持按 `relation_type` 过滤。用于 Supply Chain Explorer。

### GET /api/v2/graph/entities/search?q={keyword}

按名称/别名模糊搜索实体，支持 `entity_type` 过滤。

### GET /api/v2/graph/paths?source={id}&target={id}&max_depth=4

返回两实体间的路径列表，每条路径包含：节点列表、关系列表、权重、置信度、证据。

### GET /api/v2/graph/relations/{relation_id}

返回关系详情（起终点、类型、权重、置信度、证据列表）。

### GET /api/v2/graph/relations/{relation_id}/evidence

返回关系的所有证据来源（含 `support_type`、`extracted_text`、`source_url`）。

---

## 3. Event API

### GET /api/v2/events

事件列表，支持：`event_type` / `date_range` / `page` / `page_size` / `sort_by`。

### GET /api/v2/events/{event_id}

事件详情（类型、标题、强度、方向、影响实体、来源证据）。

### GET /api/v2/events/{event_id}/impacts

事件影响实体列表（直接和间接影响）。

### GET /api/v2/events/{event_id}/paths

事件推理路径列表（从影响实体到候选股票的图谱路径）。

### GET /api/v2/events/{event_id}/stocks

事件候选股票列表（含 `exposure_score` / `final_score` / `score_breakdown` / `reason_path`）。

---

## 4. Stock Explain API

### GET /api/v2/stocks/{stock_code}/knowledge

个股知识卡（公司产品、产业链路径、关系列表、证据来源、置信度）。

### GET /api/v2/stocks/{stock_code}/events

个股相关事件列表。

### GET /api/v2/stocks/{stock_code}/explain?event_id={id}

个股事件解释（reason_paths + evidence_list + score_breakdown + validation_summary + 解释文本）。

核心回答：**为什么这只股票与该事件相关？**

---

## 5. Validation API

### GET /api/v2/validation/events/{event_id}

事件级验证结果（各窗口的候选股票表现、绝对收益、超额收益、命中率）。

### GET /api/v2/validation/events/{event_id}/stocks/{stock_code}

单只股票在某事件下的验证详情。

### GET /api/v2/validation/summary?type={summary_type}&key={key}

验证聚合统计（按 event_type / entity / path / stock 聚合的胜率、平均超额收益、样本数）。

---

## 6. Job API

### GET /api/v2/jobs

任务列表（`job_name` / `status` / `started_at` / `finished_at`），支持 `status` 过滤和分页。

### GET /api/v2/jobs/{job_id}

任务详情（运行时长、处理数量、错误信息、摘要）。

### GET /api/v2/jobs/latest

各任务类型最近一次执行结果（用于数据新鲜度展示）。

### GET /api/v2/system/health

系统健康（API 可用性、数据库连接、最近任务状态、数据新鲜度）。

---

## 7. DTO 与错误设计

### 7.1 统一成功响应

```json
{ "success": true, "data": {}, "error": null, "meta": {} }
```

### 7.2 统一失败响应

```json
{
  "success": false,
  "data": null,
  "error": { "code": "ENTITY_NOT_FOUND", "message": "Entity not found", "details": {} },
  "meta": {}
}
```

### 7.3 分页 meta

```json
{ "page": 1, "page_size": 20, "total": 100, "has_next": true }
```

### 7.4 错误码

```text
BAD_REQUEST / VALIDATION_ERROR / ENTITY_NOT_FOUND / EVENT_NOT_FOUND
STOCK_NOT_FOUND / RELATION_NOT_FOUND / JOB_NOT_FOUND
INTERNAL_ERROR / SERVICE_UNAVAILABLE
```

### 7.5 约定

| 项目 | 约定 |
|---|---|
| 时间格式 | ISO 8601（`2026-06-27T10:30:00+08:00`） |
| 分数范围 | confidence 0.0~1.0，exposure_score 0.0~1.0，final_score 0~100 |
| 空值 | 使用 `null`，不用空字符串；列表缺失返回 `[]` |

### 7.6 核心 DTO

```text
EntityDTO / RelationDTO / EvidenceDTO / EventDTO / ReasonPathDTO
StockExposureDTO / StockScoreDTO / ValidationResultDTO / JobRunDTO
```

---

## 8. 核心页面与 API 映射

| 页面 | 调用 API |
|---|---|
| Event Dashboard | `/events` + `/events/{id}` + `/events/{id}/stocks` |
| Supply Chain Explorer | `/graph/entities/{id}` + `/graph/entities/{id}/neighbors` + `/graph/paths` |
| Stock Detail | `/stocks/{code}/knowledge` + `/stocks/{code}/events` + `/stocks/{code}/explain` |
| Validation Panel | `/validation/events/{id}` + `/validation/summary` |
| Job Monitor | `/jobs` + `/jobs/{id}` + `/jobs/latest` |

→ 页面设计详见 [07_Web_Design.md](./07_Web_Design.md)。

---

## 9. 架构决策记录（ADR）

### ADR-001：API 统一使用 /api/v2 前缀

与旧接口隔离，便于版本演进和前端迁移。

### ADR-002：API 返回 DTO，不直接返回 ORM 对象

隐藏数据库细节，响应结构稳定。

### ADR-003：统一响应结构

`success/data/error/meta` 四字段结构，前端处理简单，错误处理统一。

### ADR-004：重型任务不在 API 请求中执行

API 只读取已计算结果，重型任务由后台调度执行。API 响应稳定，任务可重试。

### ADR-005：Explain API 必须返回路径和证据

返回 `reason_paths` / `evidence_list` / `score_breakdown` / `validation_summary`，可解释性强。

### ADR-006：列表接口必须分页

避免大响应，提高前端性能。

### ADR-007：Graph Path 查询必须限制深度

默认 `max_depth ≤ 4`，查询可控，结果更可解释。
