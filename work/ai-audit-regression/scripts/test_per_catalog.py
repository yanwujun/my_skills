#!/usr/bin/env python3
"""
Per-catalog regression: 3 SCENARIO_2 + 3 CONSISTENT_PASS per catalog.
Stateless mode, then threaded re-run for mismatches.
"""
import json, os, re, html, subprocess, sys, time
from urllib.parse import urlparse, parse_qs, unquote

BASE_URL = "http://192.168.2.166:30030/agents-platform/api"
AGENT_ID = "6000bb28-36cc-426c-a676-3f1b7708d187"
GRAPH_ID = "agents-platform"
IMG_BASE = "https://www.ccgp-chongqing.gov.cn/djc-gateway/files"
IMG_BUSINESS = "kjxyfile50m"
WEB_UI = "http://192.168.2.166:5175"
PER_SCENARIO = 3

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
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+10)
        elapsed = round(time.time()-start, 2)
        if r.returncode == 28: return None, elapsed, "timeout"
        if not os.path.exists(tmp) or os.path.getsize(tmp) == 0: return None, elapsed, "empty"
        with open(tmp, encoding='utf-8') as f: c = f.read()
        try: os.remove(tmp)
        except: pass
        return c, elapsed, r.stdout.strip()
    except subprocess.TimeoutExpired:
        elapsed = round(time.time()-start, 2)
        return None, elapsed, "timeout"

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
        reason = json.loads(clean).get("auditReason", "")[:300]
    except:
        pred = "0" if ('不通过' in c[:200]) else "1" if ('通过' in c[:200]) else "parse_err"
        reason = c[:300]
    return pred, reason

def parse_cells(row_xml):
    return [html.unescape(d) for d in re.findall(r'<Data[^>]*>(.*?)</Data>', row_xml, re.DOTALL)]


def stream_parse(xml_path):
    """Parse XML using working regex approach (reads full file)."""
    with open(xml_path, encoding='utf-8') as f:
        xc = f.read()
    ws = xc.find('<ss:Table>')
    we = xc.find('</ss:Table>', ws)
    if we == -1: we = len(xc)
    rows = re.findall(r'<ss:Row>(.*?)</ss:Row>', xc[ws:we+11], re.DOTALL)
    
    def cells(xml):
        return [html.unescape(d) for d in re.findall(r'<Data[^>]*>(.*?)</Data>', xml, re.DOTALL)]
    
    if not rows: return
    hdr = cells(rows[0])
    header_map = {hdr[i]: i for i in range(len(hdr))}
    
    for row_xml in rows[1:]:
        r = cells(row_xml)
        if not r or len(r) < 32: continue
        
        def g(field):
            i = header_map.get(field, -1)
            return r[i].strip() if 0 <= i < len(r) else ''
        
        cat = g('base_catalog')
        scenario = g('training_scenario')
        aj = g('audit_request_json')
        if not cat or not scenario or len(aj) < 10:
            continue
        
        yield {
            'cat': cat, 'scenario': scenario,
            'fidelity': g('data_label_fidelity'),
            'brand': g('base_brand'), 'model': g('base_model'),
            'fast': g('ai_audit_result_code'), 'human': g('human_audit_result'),
            'ai_reason': g('ai_audit_reason'), 'human_reason': g('human_audit_reason'),
            'audit_request_json': aj,
        }
def select_items(all_rows):
    """Select PER_SCENARIO items per catalog per scenario, brand-dedup."""
    # Group by (catalog, scenario)
    groups = {}
    for r in all_rows:
        key = (r['cat'], r['scenario'])
        if key not in groups: groups[key] = []
        groups[key].append(r)
    
    selected = []
    for (cat, scenario), rows in sorted(groups.items()):
        # Prefer HIGH fidelity
        high = [r for r in rows if r['fidelity'] == 'HIGH']
        pool = high if high else rows
        # Brand dedup
        seen = set()
        picked = []
        for r in pool:
            if len(picked) >= PER_SCENARIO: break
            if r['brand'] not in seen:
                picked.append(r); seen.add(r['brand'])
        for r in pool:
            if len(picked) >= PER_SCENARIO: break
            if r not in picked: picked.append(r)
        selected.extend(picked[:PER_SCENARIO])
    return selected


