# 06 Validation

> 本文档定义 AStock V2 中事件推理结果的验证设计。

---

## 1. Validation 的定位

Validation Engine 用于评估 Reasoning Engine 的推理结果是否在市场中得到验证。

它不判断产业事实是否存在，而是判断：

```text
某类事件通过某条路径推理到某些股票后，市场是否出现了可观测反应。
```

---

## 2. 验证目标

Validation 需要回答：

1. 事件发生后候选股票是否上涨？
2. 是否跑赢指数？
3. 是否跑赢所属行业？
4. 哪些事件类型更有效？
5. 哪些图谱路径更有效？
6. 哪些股票对某类事件反应更稳定？

---

## 3. 验证窗口

第一阶段默认窗口：

```text
T+1
T+3
T+5
T+10
```

不同事件类型可配置不同窗口。

例如：

```text
price_increase: T+1 / T+3
supply_shortage: T+3 / T+5
policy_support: T+5 / T+10
capacity_expansion: T+10 / T+20
```

---

## 4. 验证指标

每个事件-股票组合至少计算：

```text
return_1d
return_3d
return_5d
return_10d
excess_return_vs_index
excess_return_vs_industry
max_drawdown
max_gain
hit
```

hit 可定义为：

```text
excess_return > 0
```

或根据事件类型配置阈值。

---

## 5. 验证输入

Validation Engine 输入：

```text
event_id
stock_code
event_date
reasoning_score
exposure_score
industry_code
benchmark_index
price_data
```

---

## 6. 验证输出

输出结构：

```text
event_id
stock_code
window
absolute_return
benchmark_return
industry_return
excess_return_index
excess_return_industry
hit
calculated_at
```

---

## 7. 数据处理规则

### 7.1 非交易日

如果事件发生在非交易日，则使用下一个交易日作为 T。

### 7.2 停牌

如果股票停牌：

- 标记 suspended。
- 不参与该窗口验证。
- 不计为失败。

### 7.3 涨跌停

涨跌停需要保留标记。

涨跌停不是异常数据，但会影响后续可交易性评估。

---

## 8. 聚合验证

Validation 不只看单个事件，还需要聚合统计。

聚合维度：

```text
event_type
entity
relation_type
reason_path
stock_code
industry
```

示例：

```text
supply_shortage 类型事件
历史出现 20 次
平均 T+3 超额收益 3.2%
胜率 65%
```

---

## 9. 回写机制

Validation 结果可以回写：

- event_type_weight。
- relation_weight。
- stock_exposure_weight。
- scoring validation_score。

注意：

Validation 主要校准交易有效性，不直接删除事实关系。

---

## 10. 噪音识别

以下情况可能标记为噪音：

- 事件热度高但股票无反应。
- 路径过长且多次验证无效。
- 新闻重复传播但无新增事实。
- 概念关联弱且无资金响应。

噪音关系应降低 weight，而不是删除 evidence。

---

## 11. 验证结果展示

前端应展示：

```text
同类事件历史次数
平均收益
胜率
最大回撤
最近一次表现
该股票历史响应
```

这可以帮助用户判断事件是否只是概念炒作。

---

## 12. Validation 设计原则

1. 验证市场反应，不验证事实真假。
2. 使用绝对收益和超额收益双指标。
3. 停牌和非交易日必须特殊处理。
4. 验证结果可回写权重。
5. 聚合统计比单次表现更重要。
6. 验证结果必须可追溯到事件和路径。

---

## 13. 结论

Validation Engine 是 AStock V2 从“推理系统”升级为“可学习系统”的关键。

没有验证闭环，系统只能说明“看起来相关”。

有了验证闭环，系统才能逐步知道“哪些关系真的有效”。