# 05 Validation Panel

> 本文档定义 AStock V2 Validation Panel 设计。

---

## 1. 页面目标

Validation Panel 用于展示事件推理结果的历史验证表现。

---

## 2. 核心内容

```text
Validation Summary
Event Type Statistics
Path Statistics
Stock Response Profile
Recent Cases
Window Comparison
```

---

## 3. Validation Summary

展示总览指标：

```text
sample_count
hit_rate
avg_return
avg_excess_return
median_return
max_drawdown
```

所有统计必须展示样本数。

---

## 4. Event Type Statistics

按事件类型展示：

```text
event_type
sample_count
hit_rate
avg_excess_return
best_window
confidence
```

---

## 5. Path Statistics

按路径模式展示：

```text
path_pattern
sample_count
hit_rate
avg_excess_return
weight_adjustment
```

---

## 6. Stock Response Profile

展示某个标的历史响应：

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

## 7. Recent Cases

展示最近验证案例：

```text
event_title
stock_code
event_date
window
absolute_return
excess_return
hit
```

---

## 8. Window Comparison

展示不同窗口对比：

```text
T+1
T+3
T+5
T+10
```

每个窗口展示：

```text
sample_count
hit_rate
avg_excess_return
```

---

## 9. 状态提示

验证状态包括：

```text
calculated
pending
missing_data
suspended
skipped
```

页面不能把 pending 或 missing_data 显示为失败。

---

## 10. 设计原则

1. 所有验证统计必须展示样本数。
2. 绝对收益和超额收益分开展示。
3. 不同时间窗口必须可比较。
4. 数据缺失和停牌必须单独标记。
5. 验证结果用于复盘和权重校准。

---

## 11. 结论

Validation Panel 是 V2 的可信度展示层。