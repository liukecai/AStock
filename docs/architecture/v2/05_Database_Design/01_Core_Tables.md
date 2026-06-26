# 01 Core Tables

> 本文档定义 AStock V2 的基础核心表。

---

## 1. Core Tables 目标

Core Tables 用于保存系统中最基础、最稳定、被多个模块复用的数据。

包括：

- 股票基础信息。
- 公司基础信息。
- 数据源配置。
- 任务运行记录。
- 系统审计信息。

---

## 2. stocks

股票基础表。

```text
stocks
```

建议字段：

```text
id
stock_code
stock_name
exchange
market
industry
sector
list_date
status
created_at
updated_at
```

说明：

- stock_code 使用统一格式，例如 `600160.SH`。
- status 用于标记 active、delisted、suspended 等状态。

---

## 3. companies

公司基础表。

```text
companies
```

建议字段：

```text
id
company_name
short_name
legal_name
stock_code
website
description
status
created_at
updated_at
```

Company 与 Stock 可以通过 stock_code 或 kg relation 关联。

后续在 Knowledge Graph 中应使用：

```text
Company -> listed_as -> Stock
```

---

## 4. data_sources

数据源表。

```text
data_sources
```

建议字段：

```text
id
source_name
source_type
base_url
priority
confidence_base
enabled
config_json
created_at
updated_at
```

source_type 示例：

```text
market_data
announcement
rss
news
annual_report
company_website
manual
```

---

## 5. job_runs

任务运行记录表。

```text
job_runs
```

建议字段：

```text
id
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
summary_json
created_at
```

status 枚举：

```text
pending
running
success
failed
partial_success
skipped
```

---

## 6. system_configs

系统配置表。

```text
system_configs
```

建议字段：

```text
id
config_key
config_value
config_type
description
enabled
created_at
updated_at
```

适合保存非敏感配置。

敏感配置仍应通过环境变量管理。

---

## 7. audit_logs

通用审计日志表。

```text
audit_logs
```

建议字段：

```text
id
module_name
action
object_type
object_id
old_value
new_value
operator
reason
created_at
```

operator 示例：

```text
system
scheduler
llm_extractor
manual_admin
validation_engine
```

---

## 8. 通用字段规范

大多数业务表应包含：

```text
id
status
created_at
updated_at
```

需要审计的表应增加：

```text
created_by
updated_by
reviewed_by
reviewed_at
```

---

## 9. 命名规范

表名使用复数小写蛇形命名。

示例：

```text
kg_entities
kg_relations
event_instances
stock_exposures
```

字段名使用小写蛇形命名。

---

## 10. 设计原则

1. Core Tables 保持稳定，不频繁变化。
2. 股票和公司基础信息与图谱关系解耦。
3. 任务运行必须可追踪。
4. 配置与密钥分离。
5. 所有自动化任务应写入 job_runs。
6. 关键变更应写入 audit_logs。

---

## 11. 结论

Core Tables 是 V2 的基础设施层。

它们不承载复杂推理逻辑，但为 Evidence、Graph、Reasoning、Validation 提供统一基础对象。