def test_one(item, mode="stateless"):
    """Test one item. mode: 'stateless' or 'threaded'. Returns (pred, reason, elapsed, tid)."""
    rd = json.loads(item['audit_request_json'])
    imgs = [make_img_url(u) for u in (rd.get('imageUrls') or []) if u]
    gdh = rd.get('goodsDetailHtml', '')
    detail_raw = extract_detail_image_urls(gdh) if gdh else []
    detail_imgs = [make_img_url(u) for u in detail_raw if u]
    if detail_imgs: rd['detailImageUrls'] = detail_raw

    content_parts = [{"type":"text","text":"请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，严格按 Skill 输出格式返回 JSON（含 auditResult、auditReason）：\n"+json.dumps(rd,ensure_ascii=False)}]
    for u in imgs: content_parts.append({"type":"image_url","image_url":{"url":u}})
    for u in detail_imgs: content_parts.append({"type":"image_url","image_url":{"url":u}})

    body = json.dumps({
        "assistant_id": GRAPH_ID,
        "input": {"messages": [{"role":"user","content":content_parts}]},
        "config": {"configurable":{"agent_id":AGENT_ID,"recursion_limit":100}},
        "metadata": {"agent_id":AGENT_ID,"graph_id":GRAPH_ID}
    }, ensure_ascii=False)

    tid = ""
    if mode == "threaded":
        meta = json.dumps({"assistant_id":GRAPH_ID,"metadata":{"agent_id":AGENT_ID,"agent_name":"kjxy-goods-audit","owner":"dev-user","user_name":"Dev User","graph_id":GRAPH_ID,"tag":f"percat-{item['cat']}"}})
        tresp, _, _ = curl_post(f"{BASE_URL}/threads", meta, 10)
        if tresp:
            try: tid = json.loads(tresp).get("thread_id","")
            except: pass
        if not tid: return "ERR(no_thread)", "", 0, ""
        url = f"{BASE_URL}/threads/{tid}/runs/wait"
    else:
        url = f"{BASE_URL}/runs/wait"

    resp, elapsed, http_code = curl_post(url, body, 180)

    if not resp:
        return ("T/O" if "timeout" in http_code else f"ERR({http_code})"), "", elapsed, tid
    rj = json.loads(resp)
    pred, reason = parse_response(rj)
    return pred, reason, elapsed, tid


