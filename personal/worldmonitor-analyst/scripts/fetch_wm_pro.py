#!/usr/bin/env python3
"""WorldMonitor Pro 功能模拟 — bootstrap 公开数据块解析（免 key）。
用法: python3 fetch_wm_pro.py [--brief] [--refresh] [--section risk|markets|forecasts|shipping|intel|all]
"""
import json, os, ssl, sys, argparse, urllib.request, time
from datetime import datetime, timezone, timedelta

BASE = "https://api.worldmonitor.app"
BOOT_URL = f"{BASE}/api/bootstrap?tier=fast&public=1"
CACHE = "/tmp/wm_bootstrap.json"
CACHE_TTL = 300  # 5 分钟
TZ = timezone(timedelta(hours=8))

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE
_HDRS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def load(refresh=False):
    if not refresh and os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < CACHE_TTL:
        return json.load(open(CACHE))
    req = urllib.request.Request(BOOT_URL, headers=_HDRS)
    with urllib.request.urlopen(req, timeout=40, context=_ctx) as r:
        d = json.loads(r.read().decode())
    json.dump(d, open(CACHE, "w"))
    return d


def sec_worldbrief(d):
    ins = d.get("insights", {})
    wb = ins.get("worldBrief") or ""
    out = ["## 🌍 世界简报 (AI 生成)"]
    out.append(wb[:1500])
    extra = ins.get("extra") or ins.get("headlines") or ins.get("alerts")
    if extra:
        out.append(f"\n补充: {json.dumps(extra, ensure_ascii=False)[:400]}")
    return out


def sec_risk(d):
    rs = d.get("riskScores", {}).get("ciiScores", [])
    out = ["\n## ⚠️ 国家风险 CII v8 (按风险分排序 TOP 12)"]
    trend_map = {"TREND_DIRECTION_RISING": "↑升", "TREND_DIRECTION_FALLING": "↓降", "TREND_DIRECTION_STABLE": "→平"}
    for c in sorted(rs, key=lambda x: x.get("combinedScore", 0), reverse=True)[:12]:
        trend = trend_map.get(c.get("trend"), c.get("trend"))
        out.append(f"{c.get('region')}: {c.get('combinedScore')}分({trend}) 建议={c.get('advisoryLevel')} 军事活动贡献={c.get('components',{}).get('militaryActivity')}")
    tp = d.get("theaterPosture", {}).get("theaters", [])
    out.append("\n## 🎖️ 战区态势")
    for t in tp:
        ops = ",".join(t.get("activeOperations", [])) or "-"
        out.append(f"{t.get('theater')}: {t.get('postureLevel')} | 军机 {t.get('activeFlights')} | 舰船 {t.get('trackedVessels')} | 行动: {ops}")
    return out


def sec_markets(d):
    out = ["\n## 💹 市场快照"]
    mq = d.get("marketQuotes", {}).get("quotes", [])
    movers = sorted(mq, key=lambda x: abs(x.get("change", 0)), reverse=True)[:8]
    out.append("涨幅榜:")
    for m in movers:
        arrow = "▲" if m.get("change", 0) > 0 else "▼"
        out.append(f"  {m.get('display')} {m.get('price')} {arrow}{abs(m.get('change',0)):.2f}%")
    ms = d.get("macroSignals", {})
    out.append(f"宏观 verdict={ms.get('verdict')} (bullish {ms.get('bullishCount')}/{ms.get('totalCount')})")
    for k, v in (ms.get("signals") or {}).items():
        out.append(f"  {k}: {v.get('status')} (值 {v.get('value','-')})")
    return out


def sec_forecasts(d):
    out = ["\n## 🔮 预测市场 (Polymarket geopolitics TOP 6)"]
    for p in (d.get("predictions", {}).get("geopolitical", []) or [])[:6]:
        out.append(f"{p.get('title')[:90]} — yes ${p.get('yesPrice')} (量 {int(p.get('volume',0)):,})")
    fc = d.get("forecasts", {}).get("predictions", []) or []
    out.append(f"\n## 🧠 AI 预测 ({len(fc)} 条, TOP 5)")
    for f in sorted(fc, key=lambda x: x.get("confidence", 0), reverse=True)[:5]:
        cal = f.get("calibration", {}) or {}
        out.append(f"{cal.get('marketTitle','')[:90]} — 置信 {f.get('confidence')} | 市场价 {cal.get('marketPrice')} ({cal.get('source')})")
    return out


def sec_shipping(d):
    out = ["\n## 🚢 航运压力"]
    for c in (d.get("shippingStress", {}).get("carriers", []) or [])[:6]:
        arrow = "▲" if c.get("changePct", 0) > 0 else "▼"
        out.append(f"{c.get('name')} ({c.get('symbol')}): {c.get('price')} {arrow}{abs(c.get('changePct',0)):.2f}%")
    sr = d.get("shippingRates", {})
    if isinstance(sr, dict) and sr:
        out.append(f"运价快照: {json.dumps(sr, ensure_ascii=False)[:300]}")
    return out


def sec_intel(d):
    out = ["\n## 🕵️ GDELT 情报主题"]
    for t in (d.get("gdeltIntel", {}).get("topics", []) or [])[:6]:
        arts = t.get("articles", [])[:2]
        out.append(f"[{t.get('id')}]")
        for a in arts:
            out.append(f"  · {a.get('title','')[:90]} ({a.get('source')})")
    sv = d.get("socialVelocity", {})
    if sv:
        out.append(f"\nReddit 热度: {json.dumps(sv, ensure_ascii=False)[:300]}")
    wt = d.get("wsbTickers", [])
    if wt:
        out.append(f"\nr/wallstreetbets 热议: {json.dumps(wt, ensure_ascii=False)[:300]}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", action="store_true", help="只出世界简报")
    ap.add_argument("--refresh", action="store_true", help="强制刷新缓存")
    ap.add_argument("--section", default="all", help="all|risk|markets|forecasts|shipping|intel")
    args = ap.parse_args()

    d = load(args.refresh)
    if "__err__" in d:
        print("ERR:", d["__err__"])
        return
    d = d.get("data", d)

    lines = []
    if args.brief:
        lines = sec_worldbrief(d)
    elif args.section == "risk":
        lines = sec_risk(d)
    elif args.section == "markets":
        lines = sec_markets(d)
    elif args.section == "forecasts":
        lines = sec_forecasts(d)
    elif args.section == "shipping":
        lines = sec_shipping(d)
    elif args.section == "intel":
        lines = sec_intel(d)
    else:
        for fn in [sec_worldbrief, sec_risk, sec_markets, sec_forecasts, sec_shipping, sec_intel]:
            lines += fn(d)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
