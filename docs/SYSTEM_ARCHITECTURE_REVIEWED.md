# SYSTEM_ARCHITECTURE.md（审阅增强版）

> 本文档为原架构评审与优化建议版本。

## 1. 总体架构

现有分层方向正确，但建议补充 Data Standardization Layer，统一多数据源结构。

## 2. 数据层

建议标准 Schema：

```text
StockBar:
  code, date, open, high, low, close, volume, amount

NewsEvent:
  code, time, title, source, sentiment
```

更新方式应包含首次全量、每日增量和缓存层。

## 3. 因子层

规则应升级为可排序、可回测的评分系统：

```text
Trend Score = 0–100
MA 结构：40
slope：30
volume：30
```

量能因子：

```text
Volume Ratio = volume / MA20(volume)
```

## 4. 舆情层

新闻需要标准化。热度建议使用 Z-score：

```text
Burst = (x - mean) / std
```

情绪需要增加政策、业绩和风险事件分类。

## 5. 策略层

```text
Final Score =
0.5 * Trend +
0.3 * Sentiment +
0.2 * Volume
```

应支持 Top N 股票和仓位建议。

## 6. 输出层

建议提供 FastAPI：

```text
GET /stocks/today
GET /stocks/{code}
GET /signal
```

Web 层 MVP 可用 Streamlit，生产采用 Vue 3。

## 7. 调度

轻量系统使用 APScheduler，生产级分布式系统可使用 Celery。

## 8. 下一步

1. 数据标准化与 Parquet；
2. 因子 Score 与 Volume；
3. 巨潮、RSS 和 NLP 分类；
4. FastAPI 与 Dashboard。

