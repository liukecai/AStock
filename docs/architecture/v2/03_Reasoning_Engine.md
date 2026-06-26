# 03 Reasoning Engine

> AStock V2 事件推理引擎设计。
>
> 本文档定义从事件抽取、标准化、图谱路径推理、暴露度计算、多因子评分到验证闭环的完整链路。
>
> 前置阅读：[02_Knowledge_Graph_Design.md](./02_Knowledge_Graph_Design.md)（推理依赖图谱提供实体和关系数据）。

---

## 1. 核心推理链路

```text
Raw Event Text
  → Event Extraction        ← 从新闻/公告中抽取事件
  → Event Normalization     ← 标准化为可推理结构
  → Initial Entity Mapping  ← 找到事件影响的初始实体
  → Graph Traversal         ← 沿 Knowledge Graph 搜索影响路径
  → Impact Path Ranking     ← 路径评分与排序
  → Stock Exposure          ← 计算股票暴露度
  → Scoring                 ← 多因子融合评分
  → Explanation             ← 生成可解释结果
  → Validation              ← 市场表现验证
```

### 职责边界

| 负责 | 不负责 |
|---|---|
| 接收结构化事件 | 采集外部新闻 |
| 沿图谱搜索影响路径 | 直接调用行情接口 |
| 计算暴露度和评分 | 直接调用 LLM 做长文本抽取 |
| 输出可解释推理结果 | 维护图谱事实关系 |
| 将结果交给 Validation Engine | 直接生成买卖建议 |

### 与其他模块关系

```text
Event Engine → Reasoning Engine → Exposure Engine → Scoring Engine → Validation Engine
                     ↑
              Knowledge Graph
```

---

## 2. 事件抽取

### 2.1 抽取来源

| 来源 | 抽取方式 |
|---|---|
| 新闻标题/正文 | 规则关键词 + LLM 抽取 |
| 巨潮公告标题/摘要 | 规则关键词 + LLM 抽取 |
| 手动输入 | 用户直接输入事件文本 |

### 2.2 抽取输出

结构化事件至少包含：

| 字段 | 说明 |
|---|---|
| event_id | 唯一标识 |
| event_type | 事件类型（如 `supply_shortage`、`demand_growth`、`policy_support`） |
| subtype | 子类型 |
| entities | 涉及实体列表 |
| intensity | 强度 |
| direction | 影响方向（如 `positive_for_supplier`） |
| time_window | 预期影响窗口 |
| source_evidence_id | 来源证据 |

### 2.3 抽取原则

- LLM 用于事件抽取时属于离线任务 → 详见 [04_LLM_Integration.md](./04_LLM_Integration.md)。
- 原始新闻文本存在歧义，不能直接进入图谱推理，必须先经过结构化。

---

## 3. 事件标准化

### 3.1 标准化目标

将多来源事件统一为可推理的规范格式：

```text
"六氟化钨供应紧张"     → event_type=supply_shortage, target=六氟化钨, intensity=high
"六氟化钨价格上涨"     → event_type=price_increase, target=六氟化钨, intensity=medium
"中东冲突升级"          → event_type=geo_conflict, target=原油, intensity=high
```

### 3.2 标准化流程

```text
Raw Event Text → 实体归一化 → 事件类型匹配 → 强度/方向判断 → 去重 → Structured Event
```

### 3.3 V2 第一阶段事件类型

```text
supply_shortage / supply_increase / demand_growth / demand_decline
price_increase / price_decrease / capacity_expansion / capacity_cut
policy_support / policy_restriction / export_control / import_change
geo_conflict / natural_disaster / tech_breakthrough / earnings_surprise
order_received / contract_signed / product_launch / business_divestiture
```

---

## 4. 商品推理与图谱路径搜索

### 4.1 推理流程

```text
Structured Event
  → 1. 定位事件影响的初始实体
  → 2. 沿 Knowledge Graph 多跳搜索
  → 3. 找到相关 Company / Stock
  → 4. 计算路径权重
  → 5. 排序候选路径
```

### 4.2 路径搜索

- 使用 BFS/DFS 在图谱中搜索从事件影响实体到 Company/Stock 的路径。
- 默认 `max_depth = 4`。
- 路径评分：`path_score = ∏(edge_weight × edge_confidence) × depth_decay`。
- 搜索时只使用 `status = active` 或 `validated` 的关系。

### 4.3 推理输出

