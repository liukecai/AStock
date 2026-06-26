# 06 API Design

> 本目录定义 AStock V2 的 API 设计。
>
> API 层的目标是把 Evidence、Knowledge Graph、Reasoning Engine、Validation Loop 的能力稳定地暴露给 Web 前端和后续外部调用方。

---

## 文档范围

```text
06_API_Design/
├── README.md
├── 00_Overview.md
├── 01_Graph_API.md
├── 02_Event_API.md
├── 03_Stock_Explain_API.md
├── 04_Validation_API.md
├── 05_Job_API.md
├── 06_DTO_Error_Design.md
└── 07_ADR.md
```

---

## 阅读顺序

1. `00_Overview.md`：理解 API 层总体设计原则。
2. `01_Graph_API.md`：理解图谱实体、关系、路径查询接口。
3. `02_Event_API.md`：理解事件列表、事件详情、事件推理接口。
4. `03_Stock_Explain_API.md`：理解个股解释、暴露度、原因路径接口。
5. `04_Validation_API.md`：理解历史验证和统计接口。
6. `05_Job_API.md`：理解后台任务、调度状态和系统健康接口。
7. `06_DTO_Error_Design.md`：理解统一 DTO 与错误响应设计。
8. `07_ADR.md`：理解 API 设计关键决策。

---

## API 层职责

API 层负责：

- 对前端提供稳定数据契约。
- 屏蔽数据库表结构细节。
- 组织领域服务输出 DTO。
- 返回图谱路径、事件推理、股票解释、验证结果。
- 提供任务状态和系统健康信息。

API 层不负责：

- 直接采集外部数据。
- 直接调用 LLM 做长文本抽取。
- 直接修改图谱底层表。
- 在请求中执行重型批处理。
- 直接生成买卖建议。

---

## API 分组

```text
/api/v2/graph
/api/v2/events
/api/v2/stocks
/api/v2/validation
/api/v2/jobs
/api/v2/system
```

---

## 设计原则

1. API 只暴露领域语义，不暴露数据库表细节。
2. 所有响应必须使用统一 DTO。
3. 所有错误必须使用统一错误结构。
4. 重型计算必须离线完成，API 只查询结果。
5. 图谱路径必须返回节点、边、证据和分数。
6. 个股解释必须能回答 Why This Stock。
7. API 必须版本化，默认使用 `/api/v2`。

---

## 核心页面与 API 映射

```text
Event Dashboard
  -> /api/v2/events
  -> /api/v2/events/{event_id}
  -> /api/v2/events/{event_id}/stocks

Supply Chain Explorer
  -> /api/v2/graph/entities/{entity_id}
  -> /api/v2/graph/entities/{entity_id}/neighbors
  -> /api/v2/graph/paths

Stock Detail
  -> /api/v2/stocks/{stock_code}/knowledge
  -> /api/v2/stocks/{stock_code}/events
  -> /api/v2/stocks/{stock_code}/explain

Validation Panel
  -> /api/v2/validation/events/{event_id}
  -> /api/v2/validation/summary

Job Monitor
  -> /api/v2/jobs
  -> /api/v2/jobs/{job_id}
```

---

## 成功标准

API 层完成后，前端应能：

1. 展示事件列表和事件详情。
2. 展示事件影响路径。
3. 展示候选股票及分数拆解。
4. 展示某只股票为什么与事件相关。
5. 展示每条路径背后的证据。
6. 展示历史验证表现。
7. 展示后台任务运行状态。