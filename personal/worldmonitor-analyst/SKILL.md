---
name: worldmonitor-analyst
description: "Use when 深度分析/情景推演/模拟Pro. WorldMonitor via bootstrap API."
version: 1.0.0
author: Hermes
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [intelligence, analysis, scenario, pro-simulation]
---

# WorldMonitor Pro 模拟（免 key）

把 WorldMonitor Pro 付费功能用公开 bootstrap API（`/api/bootstrap?tier=fast&public=1`，免 key）模拟出来，再叠加 Hermes LLM 分析。数据缓存 /tmp/wm_bootstrap.json（5 分钟 TTL）。

## 触发场景

- "模拟 WM Analyst" / "深度分析全球局势" / "今天局势怎么解读"
- "情景推演"（美伊/台海/关税…升级会怎样）
- "国家风险评级" / "哪个国家最危险" / "航运/咽喉点分析"

## Pro 功能 → 模拟对照

| Pro 功能 | 模拟方式 | 数据来源 |
|---|---|---|
| WM Analyst | `fetch_wm_pro.py` 全量 → Hermes LLM 深度解读 | worldBrief + gdeltIntel + marketQuotes |
| Scenario Engine | 预测市场 + AI 预测 + 新闻 → Hermes 三情景推演 | predictions / forecasts |
| Route Explorer | shippingStress + shippingRates + 战区态势 | shippingStress / theaterPosture |
| Resilience/国家风险 | CII v8 riskScores（UA 93 分等） | riskScores.ciiScores |
| Scheduled digests | Hermes cron + fetch_wm.py/fetch_wm_pro.py | — |
| MCP access | 不需要——REST 公开端点直接可用 | — |

## 命令

```bash
# 全维度 Pro 数据（世界简报/国家风险/市场/预测/航运/情报）
python3 ~/.hermes/skills/research/worldmonitor-analyst/scripts/fetch_wm_pro.py
# 分块
python3 .../fetch_wm_pro.py --section risk|markets|forecasts|shipping|intel
python3 .../fetch_wm_pro.py --brief        # 只要世界简报
python3 .../fetch_wm_pro.py --refresh      # 强制刷新缓存
# 新闻（基础版，见 worldmonitor-intel skill）
python3 ~/.hermes/skills/research/worldmonitor-intel/scripts/fetch_wm.py
```

## 分析输出框架（LLM 深度解读时用）

1. **局势主线**：worldBrief 提炼 1-3 条主线
2. **风险矩阵**：TOP 风险国家（CII 分 + 趋势 + 军事活动贡献）→ 对全球/供应链/市场的影响
3. **市场联动**：涨幅榜 + 宏观信号（verdict=CASH/SQUEEZE/DEFENSIVE…）→ 资金面解读
4. **情景推演**：选主题 → 基准/升级/缓和三情景 + 概率（参考预测市场 yes 价）+ 触发信号（哪些新闻关键词出现即转向）
5. **关注清单**：接下来 24-48h 跟踪点（事件、数据、警报）

## 定时简报（digest 模拟）

```bash
# 每天 08:30 推送全球简报（示例 cron prompt）
# "运行 fetch_wm_pro.py --brief 和 fetch_wm.py --brief，整理成 10 条以内的今日全球简报推送"
```
cron 创建用 cronjob action=create，schedule="30 8 * * *"，enabled_toolsets=["terminal"]。

## 预测-验证闭环（每日复盘）

**标准节奏（用户偏好 2026-08 起）：早上预测 → 晚上复盘**

- **早上（~8:30 开盘前）**：拉新闻（fetch_wm.py）+ 行情（wm_forecast.py prices）+ 姜汁汽水观点（upmarker-vs-wm）→ 写当日预测到 `~/.hermes/wm_forecasts.json`（方向 + 区间 + 基准价 + 理由）→ 推送
- **晚上（~17:30 收盘后）**：`wm_forecast.py verify` 验证当日预测 + `stats` 累计命中率 + 复盘"为什么错"（对照当日新闻）→ 推送

**记录**：分析后由 agent 用 write_file 写 `~/.hermes/wm_forecasts.json`（格式见下方），包含 direction(up/down/flat) + low/high 区间 + rationale + base_price。

**验证**：
```bash
python3 ~/.hermes/skills/research/worldmonitor-analyst/scripts/wm_forecast.py verify   # 验证最近未验证预测
python3 .../wm_forecast.py verify --date 2026-08-05   # 指定日期
python3 .../wm_forecast.py stats                      # 累计命中率
python3 .../wm_forecast.py prices                     # 行情快照（黄金/电信A/H/BOTZ）
```

**数据源**：bootstrap（GC=F 黄金等大宗）+ Yahoo chart API（601728.SS / 0728.HK / BOTZ 等，直连可用）。

**JSON 格式**：
```json
{"2026-08-04": {"gold_gcf": {"symbol": "GC=F", "source": "bootstrap",
  "direction": "up", "low": 4090, "high": 4190,
  "rationale": "…", "base_price": 4120.6, "verified": false}}}
```
verify 后自动写入 actual / range_hit / dir_hit / verified。

**命中判定**：收盘价 ∈ [low, high] = 区间命中；方向与实际涨跌符号一致（flat 取 |涨跌|<1%） = 方向命中。

**可加 cron**（早预测晚复盘二选一或都要）：
- 早 8:30: prompt "运行 wm_forecast.py prices 和 fetch_wm.py --brief，结合姜汁汽水观点（upmarker-vs-wm skill），生成今日黄金/电信A/电信H/BOTZ预测写入 wm_forecasts.json，推送预测简报"
- 晚 17:30: prompt "运行 wm_forecast.py verify 和 stats，对未命中预测对照今日新闻复盘原因，推送复盘报告"
- schedule: "30 8 * * 1-5" / "30 17 * * 1-5"，enabled_toolsets: ["terminal", "file"]

## 踩坑

1. bootstrap 响应 ~700KB，务必缓存（脚本已做，5 分钟 TTL），不要每轮请求都拉
2. 数据结构：`data.<block>`；insights.worldBrief 带引用标注 [1][2]
3. riskScores 只有 Tier-1 国家（31 个），非全部国家；advisoryLevel 是 fallback 参考
4. `get-chokepoint-status` / `get-country-risk` 等端点 401 需 key —— 用 shippingStress 替代咽喉点数据
5. predictions = Polymarket 预测市场；forecasts = AI 预测（置信度 + 市场价）
6. 市场 quotes 的 change 是百分比数字（如 1.48 = +1.48%）
7. 脚本输出为原始数据，**必须叠加 LLM 分析**才等于"Pro 体验"——不要只打印原始 JSON
