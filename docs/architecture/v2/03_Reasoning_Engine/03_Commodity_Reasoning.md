# 03 Commodity Reasoning

> 本文档定义 AStock V2 中事件到商品、材料、行业节点的推理设计。

---

## 1. Commodity Reasoning 目标

Commodity Reasoning 负责将标准化事件映射到产业链中的初始影响节点。

事件通常先影响：

- 商品。
- 材料。
- 产品。
- 技术。
- 行业。

再进一步传播到公司和股票。

---

## 2. 输入

输入是标准化事件：

```json
{
  "event_type": "supply_shortage",
  "target_entities": ["六氟化钨"],
  "impact_direction": "positive",
  "role_direction": ["positive_for_supplier"],
  "intensity": "medium_high"
}
```

---

## 3. 输出

输出是初始影响实体集合：

```text
六氟化钨
电子特气
半导体材料
钨
钨材料
```

每个实体应包含：

```text
entity_id
entity_type
impact_direction
impact_weight
path_from_event
confidence
```

---

## 4. 推理方式

Commodity Reasoning 使用 Knowledge Graph 查询。

基本流程：

```text
Event Target Entity
  ↓
Find belongs_to / uses / upstream_of / downstream_of
  ↓
Expand to Material / Commodity / Industry
  ↓
Rank Impact Entities
```

---

## 5. 供应冲击推理

对于 supply_shortage：

```text
商品 / 产品供应紧张
  ↓
供应商可能受益
  ↓
下游使用者可能受损
  ↓
替代品可能受益
```

示例：

```text
六氟化钨供应紧张
  ↓
六氟化钨生产商
  ↓
电子特气相关公司
```

---

## 6. 需求增长推理

对于 demand_growth：

```text
下游需求增长
  ↓
上游材料需求增长
  ↓
相关供应商可能受益
```

示例：

```text
AI 算力需求增长
  ↓
HBM
  ↓
先进封装
  ↓
半导体材料
```

---

## 7. 价格上涨推理

对于 price_increase：

```text
商品价格上涨
  ↓
资源拥有者 / 生产商可能受益
  ↓
成本承压企业可能受损
```

示例：

```text
钨价上涨
  ↓
钨矿 / 钨材料公司
```

---

## 8. 政策事件推理

对于 policy_support：

```text
政策支持行业
  ↓
行业节点
  ↓
公司节点
  ↓
股票节点
```

政策事件通常路径更宽，噪音更高，应设置较强路径衰减。

---

## 9. 地缘冲突推理

对于 geo_conflict：

常见影响路径：

```text
地缘冲突
  ↓
原油 / 天然气 / 黄金 / 军工 / 航运
  ↓
相关行业和股票
```

地缘事件需要控制影响范围，避免扩散过宽。

---

## 10. 路径扩散限制

为了控制噪音，建议：

```text
max_depth = 4
max_entities_per_layer = 20
min_path_score = 0.15
```

不同事件类型可配置不同深度。

---

## 11. 影响方向传播

方向传播规则示例：

```text
supply_shortage + supplier -> positive
supply_shortage + downstream_user -> negative
price_increase + producer -> positive
price_increase + buyer -> negative
policy_support + industry -> positive
risk_event + company -> negative
```

方向传播不等于最终股票涨跌，只表示产业逻辑方向。

---

## 12. 路径权重

路径权重由边权重和事件强度共同决定。

简化公式：

```text
impact_weight = event_intensity_weight
              * product(edge_weight)
              * depth_decay
```

其中 depth_decay 用于降低长路径权重。

---

## 13. 初始实体排序

影响实体排序依据：

1. 与事件目标实体距离。
2. 路径权重。
3. 实体类型。
4. 关系置信度。
5. 历史验证结果。

优先保留高权重、高置信、短路径实体。

---

## 14. 设计原则

1. 事件必须先映射到实体，再推理到股票。
2. 商品、材料、产品、行业节点必须分层处理。
3. 不同事件类型使用不同传播规则。
4. 长路径必须衰减。
5. 宽泛事件必须限制扩散范围。
6. 产业影响方向与最终交易信号分离。

---

## 15. 结论

Commodity Reasoning 是事件进入产业链的第一步。

它决定系统能否从“新闻关键词”升级为“供应链影响推理”。