#!/usr/bin/env python3
"""WorldMonitor 今日全球大事简报 — 免 key 公开 REST API。
用法: python3 daily_brief.py [--limit 25]
输出: 今日警报 + 高优先级新闻（北京时间）
"""
import json, ssl, sys, urllib.request
from datetime import datetime, timezone, timedelta

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HDRS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
BASE = "https://api.worldmonitor.app"
TZ = timezone(timedelta(hours=8))
CN = {"politics": "政治", "us": "美国", "europe": "欧洲", "middleeast": "中东",
      "tech": "科技", "ai": "AI", "finance": "财经", "commodities": "大宗商品",
      "gov": "政府", "africa": "非洲", "latam": "拉美", "asia": "亚洲",
      "energy": "能源", "thinktanks": "智库", "crisis": "危机", "layoffs": "裁员",
      "intel": "情报"}


def get(url):
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"__err__": str(e)[:120]}


def fmt(ms):
    try:
        return datetime.fromtimestamp(ms / 1000, TZ).strftime("%H:%M")
    except Exception:
        return "?"


def main():
    limit = 25
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    d = get(f"{BASE}/api/news/v1/list-feed-digest?variant=full&lang=en&public=1")
    if "__err__" in d:
        print("ERROR:", d["__err__"])
        return 1
    allitems = []
    for cat, val in d.get("categories", {}).items():
        for it in val.get("items", []):
            it["_cat"] = CN.get(cat, cat)
            allitems.append(it)
    alerts = [x for x in allitems if x.get("isAlert")]
    top = sorted(allitems, key=lambda x: x.get("importanceScore", 0), reverse=True)
    print(f"### WorldMonitor 今日全球大事 | {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')} 北京时间"
          f" | {len(allitems)} 条新闻 / {len(alerts)} 条警报")
    print("\n== 🚨 警报 ==")
    seen = set()
    for x in alerts:
        t = x["title"][:110]
        k = t[:40]
        if k in seen:
            continue
        seen.add(k)
        print(f"[{x['_cat']}|{x['source']}|{fmt(x.get('publishedAt'))}] {t}")
    print(f"\n== 🔥 高优先级 Top {limit} ==")
    seen = set()
    for x in top:
        t = x["title"][:110]
        k = t[:40]
        if k in seen:
            continue
        seen.add(k)
        print(f"[{x['_cat']}|{x['source']}|{x.get('importanceScore')}] {t}")
        if len(seen) >= limit:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
