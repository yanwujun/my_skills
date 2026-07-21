#!/usr/bin/env python3
"""
Batch regression test runner for 框架协议商品智能审核.
Reads Excel XML data, creates per-item threads with metadata,
embeds images as image_url blocks in messages content,
calls /threads/{id}/runs/wait with curl for reliable timeout.
"""
import argparse, json, os, re, html, subprocess, sys, time

BASE_URL = "http://192.168.2.166:30030/agents-platform/api"
AGENT_ID = "6000bb28-36cc-426c-a676-3f1b7708d187"
GRAPH_ID = "agents-platform"
IMG_BASE = "https://www.ccgp-chongqing.gov.cn/djc-gateway/files"
IMG_BUSINESS = "kjxyfile50m"

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

from urllib.parse import urlparse, parse_qs, unquote

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

def curl_post(url, data, timeout=60):
    tmp = f"/tmp/audit_{int(time.time()*1000000)}_{os.getpid()}.json"
    cmd = ["curl", "-s", "-X", "POST", url, "-H", "Content-Type: application/json",
           "-d", data, "--max-time", str(timeout), "-o", tmp, "-w", "%{http_code}"]
    start = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+10)
        elapsed = round(time.time()-start, 2)
        if r.returncode == 28: return None, elapsed, "timeout"
        if not os.path.exists(tmp) or os.path.getsize(tmp) == 0: return None, elapsed, "empty"
        with open(tmp, encoding='utf-8') as f: c = f.read()
        try: os.remove(tmp)
        except: pass
        return c, elapsed, "ok"
    except subprocess.TimeoutExpired:
        elapsed = round(time.time()-start, 2)
        return None, elapsed, "timeout"

def parse_xml(path):
    with open(path, encoding='utf-8') as f: xc = f.read()
    ws = xc.find('<ss:Table>'); we = xc.find('</ss:Table>', ws)
    rows = re.findall(r'<ss:Row>(.*?)</ss:Row>', xc[ws:we+11], re.DOTALL)
    def cells(xml): return [html.unescape(d) for d in re.findall(r'<Data[^>]*>(.*?)</Data>', xml, re.DOTALL)]
    hdr = cells(rows[0]); hm = {hdr[i]: i for i in range(len(hdr))}
    def g(r, f): i = hm.get(f, -1); return r[i].strip() if i >= 0 and i < len(r) else ''
    data = [c for rx in rows[1:] if len(c:=cells(rx)) >= 32 and len(g(c, 'audit_request_json')) > 10]
    return data, g

