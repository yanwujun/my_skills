#!/usr/bin/env python3
"""
Stateless re-test of remaining mismatched items (skipping already-tested + the stuck 会议桌 item).
Uses stateless /runs/wait (accurate, no threaded false negatives).
"""
import json, os, re, html, subprocess, sys, time
from urllib.parse import urlparse, parse_qs, unquote

BASE_URL = "http://192.168.2.166:30030/agents-platform/api"
AGENT_ID = "6000bb28-36cc-426c-a676-3f1b7708d187"
GRAPH_ID = "agents-platform"
IMG_BASE = "https://www.ccgp-chongqing.gov.cn/djc-gateway/files"
IMG_BUSINESS = "kjxyfile50m"

# Already tested (from run1+run2): these have results, skip them
DONE = {
    ("不间断电源（UPS）", "中航泰克"),
    ("轿车", "长安"),
    ("小型客车（含MPV）", "长安"),
    ("A3黑白打印机", "夏普（SHARP）"),
    ("轿车", "阿维塔"),
    ("小型客车（含MPV）", "北京汽车"),
    ("沙发", "宝地文亿"),
    ("桌前椅", "宝地文亿"),
    ("桌前椅", "辰凡佳"),
}

# Stuck item: 会议桌/渝新晟 has huge payload, skip
SKIP = {("会议桌", "渝新晟")}

# Remaining targets from the original 44 mismatches
TARGETS = [
    ("沙发", "科泰"),
    ("办公桌", "楷迪瑞达"),
    ("会议椅", "辰凡佳"),
    ("折叠椅", "百川"),
    ("茶几", "百川"),
    ("折叠椅", "思迈迪"),
    ("屏风工位", "忠信诚"),
    ("便携式计算机", "联硕弘道"),
    ("多功能一体机", "方正（Founder）"),
    ("A4彩色打印机", "佳能（Canon）"),
    ("扫描仪", "成者（CZUR)"),
    ("碎纸机", "得力（deli）"),
    ("A3黑白打印机", "方正（Founder）"),
    ("碎纸机", "奥士达（OASTAR）"),
    ("碎纸机", "震旦（AURORA）"),
    ("便携式计算机", "海尔（Haier）"),
    ("多功能一体机", "中盈"),
    ("硒鼓", "利盟（Lexmark）"),
    ("硒鼓碳粉", "立思辰（LANXUM）"),
    ("色带", "DPK"),
    ("硒鼓碳粉", "利盟（Lexmark）"),
    ("色带", "中盈"),
    ("复印纸", "本刻"),
    ("复印纸", "甄白（红）"),
    ("空调机", "唛哒"),
    ("投影仪", "夏单"),
    ("投影幕", "普丽玛"),
    ("投影幕", "万鑫达"),
    ("投影幕", "万事鑫"),
]

def make_img_url(path):
    if not path: return path
    path = path.strip().strip('"').strip("'")
    if path.startswith('http'): return path
    fname = path.split('/')[-1] if '/' in path else path
    return f"{IMG_BASE}?filePath={path}&business={IMG_BUSINESS}&fileName={fname}"

def norm(v):
    v = str(v).strip()
    if v in ('-1','0','退回','审核不通过','不通过','智能审核退回','否','FAIL','fail','reject','False'): return "0"
    if v in ('2','1','通过','审核通过','PASS','pass','True','true'): return "1"
    return v

def extract_detail_image_urls(html_text):
    if not html_text or not str(html_text).strip(): return []
    urls = []
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', str(html_text), re.I):
        src = m.group(1)
        if 'filePath=' in src:
            q = urlparse(src).query
            fp = parse_qs(q).get('filePath', [None])[0]
            if fp: src = unquote(fp)
        urls.append(src)
    return urls

def curl_post(url, data, timeout=180):
    tmp = f"/tmp/audit_{int(time.time()*1000000)}_{os.getpid()}.json"
    cmd = ["curl", "-s", "-X", "POST", url, "-H", "Content-Type: application/json",
           "-d", data, "--max-time", str(timeout), "-o", tmp, "-w", "%{http_code}"]
    start = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
    elapsed = round(time.time()-start, 2)
    if r.returncode == 28: return None, elapsed, "timeout"
    if not os.path.exists(tmp) or os.path.getsize(tmp) == 0: return None, elapsed, "empty"
    with open(tmp, encoding='utf-8') as f: c = f.read()
    try: os.remove(tmp)
    except: pass
    return c, elapsed, r.stdout.strip()

