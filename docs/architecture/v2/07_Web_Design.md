# 07 Web Design

> AStock V2 Web 产品与交互设计。
>
> Web 层的目标不是只展示分数，而是将事件、图谱路径、证据、暴露度、验证结果以可解释方式展示给用户。
>
> 前置阅读：[06_API_Design.md](./06_API_Design.md)（理解 Web 消费的 API 接口）。

---

## 1. 总体设计

### 1.1 核心页面

| 页面 | 核心目标 |
|---|---|
| Event Dashboard | 展示事件列表与详情，回答"今天有哪些重要事件" |
| Supply Chain Explorer | 交互式产业链图谱探索，回答"实体之间是什么关系" |
| Company Knowledge Card | 展示公司知识画像，回答"公司涉及哪些产业链" |
| Why This Stock | 个股事件解释，回答"为什么这只股票与事件相关" |
| Validation Panel | 历史验证面板，回答"同类事件过去是否有效" |
| Job Monitor | 后台任务状态，回答"数据是否新鲜、任务是否正常" |

### 1.2 设计原则

1. 先解释路径，再展示分数。
2. 所有关系尽量展示证据来源。
3. 低置信结果必须明确提示。
4. 分数必须可拆解。
5. 路径必须可视化。
6. 验证结果必须显示样本数。
7. Web 只消费 API DTO，不承载业务推理逻辑，不直接访问数据库。

---

## 2. Event Dashboard

### 2.1 事件列表

| 展示内容 | 说明 |
|---|---|
| 事件标题 | 事件简述 |
| event_type | 事件类型标签 |
| intensity | 强度（高/中/低） |
| direction | 影响方向 |
| 影响实体 | 初始影响的商品/材料/行业 |
| 候选标的数 | 推理产生的候选股票数量 |
| occurred_at | 事件时间 |

支持按 event_type / 日期范围 / 强度筛选，按时间/影响面排序。

### 2.2 事件详情页

- 事件摘要与来源。
- 影响实体列表。
- **Event Impact Path**：从事件到候选股票的图谱路径可视化。
- 候选股票列表（含 `final_score` / `exposure_score` / `confidence` / `score_breakdown`）。
- 历史验证面板入口。

---

## 3. Supply Chain Explorer

### 3.1 交互设计

- 以选定实体为中心，展示一跳邻居。
- 点击邻居节点可展开下一层。
- 节点展示：实体名称、类型、状态。
- 边展示：关系类型、权重、置信度。
- 支持按 entity_type / relation_type 过滤。

### 3.2 路径查询

- 支持指定起点和终点查询路径。
- 展示路径列表，每条路径含节点、边、权重、证据。
- 默认 `max_depth = 4`。

### 3.3 数据源

```text
/api/v2/graph/entities/{id}
/api/v2/graph/entities/{id}/neighbors
/api/v2/graph/paths
```

---

## 4. Company Knowledge Card

### 4.1 展示内容

| 区块 | 内容 |
|---|---|
| 基本信息 | 公司名称、代码、行业、官网 |
| 产品列表 | 公司主要产品（`produces` 关系） |
| 产业链定位 | 产品 → 材料 → 行业的上下游路径 |
| 关系列表 | 所有图谱关系，带置信度和证据 |
| 相关事件 | 历史关联事件列表 |

### 4.2 数据源

```text
/api/v2/stocks/{code}/knowledge
/api/v2/stocks/{code}/events
```

---

## 5. Why This Stock

### 5.1 核心展示

| 区块 | 内容 |
|---|---|
| 事件摘要 | 事件标题、类型、强度 |
| 推理路径图 | 从事件到股票的图谱路径可视化 |
| 证据来源 | 路径上每条关系的 evidence 列表 |
| 分数拆解 | exposure / trend / sentiment / volume / event_intensity / validation 各因子 |
| 验证统计 | 同类事件历史胜率、平均超额收益、样本数 |
| 解释文本 | 结构化解释（基于路径和证据生成） |

### 5.2 数据源

```text
/api/v2/stocks/{code}/explain?event_id={id}
```

### 5.3 展示示例

```text
该股票与事件相关，因为：
公司产品涉及六氟化钨（来源：招股书、官网产品目录，置信度 0.92）
六氟化钨属于电子特气（来源：行业分类，置信度 0.88）
事件类型 supply_shortage 历史胜率 65%（20 次样本）
```

---

## 6. Validation Panel

### 6.1 展示内容

| 区块 | 内容 |
|---|---|
| 事件类型统计 | event_type 维度的样本数、胜率、平均超额收益 |
| 窗口对比 | T+1 / T+3 / T+5 / T+10 各窗口的胜率和超额收益 |
| 标的响应 | 某只股票在某类事件下的历史响应强度 |
| 近期案例 | 最近验证的事件案例列表 |
| 权重调整建议 | 基于验证结果的权重校准方向 |

### 6.2 注意事项

- 所有统计必须展示样本数（避免小样本误导）。
- 绝对收益和超额收益分开展示。
- 数据缺失和停牌必须单独标记，不显示为失败。

### 6.3 数据源

```text
/api/v2/validation/events/{id}
/api/v2/validation/summary
```

---

## 7. UI 状态设计

### 7.1 状态类型

| 状态 | 处理方式 |
|---|---|
| Loading | 使用骨架屏，不用空白页 |
| Empty | 说明原因（如"没有符合条件的事件"、"暂无高置信路径"） |
| Error | 展示错误标题+摘要+错误码+重试操作，不暴露堆栈 |
| Low Confidence | 显式提示 confidence、低置信原因、是否来自弱证据 |
| Stale Data | 展示 `last_updated_at` 和过期原因 |
| Partial Data | 尽量展示可用内容（如"路径已展示，验证结果仍在计算中"） |
| Pending Review | 标记候选关系/待审核状态 |

### 7.2 Badge 规范

```text
High Confidence / Low Confidence / Pending Review / Validated
Weak Evidence / Stale Data / Missing Data
```

### 7.3 原则

页面不能静默失败。空状态必须说明原因。低置信必须显式提示。数据过期必须提示。不向用户暴露内部错误堆栈。

---

## 8. 架构决策记录（ADR）

### ADR-001：Web 层以解释为核心，而不是只展示排名

V2 优先展示事件 → 路径 → 证据 → 分数拆解 → 验证结果，再展示排名。

### ADR-002：路径图作为核心交互组件

Event Impact Path 和 Reason Path Graph 是核心组件，用户能直观看到推理链路。

### ADR-003：低置信结果必须显式展示

所有低 confidence、pending_review、weak_evidence 状态在 UI 中明确标记，降低误读风险。

### ADR-004：验证结果必须展示样本数

所有验证统计展示 `sample_count`，避免小样本误导。

### ADR-005：Web 不承载业务推理逻辑

Web 只消费 API DTO，不直接访问数据库、不执行图谱推理、不计算最终分数。前后端职责清晰。

### ADR-006：空状态和错误状态必须说明原因

空状态、错误状态、数据过期、低置信、缺失数据必须有明确提示。