def main():
    p = argparse.ArgumentParser()
    p.add_argument("xml_path"); p.add_argument("--catalogs", type=int, default=0)
    p.add_argument("--items", type=int, default=5); p.add_argument("--timeout", type=int, default=120)
    args = p.parse_args()
    data, g = parse_xml(args.xml_path)
    # Brand-dedup selection: one per distinct brand first, then fill remaining slots
    cats_all = {}
    for r in data:
        cat = g(r, 'base_catalog')
        if cat not in cats_all: cats_all[cat] = []
        if g(r, 'data_label_fidelity') == 'HIGH':
            cats_all[cat].append(r)
    cat_list = sorted(cats_all.keys())
    if args.catalogs > 0: cat_list = cat_list[:args.catalogs]
    cats = {}
    for cat in cat_list:
        items = cats_all.get(cat, [])
        selected = []; seen_brands = set()
        for r in items:
            if len(selected) >= args.items: break
            br = g(r, 'base_brand')
            if br not in seen_brands:
                selected.append(r); seen_brands.add(br)
        for r in items:
            if len(selected) >= args.items: break
            if r not in selected: selected.append(r)
        if selected: cats[cat] = selected[:args.items]
    catalogs = list(cats.keys())
    if not catalogs:
        print("No items found!")
        sys.exit(1)

    results = []; total_start = time.time()
    for ci, cat in enumerate(catalogs):
        for ii, r in enumerate(cats[cat]):
            brand = g(r, 'base_brand'); model = g(r, 'base_model')[:25]
            fast = norm(g(r, 'ai_audit_result_code')); human = norm(g(r, 'human_audit_result'))
            ai_reason = g(r, 'ai_audit_reason')[:120]; human_reason = g(r, 'human_audit_reason')[:100]

            meta = json.dumps({"assistant_id": GRAPH_ID, "metadata": {
                "agent_id": AGENT_ID, "agent_name": "kjxy-goods-audit",
                "graph_id": GRAPH_ID}})
            resp, _, _ = curl_post(f"{BASE_URL}/threads", meta, 10)
            if not resp: continue
            tid = json.loads(resp).get("thread_id", "")

            rd = json.loads(g(r, 'audit_request_json'))
            imgs = [make_img_url(u) for u in (rd.get('imageUrls') or []) if u]
            # 从 goodsDetailHtml 提取详情图
            gdh = rd.get('goodsDetailHtml', '')
            detail_raw = extract_detail_image_urls(gdh) if gdh else []
            detail_imgs = [make_img_url(u) for u in detail_raw if u]
            # 把详情图 URL 补进 request JSON 的 detailImageUrls 字段
            if detail_imgs:
                rd['detailImageUrls'] = detail_raw  # 原始相对路径
            content_parts = [{"type": "text", "text": "请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，严格按 Skill 输出格式返回 JSON（含 auditResult、auditReason）：\n" + json.dumps(rd, ensure_ascii=False)}]
            for u in imgs:
                content_parts.append({"type": "image_url", "image_url": {"url": u}})
            for u in detail_imgs:
                content_parts.append({"type": "image_url", "image_url": {"url": u}})
            body = json.dumps({"assistant_id": GRAPH_ID,
                "input": {"messages": [{"role": "user", "content": content_parts}]},
                "config": {"configurable": {"agent_id": AGENT_ID, "recursion_limit": 100}},
                "metadata": {"agent_id": AGENT_ID, "graph_id": GRAPH_ID}}, ensure_ascii=False)

            resp, elapsed, http = curl_post(f"{BASE_URL}/threads/{tid}/runs/wait", body, args.timeout)
            if not resp:
                results.append({"cat":cat,"brand":brand,"model":model,"fast":fast,"human":human,"pred":"T/O","tid":tid,"ai_reason":ai_reason})
                print(f"  [{ci+1}/{len(catalogs)}][{ii+1}] T/O {cat} {brand} {elapsed}s tid={tid}（图{len(imgs)}+{len(detail_imgs)}）")
                continue

            rj = json.loads(resp); msgs = rj.get("messages",[])
            c = ""
            for m in reversed(msgs):
                if m.get("type")=="ai" and not m.get("tool_calls"):
                    raw = m.get("content","")
                    if isinstance(raw, list): raw = "\n".join(b.get("text","") for b in raw if isinstance(b,dict))
                    c = raw; break
            clean = c
            if "```json" in clean: clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                ps = [p for i,p in enumerate(clean.split("```")) if i%2==1]
                if ps: clean = max(ps, key=len).strip()
            try: pred = norm(str(json.loads(clean).get("auditResult","?")))
            except: pred = "0" if ('不通过' in c[:200]) else "1" if ('通过' in c[:200]) else "parse_err"
            match = "✅" if pred == human else "❌"
            print(f"  [{ci+1}/{len(catalogs)}][{ii+1}] {cat} {brand} pred={pred} human={human} {match} {elapsed}s tid={tid}（图{len(imgs)}+{len(detail_imgs)}）")
            results.append({"cat":cat,"brand":brand,"model":model,"fast":fast,"human":human,"pred":pred,"elapsed":elapsed,"tid":tid,"ai_reason":ai_reason,"human_reason":human_reason})

    total = len(results)
    matched = sum(1 for r in results if r.get("pred")==r.get("human"))
    print(f"\n{'='*60}")
    print(f"Total: {total} items, {matched} matched ({round(matched/total*100,1)}%)\n")
    # Per-catalog breakdown
    cat_stats = {}
    for r in results:
        c = r['cat']; cat_stats.setdefault(c, [0,0])
        cat_stats[c][0] += 1
        if r.get('pred')==r.get('human'): cat_stats[c][1] += 1
    print(f"{'Catalog':<30} {'Items':>5} {'Match':>5} {'Rate':>7}")
    print("-"*50)
    for cat in sorted(cat_stats):
        items, m = cat_stats[cat]
        print(f"{cat:<30} {items:>5} {m:>5} {round(m/items*100,1):>6}%")
    # Save results
    out = f"/tmp/audit_results_{int(time.time())}.json"
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({"run_at": int(time.time()), "agent": AGENT_ID, "total": total, "matched": matched, "results": results}, f, ensure_ascii=False)
    print(f"\nResults saved to {out}")
    os.environ.setdefault('AUDIT_RESULTS_FILE', out)

if __name__ == "__main__":
    main()
