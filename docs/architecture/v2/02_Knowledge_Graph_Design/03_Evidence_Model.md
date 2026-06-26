# 03 Evidence Model

> 本文档定义 AStock V2 Knowledge Graph 的证据模型。

---

## 1. Evidence 设计目标

Evidence 是 AStock V2 的可信度基础。

系统不应只保存“某公司涉及某产品”，还必须保存：

```text
这条关系来自哪里？
原文是什么？
发布时间是什么？
来源可信度如何？
是否由多个来源交叉验证？
```

Evidence 的目标是让图谱关系可追溯、可审计、可复核。

---

## 2. Evidence 基础字段

Evidence 至少包含：

```text
evidence_id
source_type
source_name
source_url
title
raw_text
published_at
collected_at
related_company
related_stock_code
source_confidence
content_hash
status
```

字段说明：

| 字段 | 说明 |
|---|---|
| evidence_id | 证据唯一 ID |
| source_type | 来源类型 |
| source_name | 来源名称 |
| source_url | 原文链接 |
| title | 标题 |
| raw_text | 原文或摘要 |
| published_at | 发布时间 |
| collected_at | 采集时间 |
| related_company | 相关公司 |
| related_stock_code | 相关股票代码 |
| source_confidence | 来源基础可信度 |
| content_hash | 去重 hash |
| status | active / archived / rejected |

---

## 3. Source Type

V2 第一阶段支持以下来源类型：

```text
annual_report
prospectus
announcement
company_website
product_catalog
irm_reply
news
rss
job_posting
patent
yaml_seed
manual_input
llm_extraction
```

---

## 4. 来源基础可信度

不同来源具备不同基础可信度。

建议默认值：

| 来源 | 基础可信度 |
|---|---:|
| annual_report | 0.95 |
| prospectus | 0.95 |
| announcement | 0.90 |
| company_website | 0.85 |
| product_catalog | 0.85 |
| irm_reply | 0.70 |
| patent | 0.75 |
| job_posting | 0.55 |
| news | 0.50 |
| rss | 0.45 |
| yaml_seed | 0.80 |
| manual_input | 0.90 |
| llm_extraction | 依赖原始来源 |

说明：

LLM 不是独立证据来源。LLM 只是抽取方式。

如果 LLM 从年报中抽取信息，证据来源仍然是 annual_report。

---

## 5. Evidence 与 Relation 的关系

一条 Relation 可以有多个 Evidence 支持。

例如：

```text
中船特气 -> produces -> 六氟化钨
```

可以由以下证据共同支持：

- 招股说明书。
- 年报。
- 官网产品目录。
- 公告。

因此需要中间表：

```text
relation_evidence
```

字段：

```text
relation_id
evidence_id
support_type
extracted_text
confidence_delta
created_at
```

---

## 6. Support Type

support_type 表示证据如何支持关系。

可选值：

```text
direct
indirect
weak
contradictory
```

说明：

| 类型 | 说明 |
|---|---|
| direct | 原文直接说明关系 |
| indirect | 原文间接支持关系 |
| weak | 弱相关，仅作候选 |
| contradictory | 与已有关系相矛盾 |

---

## 7. 证据片段

Evidence 不应只保存全文，还应保存与关系相关的片段。

例如：

```text
公司主要产品包括六氟化钨、三氟化氮、高纯氨等电子特气产品。
```

该片段可以支持：

```text
公司 -> produces -> 六氟化钨
六氟化钨 -> belongs_to -> 电子特气
```

---

## 8. Evidence 去重

使用 content_hash 对证据去重。

hash 输入建议：

```text
source_type + source_url + title + raw_text
```

同一新闻被多个 RSS 源转载时，应避免重复放大证据权重。

---

## 9. Evidence 时效性

某些证据会过期。

例如：

- 公司已剥离某业务。
- 产品已停产。
- 项目已终止。
- 概念题材已不再相关。

Evidence 可设置有效期：

```text
valid_from
valid_to
```

第一阶段可选实现，后续用于关系过期管理。

---

## 10. Evidence 质量控制

### 10.1 高质量证据

- 年报明确披露。
- 招股书明确披露。
- 公告明确披露。
- 官网产品目录明确列出。

### 10.2 中质量证据

- 互动易回复。
- 公司公众号。
- 权威财经新闻。

### 10.3 低质量证据

- 社交平台讨论。
- 未证实传闻。
- 二次转载新闻。

低质量证据不能单独生成高置信关系。

---

## 11. Evidence 与 LLM

LLM 的输出必须绑定 Evidence。

错误方式：

```text
LLM 认为公司涉及 WF6
```

正确方式：

```text
LLM 从某年报第 X 段中抽取出公司涉及 WF6
```

LLM 只负责抽取，不作为事实来源。

---

## 12. Evidence 与前端解释

前端 Why This Stock 页面应能展示：

```text
关系：中船特气 produces 六氟化钨
证据：2024 年报 / 官网产品目录
片段：公司主要产品包括...
置信度：0.92
```

用户应能理解每条推理路径背后的来源。

---

## 13. Evidence 设计原则

1. 没有证据的关系只能是候选关系。
2. LLM 不是证据来源。
3. 多来源证据应合并提高置信度。
4. 弱证据不能单独生成高置信关系。
5. 证据必须可追溯到原文或来源。
6. 证据需要去重，避免重复转载放大权重。

---

## 14. 结论

Evidence Model 是 V2 图谱可信度的根基。

如果没有 Evidence，Knowledge Graph 会退化为不可审计的概念标签库。

有了 Evidence，系统才能回答：

```text
这条供应链关系为什么可信？
它来自哪些资料？
是否被多个来源确认？
```