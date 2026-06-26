# 05 Runtime

> 本文档描述 AStock V2 的运行时架构，包括离线任务、在线服务、调度流程和任务边界。

---

## 1. Runtime 总览

AStock V2 同时包含离线计算和在线查询两类运行时。

```text
Offline Runtime
  ↓
数据采集 / 证据构建 / 图谱更新 / 推理计算 / 验证计算

Online Runtime
  ↓
API 查询 / Web 展示 / 用户交互 / 解释查询
```

两类运行时必须解耦。

在线服务不应直接执行重型采集、LLM 抽取或批量推理任务。

---

## 2. Offline Runtime

离线运行时负责重计算和批处理。

主要任务包括：

- 行情更新。
- 新闻更新。
- 公告更新。
- Evidence 构建。
- LLM 抽取。
- Candidate Knowledge 合并。
- Knowledge Graph 更新。
- 批量事件推理。
- 收益验证计算。
- 任务日志归档。

---

## 3. Online Runtime

在线运行时负责低延迟查询。

主要能力包括：

- 查询事件列表。
- 查询股票详情。
- 查询图谱路径。
- 查询证据来源。
- 查询推理结果。
- 查询验证结果。
- 返回前端 DTO。

在线服务必须只读取已落库结果，避免请求期间执行大模型调用或长时间任务。

---

## 4. Scheduler

V2 可以继续使用 APScheduler 作为第一阶段调度器。

推荐任务：

```text
market_data_update
news_update
announcement_update
evidence_build
llm_extraction
kg_update
event_reasoning
validation_update
backup
```

每个任务必须记录：

- 任务名称。
- 开始时间。
- 结束时间。
- 状态。
- 错误信息。
- 处理数量。
- 输出结果摘要。

---

## 5. Job State

建议统一任务状态：

```text
pending
running
success
failed
skipped
partial_success
```

失败任务不得静默失败。

失败信息必须可以在 Web 任务中心查看。

---

## 6. LLM Runtime

LLM 调用属于离线任务。

LLM 不应出现在以下路径中：

```text
用户打开页面 -> API -> LLM -> 返回结果
```

正确方式：

```text
离线任务 -> LLM 抽取 -> 候选关系入库 -> 审核 / 校验 -> 图谱更新 -> 在线查询
```

这样可以避免：

- 页面响应变慢。
- 成本不可控。
- 输出不稳定。
- 难以审计。

---

## 7. Graph Update Runtime

图谱更新应采用批处理方式。

```text
Candidate Relations
  ↓
Deduplicate
  ↓
Merge Entity
  ↓
Merge Relation
  ↓
Update Confidence
  ↓
Write Graph
```

图谱更新必须可重复执行。

同一证据重复处理不应产生重复实体或重复关系。

---

## 8. Event Reasoning Runtime

事件推理可以分为两种模式：

### 8.1 Batch Reasoning

用于每天盘后批量处理新增事件。

```text
new_events
  ↓
reasoning_engine
  ↓
event_stock_scores
```

### 8.2 On-demand Reasoning

用于用户手动输入事件文本后进行临时推理。

On-demand 推理可以执行轻量图谱查询，但不应执行大规模 LLM 抽取。

---

## 9. Validation Runtime

Validation Engine 需要根据事件时间延迟执行。

例如：

```text
事件日 T
T+1：计算一天表现
T+3：计算三天表现
T+5：计算五天表现
T+10：计算十天表现
```

验证任务可每日盘后运行，检查是否有到期事件需要更新验证结果。

---

## 10. Runtime 边界

### API 请求中允许

- 查询数据库。
- 查询图谱路径。
- 读取已计算分数。
- 返回解释文本。

### API 请求中不允许

- 拉取外部行情。
- 拉取新闻。
- 解析 PDF。
- 调用 LLM 做长文本抽取。
- 批量更新图谱。
- 批量计算验证结果。

---

## 11. Runtime 监控

系统应提供任务监控能力：

- 最近一次行情更新时间。
- 最近一次新闻更新时间。
- 最近一次图谱更新时间。
- 最近一次推理任务状态。
- 最近一次验证任务状态。
- 失败任务列表。

这些信息应通过 API 和 Web 页面展示。

---

## 12. Runtime 演进

### Phase 1

继续使用 APScheduler + FastAPI 单体部署。

### Phase 2

将重型任务拆为 Worker。

### Phase 3

引入队列系统，例如 Redis Queue 或 Celery。

### Phase 4

将 LLM 抽取、图谱更新、验证计算拆分为独立服务。

---

## 13. 结论

AStock V2 的运行时设计原则是：

```text
重任务离线跑
轻查询在线跑
LLM 不进实时链路
图谱批量更新
验证延迟计算
任务状态可观测
```

这能保证系统在功能扩展后仍然稳定可维护。