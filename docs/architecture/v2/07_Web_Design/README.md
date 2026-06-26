# 07 Web Design

> 本目录定义 AStock V2 的 Web 产品与交互设计。
>
> Web 层的目标不是只展示分数，而是把事件、图谱路径、证据、暴露度、验证结果以可解释方式展示给用户。

---

## 文档范围

```text
07_Web_Design/
├── README.md
├── 00_Overview.md
├── 01_Event_Dashboard.md
├── 02_Supply_Chain_Explorer.md
├── 03_Company_Knowledge_Card.md
├── 04_Why_This_Stock.md
├── 05_Validation_Panel.md
├── 06_UI_State_Design.md
└── 07_ADR.md
```

---

## 阅读顺序

1. `00_Overview.md`：理解 Web 层总体目标和信息架构。
2. `01_Event_Dashboard.md`：理解事件看板设计。
3. `02_Supply_Chain_Explorer.md`：理解产业链图谱探索设计。
4. `03_Company_Knowledge_Card.md`：理解公司知识卡设计。
5. `04_Why_This_Stock.md`：理解个股解释模块设计。
6. `05_Validation_Panel.md`：理解历史验证面板设计。
7. `06_UI_State_Design.md`：理解加载、空状态、错误和低置信提示设计。
8. `07_ADR.md`：理解 Web 设计关键决策。

---

## Web 层职责

Web 层负责：

- 展示事件列表和事件详情。
- 展示事件影响实体和路径。
- 展示候选股票及评分拆解。
- 展示公司知识卡。
- 展示个股与事件的关联原因。
- 展示证据来源。
- 展示历史验证结果。
- 展示后台任务状态。

Web 层不负责：

- 执行事件推理。
- 计算股票暴露度。
- 维护知识图谱。
- 调用 LLM 生成新关系。
- 直接访问数据库。

---

## 核心页面

```text
Event Dashboard
Supply Chain Explorer
Company Knowledge Card
Why This Stock
Event Impact Path
Validation Panel
Job Monitor
```

---

## 设计原则

1. 先解释路径，再展示分数。
2. 所有关系尽量展示证据来源。
3. 低置信结果必须明确提示。
4. 分数必须可拆解。
5. 路径必须可视化。
6. 验证结果必须显示样本数。
7. Web 只消费 API DTO，不承载业务推理。

---

## 成功标准

V2 Web 完成后，用户应能在页面上回答：

1. 今天有哪些重要事件？
2. 每个事件影响哪些产业链节点？
3. 哪些股票与事件相关？
4. 为什么这些股票相关？
5. 关系来自哪些证据？
6. 同类事件历史表现如何？
7. 当前数据是否新鲜、任务是否正常？