```json
{
  "event": "六氟化钨供应紧张",
  "event_type": "supply_shortage",
  "affected_entities": ["六氟化钨", "电子特气", "半导体材料"],
  "candidate_stocks": [
    {
      "code": "688146",
      "name": "中船特气",
      "exposure_score": 0.82,
      "reason_path": ["六氟化钨", "电子特气", "中船特气"],
      "confidence": 0.78
    }
  ]
}
```

---

## 5. 暴露度计算

### 5.1 暴露度来源

| 因素 | 说明 |
|---|---|
| 图谱路径长度 | 越短越强 |
| 关系权重 | 路径上各关系的 weight 乘积 |
| 证据置信度 | 路径上各关系的 confidence |
| 公司主营相关度 | 产品收入占比 |
| 历史事件表现 | 同类事件历史验证结果 |

### 5.2 输出

```text
stock_code / entity_id / event_id / exposure_score / confidence / reason_path
```

### 5.3 设计决策

- Exposure 使用 0.0~1.0 连续分数，可排序、可融合多因子、可表达弱相关和强相关。

---

## 6. 多因子评分

### 6.1 输入因子

| 因子 | 来源 |
|---|---|
| Exposure Score | 图谱推理 |
| Event Intensity | 事件强度 |
| Trend Score | V1 趋势评分 |
| Sentiment Score | 舆情评分 |
| Volume Score | 成交量变化 |
| Validation Score | 历史验证表现 |

### 6.2 输出

```text
stock_code / event_id / final_score / score_breakdown / confidence / rank
```

Score 必须保留 breakdown，便于前端解释和后续调参。

### 6.3 设计决策

- `final_score` 与 `confidence` 分离。一个股票可能因事件得分高但证据置信度低，前端需明确展示风险。

---

## 7. 验证闭环

### 7.1 验证目标

确认推理结果是否真的产生市场反应：

```text
事件发生(T0) → 记录候选股票 → 计算 T+1/T+3/T+5/T+10 收益 → 计算超额收益 → 更新权重
```

### 7.2 验证指标

| 指标 | 说明 |
|---|---|
| absolute_return | 绝对收益 |
| excess_return_index | 相对指数超额收益 |
| excess_return_industry | 相对行业超额收益 |
| max_gain / max_drawdown | 窗口内最大涨幅/回撤 |
| hit | 是否命中（超额收益为正） |

### 7.3 特殊情况处理

必须处理：非交易日（向前/向后对齐）、停牌（跳过或标记 `suspended`）、行情缺失（标记 `missing_data`）、新股数据不足。

### 7.4 聚合统计

```text
supply_shortage 类型事件：历史出现 20 次，平均 T+3 超额收益 3.2%，胜率 65%
```

聚合维度：event_type / entity / relation_type / reason_path / stock_code / industry。

### 7.5 回写机制

Validation 结果可回写：event_type_weight、relation_weight、stock_exposure_weight、scoring validation_score。

验证主要校准交易有效性，不直接删除事实关系。

### 7.6 噪音识别

以下情况降低 weight 而不删除 evidence：
- 事件热度高但股票无反应
- 路径过长且多次验证无效
- 新闻重复传播但无新增事实
- 概念关联弱且无资金响应

---

## 8. 架构决策记录（ADR）

### ADR-001：推理必须基于结构化事件

原始新闻文本不能直接进入图谱推理，必须先经过 Event Extraction 和 Event Normalization。输入稳定、便于去重和验证。

### ADR-002：事件先映射到实体，再推理到股票

采用 `事件 → 目标实体 → 图谱路径 → 股票`，而不是 `事件关键词 → 股票列表`。路径可解释、中间实体可复用、支持多跳推理。

### ADR-003：Exposure 使用连续分数

0.0~1.0 连续分数，可排序、可融合多因子、可表达弱相关和强相关。

### ADR-004：Final Score 与 Confidence 分离

分别保存 `final_score` 和 `confidence`，避免高分低可信结果被误读。

### ADR-005：长路径必须衰减

路径分数引入 `depth_decay`，推荐最大深度 4。控制噪音，提高解释质量。

### ADR-006：历史验证用于校准交易有效性

Validation 结果校准事件权重、路径权重和股票响应权重。验证主要校准影响强度，不直接删除事实关系。

### ADR-007：推理结果必须保存路径

保存 `reason_path` / `path_score` / `edge_details` / `evidence_ids`，支持 Why This Stock、人工复核和路径级验证。

### ADR-008：Reasoning Engine 不生成买卖建议

输出候选影响、暴露度和解释，不输出买入/卖出/仓位建议。保持系统定位为研究分析工具。
