#!/usr/bin/env python3
"""WorldMonitor 预测-验证闭环。
用法:
  python3 wm_forecast.py verify [--date 2026-08-05]   # 验证某日预测（默认验证最近未验证的）
  python3 wm_forecast.py stats                        # 累计命中率统计
  python3 wm_forecast.py prices                       # 拉当前行情快照（黄金/电信A/H/BOTZ）
预测记录: ~/.hermes/wm_forecasts.json（agent 用 write_file 写入）
"""
import json, os, ssl, sys, argparse, urllib.request
from datetime import datetime, timezone, timedelta

FC_FILE = os.path.expanduser("~/.hermes/wm_forecasts.json")
TZ = timezone(timedelta(hours=8))
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE
_HDRS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def get_json(url):
    req = urllib.request.Request(url, headers=_HDRS)
    with urllib.request.urlopen(req, timeout=25, context=_ctx) as r:
        return json.loads(r.read().decode())


def yahoo_price(symbol, target_date=None):
    """返回 (价格, 涨跌%, 时间戳) — Yahoo chart API。
    target_date='YYYY-MM-DD' 时返回该日收盘（用于验证历史预测）。"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1mo&interval=1d"
    d = get_json(url)
    res = d["chart"]["result"][0]
    meta = res["meta"]
    ts_list = res.get("timestamp", [])
    closes = res["indicators"]["quote"][0]["close"]
    pairs = [(datetime.fromtimestamp(t, TZ).strftime("%Y-%m-%d"), c) for t, c in zip(ts_list, closes) if c is not None]
    if target_date:
        # 定位目标日期（或之前最近一日）
        cand = [p for p in pairs if p[0] <= target_date]
        if not cand:
            raise ValueError(f"{symbol} no data before {target_date}")
        dt, price = cand[-1]
        idx = pairs.index((dt, price))
        prev = pairs[idx - 1][1] if idx >= 1 else price
        chg = (price / prev - 1) * 100 if prev else 0
        return price, chg, meta.get("regularMarketTime")
    price = meta.get("regularMarketPrice") or closes[-1]
    prev = closes[-2] if len(closes) >= 2 else price
    chg = (price / prev - 1) * 100 if prev else 0
    return price, chg, meta.get("regularMarketTime")


def bootstrap_price(symbol):
    """返回 (价格, 涨跌%, 时间戳) — WorldMonitor bootstrap"""
    d = get_json("https://api.worldmonitor.app/api/bootstrap?tier=fast&public=1")
    d = d.get("data", d)
    for block in ("marketQuotes", "commodityQuotes"):
        for q in d.get(block, {}).get("quotes", []):
            if q.get("symbol") == symbol:
                return q.get("price"), q.get("change", 0), None
    raise KeyError(f"{symbol} not in bootstrap")


def resolve_price(symbol, source, target_date=None):
    # 优先雅虎历史收盘（更准，支持历史日期）；bootstrap 只有实时价，验证会漂移
    if source == "bootstrap":
        try:
            p, chg, ts = yahoo_price(symbol, target_date)  # GC=F 等在雅虎也有
            return p, chg, datetime.fromtimestamp(ts, TZ).strftime("%m-%d %H:%M") if ts else "?"
        except Exception:
            p, chg, ts = bootstrap_price(symbol)
            return p, chg, "?"
    elif source == "yahoo":
        p, chg, ts = yahoo_price(symbol, target_date)
        return p, chg, datetime.fromtimestamp(ts, TZ).strftime("%m-%d %H:%M") if ts else "?"
    else:
        raise ValueError(f"unknown source {source}")


def load_fc():
    if os.path.exists(FC_FILE):
        return json.load(open(FC_FILE))
    return {}


def verify(args):
    fc = load_fc()
    target_date = args.date or max(fc.keys())
    if target_date not in fc:
        print(f"❌ {target_date} 无预测记录")
        return 1
    items = fc[target_date]
    print(f"=== 验证 {target_date} 的预测 ===")
    all_ok = []
    for name, it in items.items():
        if it.get("verified"):
            print(f"  ⏭️  {name}: 已验证过（实际 {it.get('actual')}）")
            continue
        try:
            price, chg, ts = resolve_price(it["symbol"], it["source"], target_date)
        except Exception as e:
            print(f"  ⚠️  {name}: 拉取失败 {e}")
            continue
        low, high = it.get("low"), it.get("high")
        dirn = it.get("direction")
        in_range = (low is None or price >= low) and (high is None or price <= high)
        dir_ok = (dirn == "up" and chg > 0) or (dirn == "down" and chg < 0) or (dirn == "flat" and abs(chg) < 1.0)
        mark = "✅ 命中" if in_range else "❌ 未命中"
        dir_mark = f"方向{'✅' if dir_ok else '❌'}({chg:+.2f}%)"
        print(f"  {mark} {name}: 预测[{low}~{high} {dirn}] 实际 {price:.2f} ({ts}) {dir_mark}")
        it["actual"] = round(price, 3)
        it["actual_change"] = round(chg, 2)
        it["range_hit"] = in_range
        it["dir_hit"] = dir_ok
        it["verified_at"] = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
        it["verified"] = True
        all_ok.append(in_range)
    json.dump(fc, open(FC_FILE, "w"), ensure_ascii=False, indent=2)
    if all_ok:
        print(f"\n本次区间命中率: {sum(all_ok)}/{len(all_ok)}")
    return 0


def stats(args):
    fc = load_fc()
    total = range_hit = dir_hit = 0
    for d, items in fc.items():
        for name, it in items.items():
            if it.get("verified"):
                total += 1
                range_hit += 1 if it.get("range_hit") else 0
                dir_hit += 1 if it.get("dir_hit") else 0
    print("=== 累计统计 ===")
    print(f"已验证预测: {total} 条")
    if total:
        print(f"区间命中率: {range_hit}/{total} = {range_hit/total*100:.0f}%")
        print(f"方向命中率: {dir_hit}/{total} = {dir_hit/total*100:.0f}%")
    pending = sum(1 for d, items in fc.items() for it in items.values() if not it.get("verified"))
    print(f"待验证: {pending} 条")
    return 0


def prices(args):
    targets = [("黄金 GC=F", "GC=F", "bootstrap"), ("中国电信A 601728", "601728.SS", "yahoo"),
               ("中国电信H 0728", "0728.HK", "yahoo"), ("机器人 BOTZ", "BOTZ", "yahoo")]
    print(f"=== 行情快照 {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')} ===")
    for name, sym, src in targets:
        try:
            p, chg, ts = resolve_price(sym, src)
            arrow = "▲" if chg >= 0 else "▼"
            print(f"  {name:16s} {p:>10.2f} {arrow}{abs(chg):>6.2f}% ({ts})")
        except Exception as e:
            print(f"  {name:16s} 拉取失败: {e}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    v = sub.add_parser("verify")
    v.add_argument("--date", default=None)
    v.set_defaults(fn=verify)
    s = sub.add_parser("stats")
    s.set_defaults(fn=stats)
    p = sub.add_parser("prices")
    p.set_defaults(fn=prices)
    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return 1
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
