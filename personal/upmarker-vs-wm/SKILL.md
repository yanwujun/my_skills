---
name: upmarker-vs-wm
description: "Use when 对比姜汁汽水/UP主观点汇总. UP主+评论区vs WorldMonitor."
version: 1.0.0
author: Hermes
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [bilibili, geopolitics, finance, comparison]
---

# UP主观点 vs WorldMonitor 对比

把 B站财经/地缘 UP 主（主对象：战国时代_姜汁汽水 UID:1039025435）的观点 + 其评论区高赞"大佬"观点，与 WorldMonitor 实时数据/AI 预测对比，输出结构化报告。

## 触发场景

- "对比姜汁汽水" / "UP主分析汇总" / "他评论区有什么观点"
- "看下 UP 主和 AI 谁说得对" / "汇总他们分析"

## 数据源

| 数据 | 接口 | 说明 |
|---|---|---|
| 动态列表 | `GET https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={mid}&timezone_offset=-480` | 视频动态含 `modules.module_dynamic.major.archive`（bvid/aid/title），文字动态含 `desc.text`；翻页用 `data.offset` |
| 视频评论 | `GET https://api.bilibili.com/x/v2/reply?type=1&oid={aid}&sort=2&ps=20` | **sort=2 = 按热度(点赞)排序**，正好筛"大佬"评论；字段 `member.uname/like/content.message/member.level_info.current_level` |
| WorldMonitor | `fetch_wm.py` / `fetch_wm_pro.py`（见 research/worldmonitor-intel 与 worldmonitor-analyst） | 新闻/CII风险/预测市场/宏观信号 |
| 行情验证 | `wm_forecast.py prices` + 雅虎 chart API | 实盘对照 |

## 流程

### 1. 注入 SESSDATA（必须浏览器，终端 curl 会被风控 -1/-403）

Chrome 拿 SESSDATA → browser_navigate 到 `https://www.bilibili.com/` → browser_console:
```js
document.cookie = "SESSDATA=<value>; domain=.bilibili.com; path=/; SameSite=None; Secure";
```
然后导航到 `https://space.bilibili.com/{mid}/dynamic`。

### 2. 抓动态（browser_console fetch，credentials:'include'）

循环 2-3 页动态 feed，收集：视频（标题/bv/aid/时间）+ 文字动态观点。**免费文字动态的观点密度最高**（姜汁汽水 7/17-7/22 的动态是精华：石油85-90减仓、黄金趋势线、A股3750-3800加仓、粮食新高减仓）。

### 3. 抓评论

选 2-3 个重点视频（最新期 + 高播放地缘大片 + 宏观综述），`sort=2` 拉 top 12。提取 👍高赞 + 内容专业的评论（过滤"前排/打卡/声音好听"类）。评论里常有反方观点和补充分析（如半导体技术面看空、日韩地缘劣势论）。

### 4. 观点结构化

按主题归档：黄金/石油/A股/芯片半导体/地缘/粮食/汇率/宏观。每条 = {来源: UP主|评论区|AI, 观点, 方向/价位, 日期}。

### 5. WorldMonitor 对照 + 报告

报告模板：
```
# ⚔️ 姜汁汽水 vs WorldMonitor | 对比报告 (日期)
## N 个主题对比（每个）:
| 来源 | 观点 | 判定 |
| UP主 | … | ✅/❌/⏳ |
| 评论区大佬 | … | … |
| WorldMonitor/AI | 实时数据/预测 | … |
→ 结论：一致/分歧 + 实盘证据
## 🏆 总结：谁占优 + 分歧点 + 下轮验证点
```

## 姜汁汽水已知观点库（2026-08 更新，持续补充）

- 石油：WTI **85-90 减仓**（7/20 触发 84.6），底仓成本 70-65，跌回 70 带止损加仓；美长债利率驱动从油价→期限溢价，全球消费差；**9 月补库周期**（美元弱+油价低→各国补库）
- 黄金：4800+ 禁止加仓区；25 年底 4200 ✅已兑现；7/21 "关注能否打破下跌趋势线，等回踩"；**8/5 更新：8 月就是加仓节点，震荡上行可能超 4200 后回踩，风险不大**（10年-2年利差快速上升=托底信号）
- A股：上证 **3740-3800 救市加仓位，只加一笔**（反弹≠反转）；科技抱团被质疑；**8/5 更新：8 月科技震荡+传统涨，9 月科技拉升+传统回调；8 月横盘 9 月拉升**
- 半导体：**8 月盘整 → 9 月反弹（反弹≠反转）→ 27 年初风险最大**（26 年杠杆问题、27 年基本面问题）
- 美股：9 月加息落地可能喷出**标普 8200-8500 = AI 泡沫破裂前最后一波**；**禁止追高/禁止定投 A股美股**；巴菲特指标比互联网泡沫更疯狂
- 中金高胜率行业：保险、原材料、电气设备、创新药、**电信（警惕 9 月回调）**
- 地缘：美伊"革命卫队 vs 行政机构双轨博弈"（想打时卫队放话，想谈时行政放话）；"美伊两种结局"；东大军事科技拼图需 5-10 年（评论区观点）
- 粮食：期货回到年内高点/创新高则**减仓**，成本低留底仓；国内粮油同比 +7.9% 需求稳
- 美联储：沃什"市场在替美联储紧缩"，信心大打折扣；利率曲线陡峭化是核心趋势；9-12 月不缩表
- 8/3 新视频（充电）：美日联合干预汇率、美联储核心重点、美元趋势、8月芯片震荡整理、8月A股+黄金有色
- **8/5 视频（免费抢先看）详细提炼见 references/jiangzhi-video-20260805.md，字幕全文见 references/jzq_video_20260805_subtitle.txt**

## 踩坑

1. **终端 curl 必被风控**（wbi/arc/search -403、动态 feed -1）——所有 B 站 API 都在 browser_console fetch（带 cookie 环境指纹）
2. SESSDATA 用完即弃，不落盘
3. 充电专属（30/88元/月）内容只能看标题，观点靠免费动态+评论推断
4. 评论 sort=2 是热度不是时间；Lv5-6 + 高赞 = 值得提取的大佬评论
5. 动态置顶项是 `DYNAMIC_TYPE_DRAW`（图文），`major.archive` 为空，别当视频解析
6. 提取观点时区分"UP主原话"与"评论区观点"，来源必须标注清楚
