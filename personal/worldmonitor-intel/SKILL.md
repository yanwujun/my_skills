---
name: worldmonitor-intel
description: "Use when 今天大事/全球新闻 asked. WorldMonitor intel via REST API."
version: 1.0.0
author: Hermes
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [news, intelligence, geopolitics, api]
---

# WorldMonitor 全球情报速查

实时抓取全球情报（新闻聚合 + 地缘冲突 + 灾害 + 市场），数据源 [koala73/worldmonitor](https://github.com/koala73/worldmonitor)（78k+⭐，worldmonitor.app 官方在线站）。

## 触发场景

- "今天全球有什么大事" / "今天大事" / "世界新闻" / "全球动态"
- 地缘冲突局势、灾害情况、中东/俄乌进展查询

## 快速使用（推荐）

```bash
python3 ~/.hermes/skills/research/worldmonitor-intel/scripts/fetch_wm.py          # 全维度
python3 ~/.hermes/skills/research/worldmonitor-intel/scripts/fetch_wm.py --brief  # 只要新闻摘要
python3 ~/.hermes/skills/research/worldmonitor-intel/scripts/fetch_wm.py --alerts 20 --news 20  # 自定义条数
```

输出：新闻总览（276+ 条 / 警报数）→ 🚨警报新闻 → 🔥高优先级 → Telegram 情报流 → 自然灾害 → 以色列警报 → 地震。

## 免 key 公开端点（public=1）

基础地址 `https://api.worldmonitor.app`：

| 端点 | 说明 |
|---|---|
| `/api/news/v1/list-feed-digest?variant=full&lang=en&public=1` | 17 分类新闻（politics/us/europe/middleeast/tech/ai/finance/commodities/gov/africa/latam/asia/energy/thinktanks/crisis/layoffs/intel），每类 20 条，含 isAlert/importanceScore/corroborationCount/threat |
| `/api/telegram-feed?limit=50` | 多语言情报电报流（含 BREAKING 快讯） |
| `/api/oref-alerts` | 以色列防空警报（alerts[]/historyCount24h） |
| `/api/natural/v1/list-natural-events?days=30` | 自然灾害（🟠🟡🔴 级别） |
| `/api/seismology/v1/list-earthquakes` | 全球地震 |
| `/api/conflict/v1/list-acled-events` | ACLED 冲突事件（当前返回空，可能需要参数） |
| `/api/wildfire/v1/list-fire-detections` | 野火 |
| `/api/gpsjam` | GPS 干扰 |
| `/api/military/v1/get-usni-fleet-report` | 舰队报告（**需 key，401**） |

更多端点：浏览器打开 worldmonitor.app 仪表盘后执行
`performance.getEntriesByType('resource').map(e=>e.name).filter(n=>n.includes('api.worldmonitor.app'))` 获取页面真实请求列表。

## MCP 接入（tools/call 需 key）

- MCP server: `https://worldmonitor.app/mcp`（Streamable HTTP）
- `tools/list` 公开（59 个工具）；**`tools/call` 必须带 `X-WorldMonitor-Key: wm_xxx` header**，否则 401
- key 获取：https://www.worldmonitor.app/pro（Pro $39.99/月起，年付 3 个月免费）
- Hermes 配置（拿到 key 后）：
  ```bash
  hermes config set mcp_servers.worldmonitor.headers.X-WorldMonitor-Key "wm_xxx"
  ```
  然后重启 Hermes，工具以 `mcp_worldmonitor_*` 前缀出现（get_world_brief / get_alert_digest / get_hotspot_escalation / get_conflict_events 等）

## 踩坑

1. **REST 免 key，MCP call 要 key** —— 没 key 时用 REST 公开端点即可，能力覆盖新闻+情报+灾害
2. **时间戳是 Unix 毫秒**（publishedAt: 1785812220000），>1e11 需除以 1000
3. **新闻结构嵌套**：`categories.<name>.items[]`，每条含 source/title/link/isAlert/importanceScore/storyMeta
4. **SSL**：WSL 直连偶发证书问题，脚本用 CERT_NONE 兜底
5. **`api.worldmonitor.app` 根路径返回 SPA HTML**，不是 JSON；探测端点别从根路径猜
6. **config.yaml 禁止 agent 直接写**（安全保护），MCP 配置必须走 `hermes config set`
7. `get_alert_digest` / `get_world_brief` 等 MCP 工具描述带 Pro 字样，免费档调用会 401
