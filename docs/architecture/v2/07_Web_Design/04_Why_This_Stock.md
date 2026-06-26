# 04 Why This Stock

> 本文档定义 AStock V2 的关联解释模块设计。

---

## 1. 模块目标

该模块用于解释某个标的与某个事件之间的关联原因。

---

## 2. 核心内容

```text
Event Summary
Stock Summary
Final Score
Score Breakdown
Reason Paths
Evidence List
Validation Summary
Confidence Warning
```

---

## 3. Event Summary

展示：

```text
event_title
event_type
target_entities
intensity
confidence
occurred_at
```

---

## 4. Stock Summary

展示：

```text
stock_code
stock_name
company_name
industry
sector
```

---

## 5. Final Score

展示：

```text
final_score
rank
label
confidence
```

final_score 和 confidence 必须分开展示。

---

## 6. Score Breakdown

展示：

```text
event_score
exposure_score
trend_score
sentiment_score
volume_score
validation_score
```

---

## 7. Reason Paths

展示事件到标的的推理路径。

路径格式：

```text
Event Target
  ↓
Entity
  ↓
Company
  ↓
Stock
```

每条边展示：

```text
relation_type
weight
confidence
evidence_count
```

---

## 8. Evidence List

展示支持路径的证据：

```text
source_type
title
published_at
extracted_text
support_type
```

---

## 9. Validation Summary

展示历史验证：

```text
sample_count
hit_rate
avg_excess_return
best_window
recent_cases
```

样本数不足时必须提示。

---

## 10. Confidence Warning

当 confidence 较低时，页面必须提示：

```text
该结果基于低置信路径或弱证据，请结合更多信息判断。
```

---

## 11. 页面交互

支持：

- 点击路径节点进入图谱探索。
- 点击证据查看来源。
- 点击事件返回事件详情。
- 点击分数项查看计算说明。

---

## 12. 设计原则

1. 先解释路径，再展示分数。
2. 分数和置信度分开展示。
3. 证据必须可见。
4. 低置信结果必须提示。
5. 历史验证必须显示样本数。
6. 模块只做研究解释。

---

## 13. 结论

该模块把事件、图谱、分数、证据和验证整合为一条可理解的研究链路。