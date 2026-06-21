# A-Quant Insight

A 股趋势与舆情融合量化选股系统。当前版本是可运行的 V1 基线：FastAPI、Vue 3、SQLite、趋势/舆情/量能评分、定时任务与 Docker 部署。

> 仅供策略研究和工程验证，不构成投资建议。

## 已实现

- MA5 / MA20 / MA60、多头排列、20 日价格斜率、MA60 斜率与量比
- 确定性中文金融关键词情绪评分（无随机舆情）
- 5 日平均提及量计算 Burst
- `0.5 × Trend + 0.3 × Sentiment + 0.2 × Volume` 综合评分
- Dashboard、信号筛选、个股价格/均线图、新闻与因子详情
- SQLite 持久化、每日 16:30（Asia/Shanghai）信号计算
- AKShare 真实行情、失败重试、任务进度与演示模式隔离
- 巨潮资讯全市场公告增量采集、股票池过滤、去重与情绪评分
- Docker Compose 单机部署

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

核心系统依赖统一的 `news` 表，采集器写入以下字段：

| 字段 | 含义 |
| --- | --- |
| `id` | 来源侧唯一 ID 或正文哈希 |
| `symbol` | 6 位股票代码 |
| `published_at` | ISO 8601 时间 |
| `title` | 新闻或公告标题 |
| `source` | 巨潮、东财等 |
| `url` | 原文地址 |
| `sentiment` | `[-1, 1]` |
| `keywords` | JSON 字符串数组 |

推荐先接巨潮正式公告 API/授权数据源。免费新闻网页抓取存在反爬、版权和结构变化风险，不应放进策略核心进程。

## API

- `GET /api/health`：服务和数据状态
- `GET /api/dashboard`：最新信号及汇总
- `GET /api/stocks/{symbol}`：个股行情、新闻、因子和最新信号
- `POST /api/pipeline/run`：手动重算信号

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

1. 巨潮公告真实采集与实体/股票代码映射
2. Parquet 行情冷存储 + SQLite/PostgreSQL 元数据
3. 回测引擎、交易成本、停牌/涨跌停与幸存者偏差处理
4. 行业中性化、因子 IC、组合构建和绩效归因
5. 鉴权、任务监控、失败告警与实盘信号推送
