#!/usr/bin/env python3
"""WorldMonitor 公开 API 快速抓取 — 免 key 实时全球情报摘要。
用法: python3 fetch_wm.py [--news N] [--alerts N] [--brief] [--all]
"""
import json, ssl, sys, argparse, urllib.request
from datetime import datetime, timezone, timedelta

BASE = "https://api.worldmonitor.app"
TZ = timezone(timedelta(hours=8))
CAT_CN = {"politics": "政治", "us": "美国", "europe": "欧洲", "middleeast": "中东",
          "tech": "科技", "ai": "AI", "finance": "财经", "commodities": "大宗",
          "gov": "政府", "africa": "非洲", "latam": "拉美", "asia": "亚洲",
          "energy": "能源", "thinktanks": "智库", "crisis": "危机",
          "layoffs": "裁员", "intel": "情报"}

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE
_HDRS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def get(url):
    try:
        req = urllib.request.Request(url, headers=_HDRS)
        with urllib.request.urlopen(req, timeout=25, context=_ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"__err__": f"{type(e).__name__}: {str(e)[:120]}"}


def fmt(ms):
    if isinstance(ms, (int, float)) and ms > 1e11:
        ms /= 1000
    try:
        return datetime.fromtimestamp(ms, TZ).strftime("%m-%d %H:%M")
    except Exception:
        return "?"


def fetch_news(limit_alerts=15, limit_top=15):
    d = get(f"{BASE}/api/news/v1/list-feed-digest?variant=full&lang=en&public=1")
    if "__err__" in d:
        return [f"NEWS ERR: {d['__err__']}"]
    items = []
    for cat, val in d.get("categories", {}).items():
        for it in val.get("items", []):
            it["_cat"] = CAT_CN.get(cat, cat)
            items.append(it)
    out = [f"### 新闻总览: {len(items)} 条 / 警报 {sum(1 for x in items if x.get('isAlert'))} 条 (北京时间 {datetime.now(TZ).strftime('%m-%d %H:%M')})"]
    seen = set()
    out.append("\n== 🚨 警报新闻 ==")
    for x in sorted([i for i in items if i.get("isAlert")],
                    key=lambda i: i.get("importanceScore", 0), reverse=True)[:limit_alerts]:
        k = x["title"][:40]
        if k in seen:
            continue
        seen.add(k)
        out.append(f"[{x['_cat']}|{x['source']}|{fmt(x.get('publishedAt'))}] {x['title'][:110]}")
    seen = set()
    out.append("\n== 🔥 高优先级 ==")
    for x in sorted(items, key=lambda i: i.get("importanceScore", 0), reverse=True)[:limit_top]:
        k = x["title"][:40]
        if k in seen:
            continue
        seen.add(k)
        out.append(f"[{x['_cat']}|{x['source']}|{x.get('importanceScore')}] {x['title'][:110]}")
    return out


def fetch_telegram(limit=10):
    d = get(f"{BASE}/api/telegram-feed?limit={limit}")
    if "__err__" in d:
        return [f"TG ERR: {d['__err__']}"]
    items = d if isinstance(d, list) else d.get("items") or d.get("messages") or []
    out = [f"\n== 📰 Telegram 情报 feed ({len(items)}) =="]
    for m in items[:limit]:
        txt = (m.get("text") or m.get("message") or "").replace("\n", " ")[:130]
        out.append(f"[{m.get('channel') or m.get('source') or '?'}] {txt}")
    return out


def fetch_natural(limit=8):
    d = get(f"{BASE}/api/natural/v1/list-natural-events?days=30")
    if "__err__" in d:
        return [f"NAT ERR: {d['__err__']}"]
    items = d.get("events") or d.get("items") or (d if isinstance(d, list) else [])
    out = [f"\n== 🌍 自然灾害 30天 ({len(items)}) =="]
    for e in items[:limit]:
        out.append(f"[{e.get('type') or e.get('event_type')}] {e.get('title') or e.get('description') or ''} | {e.get('location') or e.get('country') or ''}")
    return out


def fetch_oref():
    d = get(f"{BASE}/api/oref-alerts")
    if "__err__" in d:
        return [f"OREF ERR: {d['__err__']}"]
    a = d.get("alerts", [])
    return [f"\n== 🚨 以色列 Oref 警报: 当前 {len(a)} 条 / 24h {d.get('historyCount24h', 0)} =="] + \
           [f"[{x.get('title') or x.get('type')}] {x.get('desc') or x.get('location') or ''}" for x in a[:8]]


def fetch_earthquakes(limit=8):
    d = get(f"{BASE}/api/seismology/v1/list-earthquakes")
    if "__err__" in d:
        return [f"EQ ERR: {d['__err__']}"]
    items = d.get("events") or d.get("items") or (d if isinstance(d, list) else [])
    out = [f"\n== 🌊 地震 ({len(items)}) =="]
    for e in items[:limit]:
        out.append(f"M{e.get('magnitude') or e.get('mag') or '?'} {e.get('place') or e.get('location') or ''} | {fmt(e.get('time') or e.get('timestamp'))}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--news", type=int, default=15, help="高优先级条数")
    ap.add_argument("--alerts", type=int, default=15, help="警报条数")
    ap.add_argument("--brief", action="store_true", help="只出新闻摘要")
    ap.add_argument("--all", action="store_true", help="全部维度")
    args = ap.parse_args()

    lines = fetch_news(args.alerts, args.news)
    if not args.brief or args.all:
        lines += fetch_telegram()
        lines += fetch_natural()
        lines += fetch_oref()
        lines += fetch_earthquakes()
    print("\n".join(lines))


if __name__ == "__main__":
    main()
