# 03 Company Knowledge Card

> 本文档定义 AStock V2 Company Knowledge Card 设计。

---

## 1. 目标

Company Knowledge Card 用于展示公司的结构化产业画像。

---

## 2. 核心内容

```text
Company Summary
Products
Materials
Industries
Concepts
Key Relations
Evidence Summary
Related Events
Data Freshness
```

---

## 3. Company Summary

展示：

```text
company_name
stock_code
exchange
industry
sector
website
description
last_updated_at
```

---

## 4. Products

展示：

```text
product_name
product_type
relation_type
confidence
primary_evidence
```

---

## 5. Materials

展示：

```text
material_name
relation_path
exposure_score
confidence
```

---

## 6. Industries

展示：

```text
industry_name
relation_path
confidence
evidence_count
```

---

## 7. Concepts

展示：

```text
concept_name
confidence
source_type
status
```

概念关系通常置信度低于产品和材料关系，应单独展示。

---

## 8. Key Relations

展示关键图谱关系：

```text
source
relation_type
target
weight
confidence
evidence_count
```

点击关系可查看证据详情。

---

## 9. Evidence Summary

展示证据统计：

```text
annual_report_count
announcement_count
website_count
news_count
manual_count
```

---

## 10. Related Events

展示近期相关事件：

```text
event_id
title
event_type
final_score
confidence
occurred_at
```

---

## 11. Data Freshness

展示：

```text
last_kg_update
last_evidence_update
last_validation_update
```

---

## 12. 设计原则

1. 公司画像必须基于图谱关系。
2. 产品和概念必须分开展示。
3. 每个关键关系必须能追溯证据。
4. 低置信信息必须标记。
5. 知识卡不执行推理，只展示已入库结果。

---

## 13. 结论

Company Knowledge Card 把图谱中的公司关系转化为清晰、可审计的公司画像。