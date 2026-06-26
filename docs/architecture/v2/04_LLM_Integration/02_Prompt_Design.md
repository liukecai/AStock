# 02 Prompt Design

> 本文档定义 AStock V2 中 LLM Prompt 的设计原则和模板要求。

---

## 1. Prompt 设计目标

Prompt 的目标不是让 LLM 做自由分析，而是让 LLM 在严格约束下完成结构化抽取。

Prompt 必须明确：

- 输入文本。
- 抽取任务。
- 输出字段。
- 输出格式。
- 禁止事项。
- 置信度要求。
- evidence_text 要求。

---

## 2. Prompt 基本结构

推荐结构：

```text
角色说明
任务说明
输入文本
抽取字段
输出 JSON Schema
约束规则
禁止事项
```

---

## 3. 通用约束

所有 Prompt 都必须包含：

```text
只输出 JSON
不要输出 Markdown
不要输出自然语言解释
不要生成投资建议
不要推测原文没有的信息
每条关系必须提供 evidence_text
如果没有证据，返回空数组
```

---

## 4. 年报抽取 Prompt

任务：从年报中抽取公司产品、原材料、下游行业。

关键字段：

```text
company
products
materials
industries
relations
evidence_text
confidence
```

要求：

- 只抽取原文明确出现的信息。
- 不要把行业概念误认为产品。
- 不要把客户行业误认为公司主营产品。

---

## 5. 招股书抽取 Prompt

任务：从招股书中抽取产业链上下游和募投项目。

关键字段：

```text
company
products
upstream_entities
downstream_entities
customers
suppliers
projects
relations
evidence_text
confidence
```

要求：

- 区分产品、原材料、客户、供应商。
- 区分已有业务和募投项目。
- 区分事实和风险提示。

---

## 6. 公告抽取 Prompt

任务：从公告中抽取事件。

关键字段：

```text
event_type
company
target_entities
action
impact_direction
intensity
relations
evidence_text
confidence
```

公告事件类型包括：

```text
capacity_expansion
contract_award
risk_event
earnings_surprise
shareholder_change
product_progress
```

---

## 7. 官网产品目录 Prompt

任务：从官网产品目录中抽取产品和应用领域。

关键字段：

```text
company
products
product_category
applications
industries
relations
evidence_text
confidence
```

要求：

- 产品名称必须来自原文。
- 应用领域必须和产品对应。
- 不要扩展原文未提到的行业。

---

## 8. 新闻事件 Prompt

任务：从新闻中抽取事件。

关键字段：

```text
event_type
target_entities
trigger_words
impact_direction
role_direction
intensity
confidence
```

要求：

- 抽取事件，不抽取交易建议。
- 如果新闻只是评论或传闻，应降低 confidence。
- 如果没有明确目标实体，返回 candidate 状态。

---

## 9. 解释生成 Prompt

任务：基于已存在的图谱路径生成解释文本。

输入必须包含：

```text
event
stock
reason_path
evidence_list
score_breakdown
```

要求：

- 只能基于输入内容解释。
- 不得添加新关系。
- 不得输出买卖建议。
- 解释应简洁、可读。

---

## 10. Confidence 标准

Prompt 中应明确 confidence 取值含义：

```text
0.9 - 1.0：原文直接明确支持
0.7 - 0.9：原文较明确支持
0.5 - 0.7：间接支持或语义推断
0.3 - 0.5：弱相关
0.0 - 0.3：不应输出或仅候选
```

---

## 11. Prompt 禁止事项

Prompt 必须禁止：

- 输出股票买卖建议。
- 编造不存在的产品。
- 编造客户或供应商。
- 把市场概念当作事实业务。
- 把未来计划当作已有产能。
- 不带 evidence_text 输出关系。

---

## 12. Prompt 版本管理

每个 Prompt 应有版本号。

示例：

```text
prompt_name = annual_report_extraction
prompt_version = v1.0
```

抽取结果应记录 prompt_version，便于回溯。

---

## 13. 设计原则

1. Prompt 只用于结构化抽取。
2. 输出必须是 JSON。
3. evidence_text 是强制字段。
4. 不允许自由投资分析。
5. 不同来源使用不同 Prompt。
6. Prompt 必须版本化。

---

## 14. 结论

Prompt Design 决定 LLM 输出质量。

严格结构化、强证据约束、禁止自由发挥，是 AStock V2 使用 LLM 的核心原则。