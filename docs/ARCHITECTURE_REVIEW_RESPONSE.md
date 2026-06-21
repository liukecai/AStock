# 架构评审批注落实清单

本文件对应 `SYSTEM_ARCHITECTURE_REVIEWED.md` 的逐项处理结果。

| 评审项 | 处理结果 | 当前实现证据 |
| --- | --- | --- |
| 缺少 Data Standardization Layer | 已落实 | `backend/app/schemas.py` 提供 `StockBar` 与 `NewsEvent` |
| StockBar 缺少统一字段 | 已落实 | `code/date/OHLC/volume/amount`，进入 SQLite 前强校验 |
| NewsEvent 未标准化 | 已落实 | 新闻实体与股票关联解耦；`news_items` + `news_stock_links` |
| 缺少增量更新 | 原系统已具备并保留 | 行情回刷 30 天；巨潮从最新时间回退一天；RSS Upsert |
| 缺少 Cache Layer | 已落实 | `signals` 因子快照 + `data/parquet` 标准快照 |
| Phase 1 要求 Parquet | 已落实 | 行情、新闻、关联、因子四类 Parquet 自动导出 |
| 规则系统无法评分排序 | 原系统已具备并强化 | 趋势、情绪、量能、总分均为 0–100；Dashboard Top N |
| Trend Score 建议 40/30/30 | 已落实 | MA 结构 40%、斜率 30%、趋势量能 30% |
| 缺少 Volume Ratio | 原系统已具备 | `volume / MA20(volume)`，同时生成独立 Volume Score |
| Burst 定义不稳定 | 已落实 | `(x - mean_5d) / max(std_5d, 1)` |
| 情绪缺少事件类别 | 已落实 | `policy/performance/risk/general` 中英文分类 |
| 缺少统一总分 | 原系统已具备 | `0.5 Trend + 0.3 Sentiment + 0.2 Volume` |
| 无法 Top N 选股 | 已落实 | `/api/stocks/today?top_n=N` 和 Dashboard 排序 |
| 缺少仓位建议 | 已落实但降级为研究语义 | 0–8% `research_weight_pct`，风险封顶、回避归零 |
| 缺少 FastAPI | 原系统已具备 | `/api/health`、`/api/dashboard`、`/api/jobs` 等 |
| 建议 `/stocks/today` | 已落实 | `/api/stocks/today` |
| 建议 `/stocks/{code}` | 原系统已具备 | `/api/stocks/{symbol}` |
| 建议 `/signal` | 已落实 | `/api/signal` |
| 缺少 Web | 原系统已具备 | Vue 3 Dashboard 与个股详情 |
| crontab 不够用 | 原系统已具备 | APScheduler，任务防重入 |
| 巨潮 + RSS | 原系统已具备 | 巨潮公告、国内外 RSSHub 新闻统一入库 |

## 设计取舍

### NewsEvent 为什么不直接包含单个 code

评审示例将 `code` 放入 `NewsEvent`。实际新闻可能关联多只股票，因此系统采用：

```text
news_items (一篇新闻)
    1 ─── N
news_stock_links (多个股票代码、置信度、匹配方式)
```

这比单一 `code` 字段更符合多实体新闻场景，同时仍能导出标准化股票关联 Parquet。

### 仓位建议为什么称为研究权重

系统没有回测、组合优化、风险预算和真实账户信息，直接输出实盘仓位会制造虚假精度。
因此实现为“研究权重上限”，用于研究列表资源分配，并明确不构成投资建议。

### 因子缓存为什么仍以 SQLite 为主

当前部署为单机 500 股票规模：

- SQLite `signals` 支持在线 API 查询；
- Parquet 支持离线分析和后续回测；
- 两者分别承担在线缓存和分析快照职责。

未来多实例部署时再迁移 PostgreSQL/Redis，避免当前阶段引入不必要运维复杂度。

