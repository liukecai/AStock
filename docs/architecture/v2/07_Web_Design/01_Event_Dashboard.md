# 01 Event Dashboard

> 本文档定义 AStock V2 Event Dashboard 的页面设计。

---

## 1. 页面目标

Event Dashboard 用于展示当前市场中的结构化事件和系统推理结果。

该页面回答：

```text
今天发生了哪些重要事件？
这些事件影响哪些产业链？
哪些股票进入观察列表？
```

---

## 2. 核心模块

Event Dashboard 包含：

```text
Event Filter
Event List
Event Detail Drawer
Impacted Entity Panel
Candidate Stock Table
Reason Path Preview
Validation Summary
```

---

## 3. Event Filter

筛选条件：

```text
event_type
status
intensity
min_confidence
start_date
end_date
keyword
```

默认展示最近事件，按 occurred_at 和 final_score 排序。

---

## 4. Event List

事件卡片展示：

```text
title
event_type
intensity
confidence
occurred_at
source_count
affected_entity_count
candidate_stock_count
```

事件卡片需要用颜色或标签区分：

- 高强度事件。
- 低置信事件。
- 待验证事件。
- 已验证事件。

---

## 5. Event Detail Drawer

点击事件后展开详情。

内容包括：

```text
事件摘要
事件类型
目标实体
影响方向
事件强度
来源证据
抽取置信度
标准化结果
```

---

## 6. Impacted Entity Panel

展示事件影响实体：

```text
商品
材料
行业
概念
公司
```

每个实体展示：

```text
entity_name
entity_type
impact_direction
impact_weight
confidence
```

---

## 7. Candidate Stock Table

候选股票表展示：

```text
rank
stock_code
stock_name
final_score
exposure_score
trend_score
validation_score
confidence
label
```

表格应支持：

- 按 final_score 排序。
- 按 confidence 排序。
- 按 exposure_score 过滤。
- 点击进入 Why This Stock。

---

## 8. Reason Path Preview

每只候选股票展示一条主路径预览。

示例：

```text
事件目标实体 -> 材料 -> 公司 -> 股票
```

路径预览不需要展示所有细节，但应可点击进入完整路径。

---

## 9. Validation Summary

事件面板展示历史验证摘要：

```text
同类事件样本数
T+1 胜率
T+3 胜率
平均超额收益
最近一次表现
```

样本数不足时必须提示。

---

## 10. 空状态

当没有事件时展示：

```text
当前没有符合条件的事件。
```

当事件没有候选股票时展示：

```text
该事件已识别，但暂未推理出高置信股票路径。
```

---

## 11. 设计原则

1. 事件先于股票展示。
2. 高强度和低置信状态必须突出。
3. 候选股票必须带分数拆解。
4. 每只股票必须能跳转到解释页。
5. 验证样本数不足时必须提示。

---

## 12. 结论

Event Dashboard 是 V2 的事件入口。

它让用户从事件出发，逐步看到产业链影响、股票关联和历史验证。