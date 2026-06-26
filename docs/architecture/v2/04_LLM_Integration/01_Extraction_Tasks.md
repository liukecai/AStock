# 01 Extraction Tasks

> 本文档定义 AStock V2 中 LLM 负责的抽取任务范围。

---

## 1. 抽取任务目标

LLM 抽取任务的目标是从非结构化文本中生成结构化候选知识。

LLM 输出不直接进入正式图谱，而是进入候选层。

---

## 2. 年报抽取

年报是高质量信息来源。

需要抽取：

- 主营产品。
- 核心业务。
- 原材料。
- 下游行业。
- 主要客户类型。
- 产能。
- 新业务。
- 风险提示。

输出关系示例：

```text
Company -> produces -> Product
Product -> uses -> Material
Product -> used_in -> Industry
Company -> exposed_to -> Industry
```

---

## 3. 招股说明书抽取

招股书通常包含最完整的产业链信息。

需要抽取：

- 产品结构。
- 产业链上下游。
- 核心客户。
- 供应商。
- 竞争对手。
- 募投项目。
- 行业地位。
- 技术路线。

输出关系示例：

```text
Company -> produces -> Product
Product -> upstream_of -> Product
Product -> downstream_of -> Industry
Company -> competes_with -> Company
Company -> has_project -> Project
```

---

## 4. 公告抽取

公告适合抽取事件和变化。

需要抽取：

- 新增产能。
- 中标合同。
- 回购。
- 减持。
- 风险事件。
- 业绩变化。
- 项目进展。
- 产品扩产。

输出关系示例：

```text
Announcement -> describes -> EventInstance
Company -> expands_capacity -> Product
Company -> wins_contract -> Customer
Company -> has_risk -> RiskEvent
```

---

## 5. 官网产品目录抽取

官网产品目录适合确认产品和应用场景。

需要抽取：

- 产品名称。
- 产品别名。
- 产品分类。
- 应用领域。
- 下游行业。
- 技术参数。

输出关系示例：

```text
Company -> produces -> Product
Product -> belongs_to -> Material
Product -> used_in -> Industry
```

---

## 6. 互动易抽取

互动易适合发现市场关注的新概念。

需要抽取：

- 投资者问题涉及的概念。
- 公司是否确认相关业务。
- 公司是否否认相关业务。
- 当前业务进展。

输出关系示例：

```text
Company -> related_to -> Concept
Company -> denies -> Concept
Company -> plans -> Product
```

互动易可信度低于年报和公告，应进入候选层。

---

## 7. 新闻抽取

新闻适合抽取事件。

需要抽取：

- 事件类型。
- 目标实体。
- 影响方向。
- 事件强度。
- 相关行业。
- 相关公司。

输出示例：

```text
News -> describes -> EventInstance
EventInstance -> impacts -> Commodity
EventInstance -> impacts -> Industry
```

新闻不能单独生成高置信公司产品关系。

---

## 8. RSS 抽取

RSS 主要作为新闻入口。

需要抽取：

- 标题事件。
- 发布时间。
- 来源。
- 目标实体。
- 是否重复事件。

RSS 内容通常较短，适合轻量事件抽取。

---

## 9. 招聘信息抽取

招聘信息适合发现新布局，但可信度较低。

需要抽取：

- 岗位名称。
- 技术方向。
- 产品方向。
- 地点。
- 部门。

示例：

```text
Company -> hiring_for -> Technology
Company -> candidate_related_to -> Concept
```

招聘信息只能作为弱证据。

---

## 10. 专利抽取

专利适合确认技术方向。

需要抽取：

- 专利名称。
- 技术关键词。
- 申请人。
- 应用领域。
- 相关产品。

输出关系示例：

```text
Company -> owns_patent -> Technology
Technology -> related_to -> Product
```

专利不等于商业化产品，应谨慎使用。

---

## 11. 抽取任务优先级

第一阶段优先：

1. 年报。
2. 招股书。
3. 公告。
4. 官网产品目录。
5. 新闻事件。

第二阶段：

1. 互动易。
2. 招聘。
3. 专利。

---

## 12. 设计原则

1. 不同来源使用不同抽取任务。
2. 高质量来源可生成高置信候选。
3. 低质量来源只能生成弱候选。
4. 所有抽取结果必须绑定 evidence_text。
5. LLM 不直接写入正式图谱。
6. 抽取结果必须可验证、可审核、可回滚。

---

## 13. 结论

LLM 抽取任务是 V2 图谱自动化构建的入口。

抽取任务设计越清晰，后续图谱质量越稳定。