# 06 Phase 6 Web Explainability

> Phase 6 目标：实现 V2 Web 解释层，让用户能看到事件、路径、证据、分数和验证结果。

---

## 1. 阶段目标

Phase 6 将后端推理结果转化为可理解的页面体验。

核心页面：

```text
Event Dashboard
Supply Chain Explorer
Company Knowledge Card
Why This Stock
Validation Panel
Job Monitor
```

---

## 2. 开发任务

新增前端模块：

```text
EventDashboard
EventDetail
ReasonPathGraph
StockExplainPanel
EvidenceList
ValidationPanel
CompanyKnowledgeCard
JobMonitor
```

新增 API Client：

```text
graphApi
eventApi
stockExplainApi
validationApi
jobApi
```

---

## 3. Event Dashboard

展示：

```text
事件列表
事件类型
事件强度
影响实体
候选标的
分数拆解
```

---

## 4. Reason Path Graph

展示：

```text
事件目标实体
图谱中间节点
公司节点
标的节点
关系类型
权重和置信度
```

---

## 5. Stock Explain Panel

展示：

```text
final_score
confidence
score_breakdown
reason_paths
evidence_list
validation_summary
```

---

## 6. Validation Panel

展示：

```text
sample_count
hit_rate
avg_excess_return
window comparison
recent cases
```

---

## 7. UI 状态

必须支持：

```text
loading
empty
error
low_confidence
stale_data
missing_data
pending_review
```

---

## 8. 验收标准

1. 能查看事件列表。
2. 能查看事件详情。
3. 能查看候选标的。
4. 能查看推理路径图。
5. 能查看证据来源。
6. 能查看分数拆解。
7. 能查看验证统计。
8. 能查看任务状态。

---

## 9. 风险控制

1. 前端不执行推理。
2. 前端不直接访问数据库。
3. 低置信结果必须提示。
4. 样本数不足必须提示。
5. 数据过期必须提示。

---

## 10. 结论

Phase 6 是 V2 从后端能力走向产品体验的关键阶段。