# 03 Phase 3 Reasoning MVP

> Phase 3 目标：实现事件到图谱路径再到候选标的的最小推理闭环。

---

## 1. 阶段目标

Phase 3 不追求复杂模型，只完成最小可用 Reasoning Engine。

核心链路：

```text
Structured Event
  ↓
Target Entity
  ↓
Graph Traversal
  ↓
Reasoning Path
  ↓
Stock Exposure
```

---

## 2. 开发任务

新增模块：

```text
reasoning_engine.py
exposure_engine.py
path_finder.py
```

新增核心函数：

```text
normalize_event()
find_impacted_entities()
find_reasoning_paths()
calculate_exposure()
explain_path()
```

---

## 3. 最小输入

结构化事件：

```json
{
  "event_type": "supply_shortage",
  "target_entities": ["产品A"],
  "intensity": "high",
  "direction": "positive_for_supplier"
}
```

---

## 4. 最小输出

```text
event_id
stock_code
path
path_score
exposure_score
confidence
```

---

## 5. 推理规则

第一阶段只支持：

```text
produces
belongs_to
used_in
upstream_of
downstream_of
listed_as
```

默认限制：

```text
max_depth = 4
min_path_score = 0.15
```

---

## 6. 落库表

写入：

```text
event_instances
event_impacts
reasoning_paths
stock_exposures
```

---

## 7. 验收用例

输入：

```text
产品A 供应紧张
```

系统输出：

```text
产品A -> 公司A -> 股票A
```

并保存 reasoning_paths 和 stock_exposures。

---

## 8. 验收标准

1. 能接受结构化事件。
2. 能映射到图谱实体。
3. 能查询多跳路径。
4. 能生成候选标的。
5. 能计算 exposure_score。
6. 能保存推理路径。
7. 能通过 API 查询结果。

---

## 9. 风险控制

1. 限制 max_depth。
2. 限制返回路径数量。
3. 路径必须包含 confidence。
4. 不输出操作建议。
5. 低置信路径进入观察区。

---

## 10. 结论

Phase 3 是 V2 从图谱存储走向事件推理的关键阶段。