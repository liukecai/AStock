# 商品知识库配置目录

本目录包含 A-Quant Insight 事件驱动系统的**商品知识图谱配置**。每个 YAML 文件对应一个商品，统一管理以下四层信息：

---

## 文件结构

每个 YAML 文件的字段说明：

### 顶级字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `commodity` | string | 商品唯一标识（与代码中 COMMODITY_KB key 一致） |
| `name` | string | 商品中文名称，用于日志和报告显示 |

### 关键词识别

| 字段 | 类型 | 说明 |
|---|---|---|
| `keywords` | list[str] | 触发该商品识别的关键词（标题 + 摘要中出现任一即匹配） |
| `sector_keywords` | list[str] | 用于行业模糊匹配的关键词（股票的 industry 字段） |
| `default_sector` | str | 行业默认归属（无匹配时使用） |
| `upstream_sectors` | list[str] | 上游产业链行业名称列表 |
| `downstream_sectors` | list[str] | 下游产业链行业名称列表 |

### 精确股票映射（`exact_stocks`）

```yaml
exact_stocks:
  "600519":           # 股票代码（字符串，带引号避免 YAML 把 0 开头数字解析错误）
    relationship: upstream   # 或 downstream
    name: 贵州茅台            # 仅用于注释，不写入数据库
```

### 行业-板块系数映射（`sector_mappings`）

写入数据库 `commodity_sector_mappings` 表。

| 字段 | 类型 | 说明 |
|---|---|---|
| `sector` | str | 行业名（与 stocks.industry 匹配） |
| `relationship` | `upstream` / `downstream` | 产业链位置 |
| `coefficient` | float | 正数=受益，负数=受损；绝对值=影响强度（0.0~1.0）|

### 行业-股票敞口（`sector_exposures`）

写入数据库 `sector_stock_exposures` 表。

| 字段 | 类型 | 说明 |
|---|---|---|
| `sector` | str | 行业名 |
| `symbol` | str | 股票代码（带引号）|
| `exposure` | float | 敞口强度，0~100，通常为 100.0 |

### 公司商品画像（`company_profiles`）

写入数据库 `company_commodity_profiles` 表，用于 V2 传导评分。

| 字段 | 类型 | 说明 |
|---|---|---|
| `symbol` | str | 股票代码 |
| `role` | str | `upstream_resource` / `midstream_processing` / `downstream_manufacturing` / `upstream_service` / `transport` |
| `channel` | str | `revenue`（收入直接传导）/ `cost`（成本传导）/ `spread`（价差）/ `inventory`（库存）|
| `benefit_when_price_up` | bool | 商品价格上涨时该公司是否受益 |
| `benefit_when_price_down` | bool | 商品价格下跌时该公司是否受益 |
| `exposure_strength` | float 0-100 | 商品敞口强度 |
| `pricing_power` | float 0-100 | 定价权（能否将价格波动转嫁给客户）|
| `inventory_sensitivity` | float 0-100 | 库存敏感度 |
| `pass_through_ability` | float 0-100 | 成本转嫁能力 |
| `earnings_elasticity` | float 0-100 | 业绩对商品价格的弹性 |
| `lag_days` | int | 价格变动传导到业绩的平均滞后天数 |
| `evidence` | str | 人工撰写的逻辑依据（用于报告展示）|

---

## 添加新商品步骤

1. 新建 `<商品代码>.yaml` 文件（参考 `oil.yaml` 为模板）
2. 填写所有必填字段
3. 重启 API 容器（或调用 `POST /api/admin/reload-kb` 热重载，如已实现）
4. 调用 `POST /api/events/rebuild` 重建历史事件索引（可选）

> ⚠️ 股票代码请务必用双引号包裹（如 `"000001"`），防止 YAML 将 `000001` 解析为整数 `1`。
