# 05 Phase 5 Validation Loop

> Phase 5 目标：建立事件推理结果的市场验证闭环。

---

## 1. 阶段目标

Phase 5 用于记录事件发生后相关标的的表现，并形成可聚合的验证结果。

目标链路：

```text
stock_event_scores
  ↓
price data
  ↓
event_validation_results
  ↓
validation_summary
  ↓
weight calibration
```

---

## 2. 开发任务

新增模块：

```text
validation_engine.py
return_calculator.py
benchmark_service.py
validation_summary_service.py
```

新增表：

```text
event_validation_results
validation_summary
event_type_validation
path_validation
stock_response_profiles
```

---

## 3. 验证窗口

默认窗口：

```text
T+1
T+3
T+5
T+10
```

---

## 4. 计算指标

```text
absolute_return
benchmark_return
industry_return
excess_return_index
excess_return_industry
max_gain
max_drawdown
hit
```

---

## 5. 特殊情况

必须处理：

```text
非交易日
停牌
行情缺失
新股数据不足
```

这些情况必须有明确 status。

---

## 6. 验收用例

对一个已推理事件，计算候选标的 T+1、T+3、T+5 的表现，并写入 validation 表。

---

## 7. 验收标准

1. 能读取事件推理结果。
2. 能定位事件 T0 交易日。
3. 能计算多窗口收益。
4. 能计算超额收益。
5. 能写入验证结果。
6. 能生成聚合统计。
7. Web 或 API 能查询验证结果。

---

## 8. 风险控制

1. 数据缺失不等于验证失败。
2. 停牌不计入失败样本。
3. 样本数不足必须提示。
4. 验证结果只校准权重，不直接删除事实关系。

---

## 9. 结论

Phase 5 让 V2 从一次性推理变成可复盘、可校准的闭环系统。