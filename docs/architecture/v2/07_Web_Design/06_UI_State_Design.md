# 06 UI State Design

> 本文档定义 AStock V2 Web 的 UI 状态设计。

---

## 1. 设计目标

UI State Design 用于统一页面在加载、空数据、错误、低置信、数据过期等情况下的展示方式。

---

## 2. Loading State

加载状态用于：

```text
事件列表加载
图谱路径加载
个股解释加载
验证结果加载
证据列表加载
```

建议使用骨架屏，而不是长时间空白页面。

---

## 3. Empty State

空状态必须说明原因。

示例：

```text
没有符合条件的事件。
没有找到高置信路径。
暂无验证结果。
暂无证据来源。
```

---

## 4. Error State

错误状态展示：

```text
错误标题
错误摘要
错误码
可重试操作
```

不展示后端堆栈。

---

## 5. Low Confidence State

低置信结果必须明确提示。

展示内容：

```text
confidence
低置信原因
是否来自弱证据
是否待审核
```

---

## 6. Stale Data State

数据过期时展示：

```text
last_updated_at
expected_update_frequency
stale_reason
```

例如：

```text
行情数据尚未更新到最近交易日。
```

---

## 7. Partial Data State

部分数据缺失时，页面不应完全失败。

示例：

```text
已展示图谱路径，但验证结果仍在计算中。
```

---

## 8. Pending Review State

候选关系或低质量来源需要审核时展示：

```text
pending_review
candidate_relation
needs_more_evidence
```

---

## 9. Badge 规范

常用 Badge：

```text
High Confidence
Low Confidence
Pending Review
Validated
Weak Evidence
Stale Data
Missing Data
```

---

## 10. 设计原则

1. 页面不能静默失败。
2. 空状态必须说明原因。
3. 低置信必须显式提示。
4. 数据过期必须提示。
5. 部分数据缺失时尽量展示可用内容。
6. 不向用户暴露内部错误堆栈。

---

## 11. 结论

UI State Design 保证 V2 Web 在复杂数据状态下仍然清晰可信。