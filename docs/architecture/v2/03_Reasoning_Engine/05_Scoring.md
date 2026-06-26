# 05 Scoring

> 本文档定义 AStock V2 中事件推理结果的评分设计。

---

## 1. Scoring 的定位

Scoring Engine 负责将事件推理结果、股票暴露度、趋势因子、舆情因子和历史验证结果合成为可排序分数。

Scoring 不负责生成图谱路径。

Scoring 不负责判断事实关系是否真实。

Scoring 只负责回答：

```text
在当前事件下，哪些股票更值得进入观察列表？
```

---

## 2. 输入因子

第一阶段输入因子包括：

```text
Event Score
Exposure Score
Trend Score
Sentiment Score
Volume Score
Validation Score
Confidence Score
```

---

## 3. 输出结构

评分输出：

```text
event_id
stock_code
final_score
rank
score_breakdown
confidence
label
created_at
```

示例：

```json
{
  "event_id": "evt_001",
  "stock_code": "688146",
  "final_score": 82.4,
  "rank": 1,
  "label": "event_resonance",
  "score_breakdown": {
    "event_score": 78,
    "exposure_score": 82,
    "trend_score": 75,
    "sentiment_score": 68,
    "validation_score": 70
  }
}
```

---

## 4. Event Score

Event Score 表示事件本身强度。

来源：

- 事件类型。
- 事件强度。
- 来源质量。
- 多源确认。
- 新闻热度。

建议映射：

```text
low -> 20
medium -> 50
medium_high -> 70
high -> 85
critical -> 95
```

---

## 5. Exposure Score

Exposure Score 来自 Exposure Engine。

取值建议转换为 0-100：

```text
exposure_score_100 = exposure_score * 100
```

Exposure 是事件与股票相关性的核心因子。

---

## 6. Trend Score

Trend Score 来自 V1 已有趋势系统。

可包含：

- MA 结构。
- 价格斜率。
- 均线位置。
- 波动率。
- 趋势延续性。

事件驱动系统不应忽略技术面。

因为事件相关股票如果处于明显破位趋势中，交易价值可能下降。

---

## 7. Sentiment Score

Sentiment Score 表示新闻和公告情绪。

来源：

- 新闻标题情绪。
- 公告类型。
- 多源报道情绪。
- 风险词。

Sentiment Score 不能替代事件推理，只作为辅助因子。

---

## 8. Volume Score

Volume Score 表示市场是否已经出现资金反应。

可参考：

```text
volume_ratio = today_volume / avg_volume_20d
amount_ratio = today_amount / avg_amount_20d
turnover_change
```

放量确认可以提高事件信号可信度。

---

## 9. Validation Score

Validation Score 表示历史同类事件是否有效。

来源：

- 同类事件平均收益。
- 同类事件胜率。
- 该股票历史响应。
- 该路径历史响应。

示例：

```text
同类事件历史胜率高 -> validation_score 高
同类事件多次无效 -> validation_score 低
```

---

## 10. Confidence Score

Confidence Score 表示结论可信度。

来源：

- 证据质量。
- 图谱关系置信度。
- 事件抽取置信度。
- 实体映射置信度。

Confidence 不应直接等同于 final_score。

一个事件可能得分高，但置信度低，前端应明确展示。

---

## 11. 推荐总分公式

第一阶段推荐：

```text
final_score = 0.30 * exposure_score
            + 0.20 * event_score
            + 0.20 * trend_score
            + 0.10 * sentiment_score
            + 0.10 * volume_score
            + 0.10 * validation_score
```

如果某些因子缺失，使用中性值并标记缺失。

---

## 12. 标签生成

根据得分和因子组合生成标签。

示例：

```text
event_resonance：事件强 + 暴露高 + 趋势好
high_exposure_watch：暴露高但趋势一般
concept_noise：事件弱 + 证据弱 + 路径长
risk_alert：负向事件 + 暴露高
validated_pattern：历史验证较强
```

标签用于前端展示，不替代分数。

---

## 13. 排序规则

默认排序：

```text
final_score desc
confidence desc
exposure_score desc
validation_score desc
```

当 confidence 过低时，即使 final_score 较高，也应进入观察区而不是核心列表。

---

## 14. 风险控制

以下情况应降低分数或降级标签：

- 证据来源质量低。
- 路径过长。
- 事件重复报道但缺少新信息。
- 股票处于明显下降趋势。
- 历史同类事件表现差。
- 事件方向不明确。

---

## 15. Score Breakdown

所有评分必须保存 breakdown。

前端必须能够展示：

```text
为什么总分是 82？
哪一项贡献最高？
哪一项拖累分数？
哪些因子缺失？
```

---

## 16. 设计原则

1. Exposure 是核心因子。
2. Event Score 表示事件强度。
3. Trend 和 Volume 用于市场确认。
4. Validation 用于历史有效性校准。
5. Confidence 与 Final Score 分离。
6. 所有得分必须可拆解。
7. 评分结果不是买卖建议。

---

## 17. 结论

Scoring Engine 将事件推理转化为可排序结果。

它的价值不只是给出分数，而是给出可解释、可拆解、可验证的观察优先级。