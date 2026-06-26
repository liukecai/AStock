# 05 Job API

> 本文档定义 AStock V2 的后台任务与系统状态 API。

---

## 1. 目标

Job API 用于展示后台任务状态，包括：

- 行情更新。
- 新闻更新。
- 公告更新。
- Evidence 构建。
- 图谱更新。
- 事件推理。
- 验证计算。

---

## 2. API 分组

统一前缀：

```text
/api/v2/jobs
```

主要接口：

```text
GET /jobs
GET /jobs/{job_id}
GET /jobs/latest
GET /jobs/status
GET /system/health
GET /system/version
```

---

## 3. GET /jobs

查询任务运行记录。

参数：

```text
job_name
job_type
status
start_date
end_date
page
page_size
```

返回：

```text
job_id
job_name
job_type
status
started_at
finished_at
duration_seconds
processed_count
success_count
failed_count
```

---

## 4. GET /jobs/{job_id}

查询单次任务详情。

返回：

```text
job_id
job_name
job_type
status
started_at
finished_at
duration_seconds
processed_count
success_count
failed_count
error_message
summary
```

---

## 5. GET /jobs/latest

查询每类任务最近一次运行结果。

返回任务类型：

```text
market_data_update
news_update
announcement_update
evidence_build
kg_update
event_reasoning
validation_update
```

每个任务返回：

```text
status
started_at
finished_at
summary
```

---

## 6. GET /jobs/status

查询系统任务总览。

返回：

```text
running_jobs
failed_jobs_today
last_success_by_job
data_freshness
```

---

## 7. GET /system/health

健康检查接口。

返回：

```text
api_status
database_status
scheduler_status
last_market_update
last_kg_update
last_validation_update
```

---

## 8. GET /system/version

系统版本接口。

返回：

```text
app_version
api_version
schema_version
git_commit
build_time
```

---

## 9. Job 状态

统一状态：

```text
pending
running
success
failed
partial_success
skipped
```

---

## 10. 设计原则

1. 所有后台任务必须写入 job_runs。
2. API 只查询任务状态。
3. 健康检查必须覆盖数据库和调度器。
4. 失败任务必须返回错误摘要。
5. 数据新鲜度必须可观测。

---

## 11. 结论

Job API 是 V2 可观测性的基础。

没有任务状态接口，数据采集、图谱更新和验证闭环都难以运维。