# 03 Reasoning Engine

> 本目录定义 AStock V2 的事件推理引擎设计。
>
> Reasoning Engine 的目标是把结构化事件转化为产业链影响路径、候选股票、暴露度评分和可解释结果。

---

## 文档范围

```text
03_Reasoning_Engine/
├── README.md
├── 00_Overview.md
├── 01_Event_Extraction.md
├── 02_Event_Normalization.md
├── 03_Commodity_Reasoning.md
├── 04_Exposure_Calculation.md
├── 05_Scoring.md
├── 06_Validation.md
└── 07_ADR.md
```

---

## 阅读顺序

1. `00_Overview.md`：理解 Reasoning Engine 的定位和总体链路。
2. `01_Event_Extraction.md`：理解如何从新闻、公告、手工输入中抽取事件。
3. `02_Event_Normalization.md`：理解事件如何标准化为可推理结构。
4. `03_Commodity_Reasoning.md`：理解事件如何映射到商品、材料、行业节点。
5. `04_Exposure_Calculation.md`：理解股票暴露度如何计算。
6. `05_Scoring.md`：理解事件分、图谱分、趋势分如何融合。
7. `06_Validation.md`：理解推理结果如何通过市场表现验证。
8. `07_ADR.md`：理解推理引擎关键架构决策。

---

## Reasoning Engine 的职责

Reasoning Engine 负责：

- 接收结构化事件。
- 找到事件影响的初始实体。
- 沿 Knowledge Graph 搜索影响路径。
- 找到相关公司和股票。
- 计算路径权重和股票暴露度。
- 输出可解释推理结果。
- 将结果交给 Scoring Engine 和 Validation Engine。

Reasoning Engine 不负责：

- 采集外部新闻。
- 直接调用行情接口。
- 直接调用 LLM 做长文本抽取。
- 维护图谱事实关系。
- 直接生成买卖建议。

---

## 核心推理链路

```text
Raw Event Text
  ↓
Event Extraction
  ↓
Event Normalization
  ↓
Initial Entity Mapping
  ↓
Graph Traversal
  ↓
Impact Path Ranking
  ↓
Stock Exposure Calculation
  ↓
Scoring
  ↓
Explanation
  ↓
Validation
```

---

## 示例

输入：

```text
市场传出六氟化钨供应紧张。
```

输出：

```json
{
  "event_type": "supply_shortage",
  "target_entities": ["六氟化钨"],
  "impacted_chains": ["电子特气", "半导体材料", "钨材料"],
  "candidate_stocks": [
    {
      "code": "688146",
      "name": "中船特气",
      "exposure_score": 0.82,
      "reason_path": ["六氟化钨", "电子特气", "中船特气"]
    }
  ]
}
```

---

## 设计原则

1. 事件必须结构化后才能推理。
2. 推理必须基于 Knowledge Graph，不直接依赖关键词到股票映射。
3. 路径必须可解释。
4. 暴露度必须可拆解。
5. 推理结果必须可验证。
6. LLM 只参与事件抽取和解释辅助，不直接决定最终股票。

---

## 与其他模块关系

```text
Event Engine -> Reasoning Engine -> Exposure Engine -> Scoring Engine -> Validation Engine
                 ↑
          Knowledge Graph
```

Reasoning Engine 是连接事件与图谱、图谱与股票的核心中间层。