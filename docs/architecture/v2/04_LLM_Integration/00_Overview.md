# 00 Overview

> 本文档定义 AStock V2 中 LLM Integration 的总体设计。

---

## 1. 为什么需要 LLM

AStock V2 需要从大量非结构化文本中提取产业知识。

这些文本包括：

- 年报。
- 招股说明书。
- 公告。
- 公司官网产品目录。
- 互动易回复。
- 新闻。
- RSS 内容。

这些文本中包含大量供应链信息，例如：

```text
主营产品
原材料
下游行业
客户类型
募投项目
新增产能
产品应用场景
风险事件
```

传统规则可以处理明确关键词，但很难稳定覆盖复杂语义。

LLM 的价值在于把非结构化文本转化为结构化候选知识。

---

## 2. LLM 的边界

LLM 不直接参与最终投资判断。

LLM 在 V2 中的边界是：

```text
阅读文本
  ↓
抽取实体和关系
  ↓
输出候选结构
  ↓
等待校验或审核
```

LLM 不做：

- 买入建议。
- 卖出建议。
- 仓位建议。
- 最终股票打分。
- 正式图谱写入。
- 市场表现验证。

---

## 3. LLM Integration 总体链路

```text
Raw Document / News
  ↓
Evidence Collector
  ↓
Text Chunking
  ↓
Prompt Builder
  ↓
LLM Extraction
  ↓
JSON Validation
  ↓
Candidate Entity / Relation / Event
  ↓
Review / Rule Check
  ↓
Knowledge Graph
```

---

## 4. LLM 适合的任务

LLM 适合：

- 长文本摘要。
- 产品抽取。
- 上下游抽取。
- 应用场景抽取。
- 事件类型识别。
- 关系候选生成。
- 证据片段定位。
- 解释文本生成。

---

## 5. LLM 不适合的任务

LLM 不适合：

- 高频实时判断。
- 确定事实真伪。
- 替代行情回测。
- 替代人工审核。
- 直接给出交易结论。
- 直接维护正式图谱。

---

## 6. 输出规范

所有 LLM 结果必须是 JSON。

禁止只输出自然语言。

每条抽取结果必须包含：

```text
subject
predicate
object
evidence_text
confidence
reason
```

其中 evidence_text 是最关键字段。

如果没有 evidence_text，该结果不能进入候选关系表。

---

## 7. Candidate First

LLM 输出必须进入候选层。

```text
candidate_entities
candidate_relations
candidate_events
```

候选层的作用是隔离错误和幻觉。

只有通过校验的结果才能进入正式图谱。

---

## 8. LLM 与 Evidence 的关系

LLM 输出必须绑定 Evidence。

错误方式：

```text
LLM 认为某公司涉及某产品
```

正确方式：

```text
LLM 从某份年报中的某段文本抽取出某公司涉及某产品
```

LLM 是抽取器，不是事实来源。

---

## 9. LLM 与 YAML 的关系

YAML 是人工确认的种子知识。

LLM 可以生成 YAML 候选片段，但不能直接覆盖 YAML。

推荐流程：

```text
LLM 输出候选关系
  ↓
审核通过
  ↓
写入图谱
  ↓
必要时反向生成 YAML seed
```

---

## 10. LLM 与前端解释

LLM 可以辅助生成解释文本。

但解释文本必须基于已存在的图谱路径和证据。

不能让 LLM 自行发挥新的关系。

---

## 11. 成本控制

LLM 调用应离线执行。

应避免：

```text
用户请求 -> 实时长文本 LLM
```

推荐：

```text
离线抽取 -> 入库 -> 在线查询
```

---

## 12. 结论

LLM Integration 的核心原则是：

```text
LLM 负责理解文本
图谱负责保存知识
推理引擎负责路径计算
市场数据负责验证效果
```

LLM 是 V2 的加速器，但不是系统的决策核心。