# 00 Overview

> 本文档定义 AStock V2 Web 层总体设计。

---

## 1. Web 层定位

AStock V2 的 Web 层不是简单数据表格，也不是单纯股票列表。

它需要展示完整研究链路：

```text
Event
  ↓
Impacted Entity
  ↓
Reasoning Path
  ↓
Stock Exposure
  ↓
Score Breakdown
  ↓
Evidence
  ↓
Validation
```

Web 层的核心价值是可解释性。

---

## 2. 设计目标

V2 Web 需要让用户快速理解：

- 发生了什么事件。
- 事件影响哪些商品、材料、行业。
- 哪些股票被推理出来。
- 每只股票的关联路径是什么。
- 每条关系有什么证据。
- 历史上同类事件是否有效。
- 当前数据是否可信。

---

## 3. 信息架构

推荐信息架构：

```text
Dashboard
├── Event Dashboard
├── Stock Dashboard
├── Supply Chain Explorer
├── Validation Panel
└── System Monitor
```

每个页面围绕一个核心问题设计。

---

## 4. 页面关系

```text
Event Dashboard
  ↓
Event Detail
  ↓
Event Impact Path
  ↓
Why This Stock
  ↓
Evidence Detail
```

```text
Stock Detail
  ↓
Company Knowledge Card
  ↓
Related Events
  ↓
Why This Stock
```

```text
Supply Chain Explorer
  ↓
Entity Detail
  ↓
Neighbor Relations
  ↓
Related Stocks
```

---

## 5. 核心组件

V2 Web 核心组件包括：

- Event Card。
- Stock Score Card。
- Reason Path Graph。
- Evidence List。
- Score Breakdown。
- Validation Summary。
- Company Knowledge Card。
- Entity Relation Table。
- Job Status Badge。

---

## 6. 解释优先原则

V1 更偏向展示结果。

V2 应优先展示原因。

错误方式：

```text
股票 A：82 分
股票 B：78 分
```

推荐方式：

```text
股票 A：82 分
原因：事件目标实体 -> 材料 -> 公司产品
证据：年报 / 官网产品目录
历史验证：同类事件 T+3 胜率 65%
```

---

## 7. 低置信提示

Web 必须明确展示低置信结果。

例如：

```text
该路径基于新闻候选关系，尚未被高质量来源确认。
```

低置信结果不应和高置信结果混在一起展示。

---

## 8. 数据新鲜度

页面应展示关键数据更新时间：

- 行情更新时间。
- 新闻更新时间。
- 图谱更新时间。
- 验证更新时间。

数据过期时必须提示。

---

## 9. Web 与 API 的关系

Web 只消费 API DTO。

```text
Web Component
  ↓
API Client
  ↓
/api/v2/*
```

Web 不直接访问数据库，不执行推理逻辑。

---

## 10. 设计原则

1. 页面围绕用户问题组织。
2. 解释优先于排名。
3. 路径优先于标签。
4. 证据优先于概念。
5. 验证优先于主观判断。
6. 所有数据状态必须清晰。

---

## 11. 结论

AStock V2 Web 层的目标是把复杂推理变成用户能理解的研究界面。

它不只是展示结果，而是展示系统为什么得到这个结果。