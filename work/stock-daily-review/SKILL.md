---
name: stock-daily-review
description: "Use when 股票复盘/今日行情/持仓分析 asked. 腾讯行情字段映射+板块抓取+复盘流程。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [stock, finance, review, a-share, etf]
---

# 股票每日复盘（A股指数 / ETF / 美股）

用户每天早上预测、晚上手动复盘。本 skill 固化数据抓取脚本与字段映射，避免每次临时写代码读错字段。

## 数据源（全部免 key）

| 用途 | 接口 | 说明 |
|---|---|---|
| A股指数/ETF/个股 | `http://qt.gtimg.cn/q=code1,code2` | gbk 编码，`~` 分隔，**昨收为准** |
| 美股 | 同上，`usDJI`/`usIXIC`/`usINX`/`usNVDA` 等代码 | **字段位置与 A 股不同** |
| 行业板块 | 东财 `push2.eastmoney.com/api/qt/clist/get` | 易限流，需重试 |
| 板块备选 | 新浪 `vip.stock.finance.sina.com.cn/q/view/newSinaHy.php` | gbk，`eval` 解析 |

## 字段映射（最高频错误点）

A股/ETF（f[1] 起为名称）：
- f[3] 现价, f[4] 昨收, f[5] 今开, f[30] 时间, f[31] 涨跌额, f[32] 涨跌%, f[33] 最高, f[34] 最低, f[37] 成交额(万元，/10000=亿), f[38] 换手%

**美股（us 代码）字段位置不同**：f[3] 现价, f[4] 昨收, f[5] 今开, f[31] 涨跌额, f[32] 涨跌%。用 A 股字段位解析美股会得到离谱涨跌幅（曾解析出 53797%）。

## 常用代码

- 指数: sh000001 上证 / sz399001 深成 / sz399006 创业板 / sh000300 沪深300 / sh000905 中证500 / sh000688 科创50
- 机器人ETF: sz159770 天弘 / sh562500 华夏 / sh562360 银华
- 黄金ETF: sh518880 华安 / sz159934 易方达 / sz159937 博时 / sh518800 国泰
- 中国电信: sh601728
- 创新药ETF: sz159992 银华 / sz159570 港股通汇添富 / sh512010 医药易方达
- 美股: usDJI / usIXIC / usINX / usNVDA / usTSLA

## 复盘流程

1. 收盘后（15:00 后）抓 A 股指数 + 持仓/候选 ETF（qt.gtimg.cn）
2. 抓美股昨收（us 代码，注意国际字段位）
3. 抓行业板块涨跌榜（东财 → 限流换新浪）
4. 输出：指数涨跌表 → 持仓浮盈（现价 vs 成本）→ 待接标的 vs 挂单价 → 外围 → 小结

## 踩坑

- 字段映射：A 股与美股字段位不同，先判代码前缀再解析
- 东财板块接口限流（RemoteDisconnected）→ sleep 2s 重试 3 次 + Referer: https://quote.eastmoney.com/，仍失败换新浪
- 新浪板块接口 eval 解析可能触发审批超时（命令超时需用户确认）
- 行情接口 WSL 直连可通；WorldMonitor 新闻 API 需代理（见 worldmonitor-intel skill）