def parse_response(resp_json):
    msgs = resp_json.get("messages", [])
    c = ""
    for m in reversed(msgs):
        if m.get("type") == "ai" and not m.get("tool_calls"):
            raw = m.get("content", "")
            if isinstance(raw, list):
                raw = "\n".join(b.get("text", "") for b in raw if isinstance(b, dict))
            c = raw
            break
    clean = c
    if "```json" in clean:
        clean = clean.split("```json")[1].split("```")[0].strip()
    elif "```" in clean:
        ps = [p for i,p in enumerate(clean.split("```")) if i%2==1]
        if ps: clean = max(ps, key=len).strip()
    try:
        pred = norm(str(json.loads(clean).get("auditResult", "?")))
        reason = json.loads(clean).get("auditReason", "")[:200]
    except:
        pred = "0" if ('不通过' in c[:200]) else "1" if ('通过' in c[:200]) else "parse_err"
        reason = c[:200]
    return pred, reason

def parse_cells(row_xml):
    return [html.unescape(d) for d in re.findall(r'<Data[^>]*>(.*?)</Data>', row_xml, re.DOTALL)]


def stream_parse(xml_path, targets, skip_set):
    with open(xml_path, encoding='utf-8') as f:
        header_map = None
        buffer = []
        in_row = False
        in_table = False
        row_count = 0
        match_count = 0
        seen_pairs = set()

        for line in f:
            if '<ss:Table>' in line:
                in_table = True
                continue
            if '</ss:Table>' in line:
                in_table = False
                break
            if not in_table:
                continue

            if '<ss:Row>' in line:
                in_row = True
                buffer = [line]
            elif '</ss:Row>' in line and in_row:
                buffer.append(line)
                row_text = ''.join(buffer)
                in_row = False
                row_count += 1

                cells = parse_cells(row_text)
                if not cells or len(cells) < 32:
                    continue

                if header_map is None:
                    header_map = {cells[i]: i for i in range(len(cells))}
                    continue

                def g(field):
                    i = header_map.get(field, -1)
                    return cells[i].strip() if 0 <= i < len(cells) else ''

                cat = g('base_catalog')
                brand = g('base_brand')
                fidelity = g('data_label_fidelity')

                if fidelity != 'HIGH':
                    continue

                key = (cat, brand)
                if key in skip_set:
                    continue
                if key in seen_pairs:
                    continue

                if key in targets:
                    seen_pairs.add(key)
                    match_count += 1
                    audit_json = g('audit_request_json')
                    if len(audit_json) < 10:
                        continue
                    yield {
                        'cat': cat, 'brand': brand,
                        'model': g('base_model'),
                        'fast': g('ai_audit_result_code'),
                        'human': g('human_audit_result'),
                        'ai_reason': g('ai_audit_reason'),
                        'audit_request_json': audit_json,
                    }
                    print(f"  Found [{match_count}]: {cat} / {brand}", flush=True)
            elif in_row:
                buffer.append(line)

        print(f"Scanned {row_count} rows, found {match_count} matching items\n", flush=True)


