# A-Quant Insight

A 股趋势与舆情融合量化选股系统。当前版本是可运行的 V2 版本：FastAPI、Vue 3、支持 SQLite/PostgreSQL 双持久化层（支持高并发并发无锁写入）、前端任务控制中心与失败告警、事件知识库 YAML 配置外置化、定时任务与 Docker 部署。

> 仅供策略研究和工程验证，不构成投资建议。

完整设计说明见 [系统架构与实现逻辑](docs/SYSTEM_ARCHITECTURE.md)。

## 已实现

- MA5 / MA20 / MA60、多头排列、20 日价格斜率、MA60 斜率与量比
- 确定性中文金融关键词情绪评分（无随机舆情）
- 5 日基线 Z-score 新闻热度
- 政策、业绩、风险和一般事件分类
- 标准 `StockBar` / `NewsEvent` Schema 与 Parquet 快照
- 默认 `0.5 × Trend + 0.3 × Sentiment + 0.2 × Volume`，支持 IC 校准
- Dashboard、信号筛选、个股价格/均线图、新闻与因子详情、映射审核
- SQLite/PostgreSQL 双持久化层支持，通过 `DATABASE_URL` 动态切换，自动兼容 DDL 与 SQL 语句
- 提供一键式 SQLite 到 PostgreSQL 的高性能数据迁移脚本（`cli_pg_migrate.py`）
- 针对单元测试提供 `conftest.py` 会话隔离机制，保证测试纯净度与本地 38 项单元测试顺利通过
- 统一新闻数据层与 RSSHub 国内外新闻聚合，支持失败源隔离与自动规则降级
- 飞书/钉钉 webhook 定时任务失败卡片提醒与数据库自动在线热备份
- 产业链事件传导 V2 引擎（支持 oil、lithium、copper 商品画像与财务量化打分）
- 事件知识库（商品行业映射、股票敞口、画像特征）外置化为 `config/commodity_graph/*.yaml`
- 新增可视化“任务监控中心”页面，支持任务进度展示、失败日志展开与手动触发重试
- 管理口令口令校验授权，关键写操作及任务重触发需配合 `X-Admin-Secret` 头校验
- 可成交约束历史回测：因子 IC、五分位收益、Sharpe、最大回撤，以及基于历史 IC 的权重自动校准
- Docker Compose 生产环境一键式容器化部署（包含自动拉起 postgres 服务及内网 Tailscale 模型调用）

## 本地运行

### Docker（推荐）

```bash
cp .env.example .env
docker compose up --build -d
```

生产 Compose 默认不暴露宿主机端口，而是把 Web 容器接入现有
`headscale_default` Caddy 网络。独立本地运行时可临时添加
`ports: ["8080:80"]`，然后打开 <http://localhost:8080>。

生产模式默认使用 AKShare。若需要前端开发样例，可设置 `DEMO_DATA=true`。

### 开发模式

后端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## 接入真实行情

AKShare 被放在独立依赖文件中，避免上游频繁发布影响核心镜像：

```bash
cd backend
pip install -r requirements-market.txt
python -m app.cli update-market --symbols 600519,300750
```

生产环境默认使用 AKShare 新浪源（腾讯云 IP 访问东财可能被重置），并按实时成交额选择
500 只活跃股。设置 `AKSHARE_UNIVERSE_SIZE=0`
会遍历全部 A 股；免费数据源下建议分批执行。

## 接入真实新闻

生产环境通过 AKShare 维护的巨潮公告接口按日期获取全市场公告，再过滤到当前
股票池。默认每天 20:30 更新，20:45 使用新公告重算信号；首次回补最近 7 天。

RSS 新闻链路为：

```text
国内外新闻 → RSSHub → 统一新闻实体 → 中英文 NLP → 股票别名/代码映射 → 舆情因子
```

默认源包含财联社、华尔街见闻、36氪、Bloomberg 与 Al Jazeera。RSSHub 在
Compose 内自托管，不暴露公网端口；单个源失败会被隔离并记录在 `/api/jobs`。
可以通过 `RSS_FEEDS_JSON` 覆盖源列表。

统一数据层分为：

| 表 | 含义 |
| --- | --- |
| `news_items` | 新闻/公告实体、来源、语言、地区、摘要、情绪与原文 |
| `news_stock_links` | 一篇新闻到多只股票的映射、置信度和匹配方式 |
| `stock_aliases` | 股票简称、派生名称与中英文别名 |

推荐先接巨潮正式公告 API/授权数据源。免费新闻网页抓取存在反爬、版权和结构变化风险，不应放进策略核心进程。

## API

