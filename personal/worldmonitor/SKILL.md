---
name: worldmonitor
description: "Use when 今天大事/全球大事. WorldMonitor intel via free REST API."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [news, geopolitics, intelligence, osint, api]
    homepage: https://github.com/koala73/worldmonitor
platforms: [linux, macos, windows]
---

# WorldMonitor — 全球实时情报数据访问

WorldMonitor = 全球新闻聚合 + 地缘政治监控 + 基础设施跟踪 的实时情报仪表盘。
GitHub: https://github.com/koala73/worldmonitor (78.6k⭐, AGPL-3.0, 作者 koala73/Elie Habib)
官方在线站: https://www.worldmonitor.app/ (免登录免费看大屏)

## 访问层级（重要）

| 方式 | 地址 | 认证 |
|---|---|---|
| Web 大屏 | https://www.worldmonitor.app/ | 免费无门槛 |
| MCP server | https://worldmonitor.app/mcp | `tools/list` 公开；**`tools/call` 需 `X-WorldMonitor-Key` header**（无 key 一律 401），key 在 worldmonitor.app/pro 注册（wm_ 开头，Pro $39.99/月起） |
| REST API | https://api.worldmonitor.app | **带 `public=1` 的端点免 key 可用** ← 日常首选 |

**核心结论：日常"今天大事/全球大事"直接 curl REST 公开端点即可，不需要 MCP key。**

## 免 key REST 端点（已验证 2026-08）

| 端点 | 内容 |
|---|---|
| `/api/news/v1/list-feed-digest?variant=full&lang=en&public=1` | 新闻摘要，17 分类（politics/us/europe/middleeast/tech/ai/finance/commodities/gov/africa/latam/asia/energy/thinktanks/crisis/layoffs/intel），每类 items 最多 20 条 |
| `/api/telegram-feed?limit=50` | Telegram 情报流（多语言，含 BREAKING） |
| `/api/oref-alerts` | 以色列防空警报状态 |
| `/api/natural/v1/list-natural-events?days=30` | 自然灾害（洪水/山火/干旱） |
| `/api/conflict/v1/list-acled-events` | ACLED 冲突事件 |
| `/api/wildfire/v1/list-fire-detections` | 野火探测 |
| `/api/seismology/v1/list-earthquakes` | 地震 |
| `/api/gpsjam` | GPS 干扰区 |
| `/api/intelligence/v1/get-pizzint-status?include_gdelt=true` | 情报状态(GDELT) |
| `/api/military/v1/get-usni-fleet-report` | ⚠️ 401，需 key |
| **`/api/bootstrap?tier=fast&public=1`** | **⭐ 宝库端点：~700KB 打包全部 24 个数据块，一次拉全**（见下） |

## bootstrap 大端点（一次拉全部维度，2026-08 验证）

`/api/bootstrap?tier=fast&public=1` 响应结构 `data.<block>`，24 个数据块覆盖 Pro 大部分能力且免 key：

- `insights.worldBrief` — AI 世界简报（带引用标注 [1][2]）← 相当于 Pro 的 get_world_brief
- `riskScores.ciiScores` — CII v8 国家风险（UA 93 分/do-not-travel 等 31 个 Tier-1 国家）
- `theaterPosture.theaters` — 9 个战区态势（iran/taiwan/baltic…normal/军机/舰船数）
- `marketQuotes.quotes`(59) / `commodityQuotes.quotes`(33) — 指数/大宗，change 是**百分比数字**
- `macroSignals` — 7 信号（verdict=CASH / liquidity SQUEEZE / fearGreed 等）
- `predictions.geopolitical` — Polymarket 预测市场（yes 价+量）
- `forecasts.predictions` — AI 预测（confidence + calibration.marketPrice）
- `shippingStress.carriers` / `shippingRates` — 航运压力/运价（替代 401 的 chokepoint 端点）
- `gdeltIntel.topics` / `socialVelocity` / `wsbTickers` / `earthquakes` / `outages` / `ddosAttacks` / `trafficAnomalies` / `weatherAlerts` / `positiveGeoEvents` / `temporalAnomalies` / `spending` / `correlationCards` / `flightDelays`

**用法**：`curl -s "https://api.worldmonitor.app/api/bootstrap?tier=fast&public=1"`，约 700KB，**务必缓存 5 分钟**（/tmp/wm_bootstrap.json），别每轮请求都拉。bootstrap 只有实时价，**无历史日线**——验证历史预测要换雅虎日线（`query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1mo&interval=1d`，按日期取收盘）。

## 新闻 JSON 结构

```json
{"categories": {"politics": {"items": [{"source": "AP News", "title": "...", "link": "...",
  "publishedAt": 1785812220000, "isAlert": true, "importanceScore": 120,
  "corroborationCount": 1, "storyMeta": {...}, "threat": "..."}]}}, "generatedAt": "..."}
```

- `publishedAt` 是 **unix 毫秒**，转 UTC+8
- 排序用 `importanceScore` 降序；警报过滤 `isAlert == true`
- 把英文分类名映射成中文再展示（见 scripts/daily_brief.py 的 CN 字典）

## 发现新端点的方法

浏览器打开 https://www.worldmonitor.app/ 进 Dashboard，console 执行：
```js
performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes('api.')||n.includes('/api/'))
```
前端调用的真实端点全在里面（带 `public=1` 的就是免 key 的）。注意：browser_vision 在非视觉模型上会失败，用 browser_console 提取 innerText 代替。

## Hermes MCP 接入（可选，需 key）

```bash
hermes config set mcp_servers.worldmonitor.url "https://worldmonitor.app/mcp"
hermes config set mcp_servers.worldmonitor.timeout 180
hermes config set mcp_servers.worldmonitor.connect_timeout 60
hermes config set mcp_servers.worldmonitor.enabled true
# 拿到 key 后加 headers：
hermes config set mcp_servers.worldmonitor.headers.X-WorldMonitor-Key "wm_xxx"
```
- ⚠️ 直接 patch config.yaml 会被 Hermes 安全机制拒绝（"Agent cannot modify security-sensitive configuration"），必须走 `hermes config set` 点路径
- MCP 工具在 Hermes **启动时**发现，无热加载，改完必须重启才生效
- 工具前缀 `mcp_worldmonitor_*`，共 59 个（get_world_brief / get_alert_digest / get_conflict_events / get_market_data 等）

## 快速出简报

```bash
python3 ~/.hermes/skills/research/worldmonitor/scripts/daily_brief.py
```
输出今日警报 + 高优先级新闻（北京时间）。用户说"今天大事/全球大事"时优先用它，不要 web_search。

## 踩坑
- MCP `tools/list` 成功 ≠ `tools/call` 可用——call 无 key 必 401，先测 REST 公开端点
- Dashboard LIVE NEWS 面板点 PLAY 后可能仍显示 "READY WHEN YOU ARE"（远程浏览器媒体流限制），改用 REST API 拿数据
- `get-usni-fleet-report` 等部分端点无 key 返回 401，属正常，用公开端点替代
- 官网根路径/未知路径返回 SPA HTML 而非 JSON，探测端点时看 HTTP 404 JSON 错误体（含 "No API endpoint matches"）可确认是真实 API