def main():
    xml_path = "/mnt/d/项目/gitlib/智能审核/doc/线上数据/061601.xml"
    if not os.path.exists(xml_path):
        print(f"XML not found: {xml_path}")
        sys.exit(1)

    target_set = set(TARGETS)
    skip_set = DONE | SKIP
    print(f"Targets: {len(target_set)}, Skip: {len(skip_set)}", flush=True)
    print("Streaming XML...", flush=True)
    items = list(stream_parse(xml_path, target_set, skip_set))
    print(f"Collected {len(items)} items for testing\n", flush=True)

    if not items:
        print("No matching items found!")
        sys.exit(1)

    print("=" * 85)
    print(f"  {'Catalog':<26} {'Brand':<22} {'人工':>4} {'fast':>4} {'skill':>6} {'Match':>6} {'Time':>6}")
    print("-" * 85)

    results = []
    matched = 0
    mismatched = 0

    for idx_i, item in enumerate(items):
        cat = item['cat']
        brand = item['brand']
        fast = norm(item['fast'])
        human = norm(item['human'])
        ai_reason = item['ai_reason'][:100]

        rd = json.loads(item['audit_request_json'])
        imgs = [make_img_url(u) for u in (rd.get('imageUrls') or []) if u]
        gdh = rd.get('goodsDetailHtml', '')
        detail_raw = extract_detail_image_urls(gdh) if gdh else []
        detail_imgs = [make_img_url(u) for u in detail_raw if u]
        if detail_imgs:
            rd['detailImageUrls'] = detail_raw

        content_parts = [{"type": "text", "text": "请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，严格按 Skill 输出格式返回 JSON（含 auditResult、auditReason）：\n" + json.dumps(rd, ensure_ascii=False)}]
        for u in imgs:
            content_parts.append({"type": "image_url", "image_url": {"url": u}})
        for u in detail_imgs:
            content_parts.append({"type": "image_url", "image_url": {"url": u}})

        # STATELESS mode — accurate, no false negatives
        body = json.dumps({
            "assistant_id": GRAPH_ID,
            "input": {"messages": [{"role": "user", "content": content_parts}]},
            "config": {"configurable": {"agent_id": AGENT_ID, "recursion_limit": 100}},
            "metadata": {"agent_id": AGENT_ID, "graph_id": GRAPH_ID}
        }, ensure_ascii=False)

        resp, elapsed, http_code = curl_post(f"{BASE_URL}/runs/wait", body, 180)

        if not resp:
            pred = "T/O" if "timeout" in http_code else f"ERR({http_code})"
            reason = ""
        else:
            rj = json.loads(resp)
            pred, reason = parse_response(rj)

        is_match = pred == human
        if is_match: matched += 1
        else: mismatched += 1
        mark = "✅" if is_match else "❌"
        img_info = f"图{len(imgs)}+{len(detail_imgs)}"

        print(f"  {cat:<26} {brand:<22} {human:>4} {fast:>4} {pred:>6} {mark:>6} {elapsed:>5}s  {img_info}", flush=True)
        if not is_match and pred not in ("T/O", "parse_err", "ERR(empty)"):
            print(f"        skill原因: {reason[:150]}", flush=True)

        results.append({
            "cat": cat, "brand": brand, "model": item['model'],
            "fast": fast, "human": human, "pred": pred,
            "elapsed": elapsed, "match": is_match,
            "ai_reason": ai_reason, "skill_reason": reason,
        })

    total = len(results)
    print(f"\n{'='*85}", flush=True)
    print(f"STATELESS RESULTS: {total} items", flush=True)
    print(f"  Matched:   {matched} ({round(matched/total*100,1) if total else 0}%)", flush=True)
    print(f"  Mismatched: {mismatched} ({round(mismatched/total*100,1) if total else 0}%)", flush=True)

    cat_stats = {}
    for r in results:
        c = r['cat']
        if c not in cat_stats: cat_stats[c] = [0, 0]
        cat_stats[c][0] += 1
        if r['match']: cat_stats[c][1] += 1

    print(f"\n{'Catalog':<30} {'Items':>5} {'Match':>5} {'Rate':>7}", flush=True)
    print("-" * 50, flush=True)
    for cat in sorted(cat_stats):
        items_n, m = cat_stats[cat]
        rate = round(m/items_n*100, 1) if items_n > 0 else 0
        print(f"{cat:<30} {items_n:>5} {m:>5} {rate:>6}%", flush=True)

    # Mismatch detail
    if mismatched:
        print(f"\n--- Mismatched items ---", flush=True)
        for r in results:
            if not r['match']:
                print(f"  ❌ {r['cat']:<26} {r['brand']:<22} pred={r['pred']} human={r['human']}", flush=True)
                if r.get('skill_reason'):
                    print(f"     reason: {r['skill_reason'][:200]}", flush=True)

    out = f"/tmp/stateless_retest_{int(time.time())}.json"
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({"run_at": int(time.time()), "mode": "stateless", "agent": AGENT_ID,
                     "total": total, "matched": matched, "results": results}, f, ensure_ascii=False)
    print(f"\nResults saved to {out}", flush=True)


if __name__ == "__main__":
    main()