- `GET /api/health`：服务、数据状态及商品事件统计
- `GET /api/admin/auth-status`：返回当前是否启用管理授权
- `GET /api/dashboard`：最新信号及汇总
- `GET /api/stocks/today`：Top N 当日研究列表
- `GET /api/signal`：查询最新信号
- `GET /api/stocks/{symbol}`：个股行情、新闻、因子和最新信号
- `GET /api/jobs`：获取所有后台更新与计算任务的最新运行进度、状态与下次调度时间
- `POST /api/jobs/{name}/retry`：手动触发指定的后台更新任务运行（支持的任务包括 `market_update`、`signal_pipeline`、`rss_news`、`cninfo_announcements`）
- `POST /api/pipeline/run`：手动重算信号
- `POST /api/events/analyze`：分析特定新闻（可传 `news_id` 或 `title`/`summary`/`time`）
- `GET /api/events`：获取商品事件列表（支持分页，以及按 `commodity` / `event_type` / `direction` 筛选）
- `GET /api/events/{id}`：获取单次事件的详细因果链与受益/受损股票排序（包含 V2 `v2_reaction_scores` 附加字段）
- `GET /api/events/{event_id}/reaction`：获取 V2 传导链的详细反应打分与传导链分析结果（主字段为 `event`、`commodity_impacts`、`v2_reaction_scores`，保留 `reactions` 兼容别名）
- `GET /api/stocks/{symbol}/commodity-exposure`：获取该个股的商品因果画像与敞口多维度属性特征（主字段为 `commodity_profiles`，保留 `profiles` 兼容别名）
- `POST /api/events/rebuild`：对数据库中已有新闻批量重构分析商品事件

若配置 `ADMIN_SECRET`，以下写操作需要在请求头中附带 `X-Admin-Secret`：

- `POST /api/pipeline/run`
- `POST /api/news-links`
- `DELETE /api/news-links`
- `POST /api/events/analyze`
- `POST /api/events/rebuild`
- `POST /api/jobs/{name}/retry`

## 商品事件驱动量化模块 (MVP)

事件驱动系统建立了“**新闻事件 → 商品冲击 → 产业链传导 → A股股票暴露 → 量化评分**”的显式因果链。

### 1. 模型边界与知识库
内置可扩展规则库，涵盖以下商品的上下游关系和传导方向：
- **钨/六氟化钨 (tungsten/WF6)**：
  - 钨矿短缺/中断：上游（中钨高新、厦门钨业、洛阳钼业）**受益**，下游（硬质合金加工）**受损**。
  - 六氟化钨 (WF6) 中断：上游电子特气（中船特气）**受益**，下游半导体制造**受损**。
- **原油/石油 (oil)**：上游采掘与开采（中国石油、中海油服、中国石化）在供应短缺时价格上涨**受益**，下游化工、航空机场**受损**。
- **铜 (copper)**：上游开采（江西铜业、紫金矿业、云南铜业）在短缺时**受益**，下游电力设备**受损**。
- **黄金 (gold)**：避险与价格飙升使黄金采选（山东黄金、中金黄金、赤峰黄金）**受益**。
- **锂 (lithium)**：上游资源开采（天齐锂业、赣锋锂业、盐湖股份）**受益**，下游电池制造（宁德时代、比亚迪）及新能源汽车**受损**。

### 2. 量化评分公式
每个暴露的股票都会计算一个综合事件评分，其所有子分数和总分均为 0-100 分：
$$\text{Event Score} = 0.5 \times \text{Event Impact} + 0.3 \times \text{Sector Exposure} + 0.2 \times \text{Trend Strength}$$
- **Event Impact** (0-100)：基于事件类型（地缘冲突 `90`、供应冲击 `80`、政策变化 `75`、意外中断 `70`）调整文本强度（intensity）和置信度（confidence）。
- **Sector Exposure** (0-100)：精确代码映射设为 `100`，行业关键词匹配回退设为 `60`。
- **Trend Strength** (0-100)：个股最近一期的技术面趋势强度分（`trend_score`），无信号时默认为 `50`。

系统同时识别需求疲弱、供应过剩和价格下跌等商品下行冲击，并反转上下游影响方向；评分表示影响强度，`direction` 单独标识受益或受损，受损标的不会混入受益排名。

### 3. 研究用途与投资风险免责声明
**特别说明**：本系统所输出的因果传导方向及打分结果，属于基于确定性规则推理的量化因子工程验证，**不包含真实投资性行情预测，绝不构成任何投资建议或实盘操作指南**。投资有风险，入市需谨慎。

### 4. 商品事件抽取 LLM 配置
系统支持“LLM 优先抽取 + 规则回退”机制。开启后，将优先使用大语言模型进行商品事件识别与属性抽取；若提取失败、超时或格式不合法，系统将自动降级为基于关键词规则的事件识别。

