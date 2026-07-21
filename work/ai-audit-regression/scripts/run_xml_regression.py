#!/usr/bin/env python3
"""
XML audit regression test runner (Excel Spreadsheet ML format).
Usage: python3 run_xml_regression.py <xml_path> [max_catalogs] [--fast]\n\nParses XML with html.unescape for JSON fields, calls agents-platform /runs/wait,\ncompares fast/human/skill results per catalog.\nDefault timeout: 120s per item (thorough). Pass --fast for 10s timeout.
"""
import json, re, sys, time, urllib.request, html

BASE_URL = "http://localhost:30030/agents-platform/api"
AGENT_ID = "341aa4fd-c0ae-4c89-b469-650e0c127b1d"
GRAPH_ID = "agents-platform"
TIMEOUT = 120  # Default 120s for thorough testing; pass --fast for 10s
IMG_BASE = "https://www.ccgp-chongqing.gov.cn/djc-gateway/files"
IMG_BUSINESS = "kjxyfile50m"


def make_image_url(path):
    if not path: return path
    path = path.strip().strip('"').strip("'")
    if path.startswith('http'): return path
    fname = path.split('/')[-1] if '/' in path else path
    return f"{IMG_BASE}?filePath={path}&business={IMG_BUSINESS}&fileName={fname}"


def stream_xml(path):
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    ws = c.find('<ss:Table'); we = c.find('</ss:Table>', ws)
    return re.findall(r'<ss:Row>(.*?)</ss:Row>', c[ws:we+11], re.DOTALL)


def cell_data(xml):
    return [html.unescape(d) for d in re.findall(r'<Data[^>]*>(.*?)</Data>', xml, re.DOTALL)]


def parse_json(s):
    s = s.strip()
    if not s or s == '\\N': return None
    try: return json.loads(s)
    except:
        try: return json.loads(s.replace('\\\\"', '\\\\\\"'))
        except: return None


def normalize(v):
    return "1" if str(v).strip() in ('2', '1') else "0"


def call_api(req_data):
    prompt = json.dumps(req_data, ensure_ascii=False)
    body = json.dumps({"assistant_id": GRAPH_ID,
        "input": {"messages": [{"role": "user",
            "content": "请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，返回JSON：\n" + prompt}]},
        "config": {"configurable": {"agent_id": AGENT_ID, "recursion_limit": 100}},
        "metadata": {"agent_id": AGENT_ID, "graph_id": GRAPH_ID}}).encode('utf-8')

    start = time.time()
    try:
        req = urllib.request.Request(f"{BASE_URL}/runs/wait", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            r = json.loads(resp.read().decode('utf-8'))
            msgs = r.get("messages", []); c = ""
            for m in reversed(msgs):
                if m.get("type") == "ai" and not m.get("tool_calls"):
                    c = m.get("content", ""); break
            if "```json" in c: c = c.split("```json")[1].split("```")[0].strip()
            elif "```" in c:
                cs = [p for i, p in enumerate(c.split("```")) if i % 2 == 1]
                if cs: c = max(cs, key=len).strip()
            try: pred = json.loads(c)
            except:
                ar = "0" if ('不通过' in c[:200] or 'auditResult: "0"' in c) else \
                      "1" if ('通过' in c[:200] or 'auditResult: "1"' in c) else "parse_err"
                pred = {"auditResult": ar}
            return {"ok": True, "elapsed": round(time.time() - start, 2),
                    "result": str(pred.get("auditResult", "")), "reason": pred.get("auditReason", c[:300])}
    except Exception as e:
        return {"ok": False, "elapsed": round(time.time() - start, 2), "error": str(e)[:80]}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/mnt/d/项目/gitlib/智能审核/doc/线上数据/061502.xml"
    max_cat = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    global TIMEOUT
    if '--fast' in sys.argv:
        TIMEOUT = 10

    rows = stream_xml(path)
    h = cell_data(rows[0]); hm = {h[i]: i for i in range(len(h))}
    def g(r, f):
        i = hm.get(f, -1)
        return r[i].strip() if i >= 0 and i < len(r) else ''

    data = [c for rx in rows[1:] if len(c := cell_data(rx)) >= 32 and g(c, 'audit_request_json').startswith('{')]
    print(f"Parsed {len(data)} valid rows", flush=True)

    grp = {}
    for r in data:
        grp.setdefault(g(r, 'base_catalog') or '未知', []).append(r)
    print(f"Catalogs: {len(grp)}", flush=True)

    for cat in sorted(grp.keys())[:max_cat]:
        items = grp[cat]
        items.sort(key=lambda r: 0 if g(r, 'data_label_fidelity') == 'HIGH' else 1)
        sel = []; seen = set()
        for it in items:
            br = g(it, 'base_brand')
            if br not in seen or len(sel) < 1:
                sel.append(it); seen.add(br)
            if len(sel) >= 2: break
        if len(sel) < 2: sel = items[:2]

        for s in sel:
            sc = g(s, 'training_scenario')
            ai_code = g(s, 'ai_audit_result_code'); hu_code = g(s, 'human_audit_result')
            gld = normalize(hu_code if sc in ('SCENARIO_2_AI_REJECT_HUMAN_PASS','SCENARIO_1_AI_PASS_HUMAN_REJECT') else ai_code)
            fast = normalize(ai_code); human = normalize(hu_code)
            brand = g(s, 'base_brand'); model = g(s, 'base_model')[:20]

            rd = parse_json(g(s, 'audit_request_json'))
            if rd is None:
                print(f"[{cat}] {brand} {model} — JSON fail", flush=True); continue

            # Construct full image URLs for Step5 LLM
            if 'imageUrls' in rd and rd['imageUrls']:
                rd['imageUrls'] = [make_image_url(u) for u in rd['imageUrls']]
            if 'detailImageUrls' in rd and rd['detailImageUrls']:
                rd['detailImageUrls'] = [make_image_url(u) for u in rd['detailImageUrls']]

            api = call_api(rd)
            skill = api.get('result', 'ERR'); match = '1' if api['ok'] and skill == human else '0'
            sym = '✓' if match == '1' else '✗'
            print(f"[{cat}] {brand} {model} fast={fast} human={human} skill={skill} {sym} ({api.get('elapsed',0):.1f}s)", flush=True)

if __name__ == '__main__':
    main()
