# 04 Validation API

> 本文档定义 AStock V2 的验证结果 API。

---

## 1. Validation API 目标

Validation API 用于展示事件推理结果在历史行情中的验证表现。

它回答：

```text
同类事件过去是否有效？
某条路径历史表现如何？
某个标的对某类事件是否有稳定响应？
```

---

## 2. API 分组

统一前缀：

```text
/api/v2/validation
```

主要接口：

```text
GET /validation/events/{event_id}
GET /validation/stocks/{stock_code}
GET /validation/summary
GET /validation/event-types/{event_type}
GET /validation/paths/{path_id}
```

---

## 3. GET /validation/events/{event_id}

查询某个事件的验证结果。

返回：

```text
event_id
window
stock_code
absolute_return
benchmark_return
industry_return
excess_return_index
excess_return_industry
hit
status
```

---

## 4. GET /validation/stocks/{stock_code}

查询某个标的的历史事件响应。

参数：

```text
event_type
window
start_date
end_date
```

返回：

```text
stock_code
event_type
sample_count
hit_rate
avg_excess_return
preferred_window
response_strength
```

---

## 5. GET /validation/summary

查询聚合验证统计。

参数：

```text
summary_type
summary_key
window
```

summary_type：

```text
event_type
stock_code
entity_id
relation_type
path_pattern
industry
```

返回：

```text
sample_count
hit_count
hit_rate
avg_return
avg_excess_return_index
avg_excess_return_industry
median_return
max_return
min_return
```

---

## 6. GET /validation/event-types/{event_type}

查询事件类型验证表现。

返回：

```text
event_type
window
sample_count
hit_rate
avg_excess_return
confidence
weight_adjustment
```

---

## 7. GET /validation/paths/{path_id}

查询某条推理路径的历史验证表现。

返回：

```text
path_id
path_pattern
sample_count
hit_rate
avg_excess_return
weight_adjustment
recent_results
```

---

## 8. Validation DTO

标准 DTO：

```json
{
  "window": "T+3",
  "sample_count": 20,
  "hit_rate": 0.65,
  "avg_excess_return": 0.032,
  "confidence": 0.72
}
```

---

## 9. 特殊状态

验证结果状态包括：

```text
calculated
pending
missing_data
suspended
skipped
```

API 必须明确返回状态，不能把数据缺失误判为无效。

---

## 10. 设计原则

1. 同时返回绝对收益和超额收益。
2. 停牌和数据缺失必须单独标记。
3. 聚合统计必须说明样本数量。
4. 历史验证用于研究复盘和权重校准。
5. API 不负责实时计算验证结果，只读取已落库数据。

---

## 11. 结论

Validation API 让用户看到推理系统的历史有效性，是 V2 可信度闭环的重要接口。