在环境配置文件 `.env` 中添加以下配置项：
- `EVENT_LLM_ENABLED` (bool): 是否启用 LLM 商品事件抽取（默认为 `false`）。
- `EVENT_LLM_BASE_URL` (string): 兼容 OpenAI 协议的 API 地址（默认为 SenseNova 接口 `https://token.sensenova.cn/v1`）。
- `EVENT_LLM_API_KEY` (string): 接口 API Key。不配置或为空时将自动回退到规则识别。
- `EVENT_LLM_MODEL` (string): 模型名称（默认为 `sensenova-6.7-flash-lite`）。
- `EVENT_LLM_TIMEOUT_SECONDS` (float): 请求超时秒数（默认为 `10.0`）。

> [!WARNING]
> 请勿将真实的 API Key 提交到代码仓库中，推荐通过本地 `.env` 环境变量文件进行配置。


### 5. 商品传导引擎 V2 (Phase 1)
V2 版本在 V1 MVP 基础上扩展了细粒度的产业链传导与财务业绩影响评估层。当前支持 `oil`、`lithium` 和 `copper` 三类商品的画像解析与反应计算。

- **多表支持 (Additive Schema)**：
  - `company_commodity_profiles`：个股商品暴露画像（如角色 `role`，传导渠道 `channel`，传导时滞 `lag_days`，弹性 `earnings_elasticity` 等）。
  - `event_earnings_impacts`：事件的个股财务业绩影响预测记录。
  - `event_stock_reaction_scores_v2`：V2 版本量化反应打分详情表。
- **打分计算公式**：
  $$\text{Reaction Score}_{V2} = 0.25 \times \text{shock\_score} + 0.25 \times \text{exposure\_score} + 0.25 \times \text{earnings\_score} + 0.15 \times \text{sentiment\_score} + 0.10 \times \text{trend\_score}$$
  - `shock_score`：基于事件源的冲击烈度及置信度打分。
  - `exposure_score`：从 `exposure_strength` 结合定价权及传导能力调节得出。
  - `earnings_score`：由传导渠道（`revenue`/`cost`/`spread`/`inventory`）、业绩弹性及传导时滞 `lag_days` 折扣得出。
  - `sentiment_score`：画像基准 50 分及角色/领头羊属性溢价。
  - `trend_score`：个股最新技术面趋势强度（从 `signals.trend_score` 获取，缺失时为 50）。

- **返回结构约定**：
  - `GET /api/events/{event_id}/reaction` 推荐读取 `event`、`commodity_impacts`、`v2_reaction_scores`
  - `GET /api/stocks/{symbol}/commodity-exposure` 推荐读取 `stock`、`commodity_profiles`
  - 为兼容早期调用，接口仍保留 `reactions` / `profiles` 别名字段




## 历史回测与参数校准

先确保 `data/parquet/factors/signals.parquet` 和
`data/parquet/market/daily_prices.parquet` 包含足够历史。信号按收盘后生成处理，
下一交易日开盘建仓，默认持有 5 个交易日；一字涨停或停牌无法买入的信号会被剔除，
一字跌停或停牌无法卖出时最多顺延 5 个交易日。

```bash
cd backend
python -m app.cli backtest --holding-period 5 --transaction-cost-bps 5
```

结果写入 `data/backtest/`，包括交易明细、逐期 IC、五分位收益、绩效表和
`summary.json`。完成至少 20 个有效 IC 截面且有 100 条可执行交易后，可生成线上
校准文件：

```bash
python -m app.cli calibrate --holding-period 5 --transaction-cost-bps 5
```

校准文件默认写入 `data/research_calibration.json`。可通过
`CALIBRATION_PATH` 指定其他路径；线上信号的 `metrics` 会记录实际使用的权重、
阈值和校准来源。样本不足或三个基础因子平均 IC 均不为正时，命令会拒绝覆盖参数。

## 云服务器部署

服务器已有 Docker 时：

```bash
git clone <repository-url> AStock
cd AStock
cp .env.example .env
docker compose up --build -d
curl http://127.0.0.1:8080/api/health
```

当前 Compose 不对宿主机暴露端口，Web 容器加入现有 Caddy Docker 网络。
请将示例域名替换为自己的域名：

```caddyfile
quant.example.com {
    reverse_proxy aquant-web:80
}
```

需要的 DNS 记录：

- 类型：`A`
- 主机记录：自定义子域名
- 记录值：云服务器公网 IPv4

若服务器仅通过私有网络暴露，则无需配置公网 DNS。

## 下一阶段

1. 对象存储支持（将 Parquet 写入 MinIO/S3）
2. 幸存者偏差处理、组合构建和绩效归因
3. 扩展历史信号覆盖并建立滚动样本外验证
4. 实盘信号推送（如企业微信、钉钉等机器人通知）
