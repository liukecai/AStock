# 04 Validation Tables

> 本文档定义 AStock V2 验证闭环相关数据库表。

---

## 1. 表设计目标

Validation Tables 用于记录事件发生后的市场表现，并将结果用于校准事件、路径和股票暴露度。

验证对象包括：

- 事件实例。
- 事件类型。
- 股票。
- 图谱路径。
- 行业。
- 关系类型。

---

## 2. event_validation_results

事件验证结果表。

```text
event_validation_results
```

建议字段：

```text
id
event_id
stock_code
path_id
event_date
trade_date_t0
window
absolute_return
benchmark_return
industry_return
excess_return_index
excess_return_industry
max_gain
max_drawdown
hit
status
calculated_at
created_at
updated_at
```

window 示例：

```text
T+1
T+3
T+5
T+10
```

---

## 3. validation_summary

验证聚合表。

```text
validation_summary
```

建议字段：

```text
id
summary_type
summary_key
window
sample_count
hit_count
hit_rate
avg_return
avg_excess_return_index
avg_excess_return_industry
median_return
max_return
min_return
updated_at
```

summary_type 示例：

```text
event_type
stock_code
entity_id
relation_type
path_pattern
industry
```

---

## 4. event_type_validation

事件类型验证表。

```text
event_type_validation
```

建议字段：

```text
id
event_type
window
sample_count
hit_rate
avg_excess_return
confidence
weight_adjustment
updated_at
```

用于校准不同事件类型的默认权重。

---

## 5. path_validation

路径验证表。

```text
path_validation
```

建议字段：

```text
id
path_pattern
start_entity_type
end_entity_type
relation_types_json
window
sample_count
hit_rate
avg_excess_return
weight_adjustment
updated_at
```

用于评估某类推理路径是否有效。

---

## 6. stock_response_profiles

股票事件响应画像表。

```text
stock_response_profiles
```

建议字段：

```text
id
stock_code
event_type
entity_id
sample_count
hit_rate
avg_excess_return
preferred_window
response_strength
updated_at
```

用于判断某只股票是否经常响应某类事件。

---

## 7. benchmark_returns

基准收益表。

```text
benchmark_returns
```

建议字段：

```text
id
benchmark_code
trade_date
return_1d
return_3d
return_5d
return_10d
created_at
```

benchmark_code 示例：

```text
000300.SH
000905.SH
000852.SH
```

---

## 8. industry_returns

行业收益表。

```text
industry_returns
```

建议字段：

```text
id
industry_code
industry_name
trade_date
return_1d
return_3d
return_5d
return_10d
created_at
```

用于计算相对行业超额收益。

---

## 9. 验证任务流程

```text
stock_event_scores
  ↓
wait for validation window
  ↓
load stock price
  ↓
load benchmark return
  ↓
load industry return
  ↓
calculate excess return
  ↓
write event_validation_results
  ↓
update validation_summary
```

---

## 10. 特殊情况处理

### 非交易日

事件日不是交易日时，使用下一交易日作为 T0。

### 停牌

停牌股票标记 status = suspended，不计入失败。

### 数据缺失

行情缺失时标记 status = missing_data，等待后续补算。

---

## 11. 回写目标

验证结果可用于回写：

```text
event_type_weight
relation_weight
path_weight
stock_response_weight
validation_score
```

但不直接删除事实关系。

---

## 12. 设计原则

1. 每个事件-股票-窗口都应独立记录。
2. 同时计算绝对收益和超额收益。
3. 聚合表用于快速查询历史有效性。
4. 停牌和数据缺失必须单独标记。
5. 验证结果用于校准权重，不直接否定事实关系。

---

## 13. 结论

Validation Tables 是 AStock V2 自学习能力的基础。

它们让系统可以从历史结果中判断哪些事件、路径和股票响应真正有效。