def main():
    xml_path = "/mnt/d/项目/gitlib/智能审核/doc/线上数据/061601.xml"
    if not os.path.exists(xml_path):
        print(f"XML not found: {xml_path}"); sys.exit(1)

    print("Streaming XML...", flush=True)
    all_rows = list(stream_parse(xml_path))
    print(f"Total rows: {len(all_rows)}", flush=True)

    items = select_items(all_rows)
    print(f"Selected {len(items)} items from {len(set(i['cat'] for i in items))} catalogs\n", flush=True)

    # Show distribution
    from collections import Counter
    sc = Counter(i['scenario'] for i in items)
    for k, v in sc.most_common():
        print(f"  {k}: {v}", flush=True)
    print()

    # Phase 1: Stateless
    print("=" * 80)
    print("PHASE 1: Stateless mode")
    print(f"{'#':>4} {'Catalog':<24} {'Scenario':<30} {'Brand':<18} {'人':>3} {'f':>2} {'sk':>5} {'M':>3} {'Time':>5}")
    print("-" * 80)

    results = []
    matched = 0
    mismatched = 0

    for idx_i, item in enumerate(items):
        pred, reason, elapsed, _ = test_one(item, "stateless")
        human = norm(item['human'])
        fast = norm(item['fast'])
        is_match = pred == human
        if is_match: matched += 1
        else: mismatched += 1
        mark = "✅" if is_match else "❌"
        sc_short = item['scenario'].replace('SCENARIO_2_AI_REJECT_HUMAN_PASS','S2_AI拒人过').replace('CONSISTENT_PASS','一致通过').replace('SCENARIO_3_BOTH_REJECT','S3_双拒')

        print(f"{idx_i+1:>4} {item['cat']:<24} {sc_short:<30} {item['brand']:<18} {human:>3} {fast:>2} {pred:>5} {mark:>3} {elapsed:>5}s", flush=True)
        if not is_match and pred not in ("T/O","parse_err"):
            print(f"       reason: {reason[:120]}", flush=True)

        results.append({**item, 'pred':pred, 'reason':reason, 'elapsed':elapsed,
                        'match':is_match, 'tid':'', 'mode':'stateless'})

    print(f"\nPhase 1 done: {matched}/{len(results)} matched ({round(matched/len(results)*100,1)}%)", flush=True)

    # Phase 2: Threaded re-run for mismatched items
    mismatched_items = [r for r in results if not r['match']]
    if mismatched_items:
        print(f"\n{'='*80}")
        print(f"PHASE 2: Threaded re-run for {len(mismatched_items)} mismatched items (for session links)")
        for idx_i, r in enumerate(mismatched_items):
            pred, reason, elapsed, tid = test_one(r, "threaded")
            r['pred'] = pred; r['reason'] = reason; r['elapsed'] = elapsed; r['tid'] = tid; r['mode'] = 'threaded'
            human = norm(r['human']); fast = norm(r['fast'])
            is_match = pred == human
            mark = "✅" if is_match else "❌"
            sc_short = r['scenario'].replace('SCENARIO_2_AI_REJECT_HUMAN_PASS','S2').replace('CONSISTENT_PASS','CP')
            print(f"  [{idx_i+1}/{len(mismatched_items)}] {r['cat']:<24} {r['brand']:<18} pred={pred} human={human} {mark} {elapsed}s  tid={tid}", flush=True)
            if not is_match and pred not in ("T/O","parse_err"):
                print(f"       reason: {reason[:120]}", flush=True)
            if not is_match:
                print(f"       Web UI: {WEB_UI}/?thread_id={tid}", flush=True)

    # Generate report
    print(f"\n{'='*80}")
    print("Generating report...", flush=True)

    # Per-catalog stats
    cat_stats = {}
    for r in results:
        c = r['cat']
        if c not in cat_stats: cat_stats[c] = {'total':0,'match':0,'s2_total':0,'s2_match':0,'cp_total':0,'cp_match':0}
        cs = cat_stats[c]; cs['total'] += 1
        if r['match']: cs['match'] += 1
        if 'SCENARIO_2' in r['scenario']:
            cs['s2_total'] += 1
            if r['match']: cs['s2_match'] += 1
        elif 'CONSISTENT' in r['scenario']:
            cs['cp_total'] += 1
            if r['match']: cs['cp_match'] += 1

    # Write report
    report_path = "/mnt/d/项目/gitlib/智能审核/doc/测试报告_goods-audit-eight_每目录6条.md"
    lines = []
    lines.append("# AI 审核 Skill 测试报告（goods-audit-eight · 每目录6条）")
    lines.append("")
    lines.append(f"- **测试日期**：2026-06-26")
    lines.append(f"- **Skill**：goods-audit-eight")
    lines.append(f"- **Agent ID**：{AGENT_ID}")
    lines.append(f"- **样本**：{len(set(i['cat'] for i in items))}目录 × ({PER_SCENARIO} SCENARIO_2 + {PER_SCENARIO} CONSISTENT_PASS) = {len(items)}条")
    lines.append(f"- **方式**：stateless 批量 + threaded 补会话链接")
    lines.append("")
    lines.append("## 一、汇总")
    lines.append("")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 总样本 | {len(results)} |")
    lines.append(f"| 一致 ✅ | {matched} |")
    lines.append(f"| 不一致 ❌ | {mismatched} |")
    lines.append(f"| **一致率** | **{round(matched/len(results)*100,1)}%** |")
    lines.append("")
    lines.append("## 二、逐目录一致率")
    lines.append("")
    lines.append(f"| 目录 | 总计 | 一致 | 一致率 | S2一致 | CP一致 |")
    lines.append(f"|------|:---:|:---:|:-----:|:---:|:---:|")
    for cat in sorted(cat_stats):
        cs = cat_stats[cat]
        rate = round(cs['match']/cs['total']*100,1)
        s2r = round(cs['s2_match']/cs['s2_total']*100,1) if cs['s2_total'] else '-'
        cpr = round(cs['cp_match']/cs['cp_total']*100,1) if cs['cp_total'] else '-'
        lines.append(f"| {cat} | {cs['total']} | {cs['match']} | {rate}% | {s2r}% | {cpr}% |")
    lines.append("")

    # Mismatch detail
    mism = [r for r in results if not r['match']]
    if mism:
        lines.append("## 三、不一致项明细")
        lines.append("")
        lines.append(f"| # | 目录 | 场景 | 品牌 | 人工 | fast | skill | 耗时 | 会话 | skill原因 |")
        lines.append(f"|---|------|------|------|:---:|:---:|:---:|-----:|------|------|")
        for i, r in enumerate(mism):
            sc_short = 'S2' if 'SCENARIO_2' in r['scenario'] else 'CP' if 'CONSISTENT' in r['scenario'] else r['scenario'][:8]
            human = norm(r['human']); fast = norm(r['fast']); pred = r.get('pred','?')
            tid = r.get('tid','')
            link = f"[查看]({WEB_UI}/?thread_id={tid})" if tid else "-"
            reason = (r.get('reason','') or '')[:80]
            lines.append(f"| {i+1} | {r['cat']} | {sc_short} | {r['brand']} | {human} | {fast} | {pred} | {r.get('elapsed','')}s | {link} | {reason} |")
        lines.append("")

    lines.append("## 四、不一致分析")
    lines.append("")
    lines.append(f"共 {len(mism)} 条不一致，按场景分布：")
    s2_mism = sum(1 for r in mism if 'SCENARIO_2' in r['scenario'])
    cp_mism = sum(1 for r in mism if 'CONSISTENT' in r['scenario'])
    lines.append(f"- SCENARIO_2（AI拒人过）：{s2_mism} 条 — skill 仍退回但人工通过了")
    lines.append(f"- CONSISTENT_PASS（双过）：{cp_mism} 条 — skill 退回但原AI和人工都通过了")
    lines.append("")

    # Save
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Report saved to {report_path}", flush=True)

    # Also save JSON
    out = f"/tmp/percat_{int(time.time())}.json"
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({"run_at":int(time.time()),"agent":AGENT_ID,"total":len(results),"matched":matched,"results":results},f,ensure_ascii=False)
    print(f"JSON saved to {out}", flush=True)


if __name__ == "__main__":
    main()
