#!/usr/bin/env python3
"""
CSV audit regression test runner.
Usage: python3 run_csv_regression.py <csv_path> [n_items]

Parses CSV with multi-line handling, calls agents-platform /runs/wait,
compares fast/human/skill results, writes report.
"""
import json, re, sys, time, urllib.request

BASE_URL = "http://localhost:30030/agents-platform/api"
AGENT_ID = "341aa4fd-c0ae-4c89-b469-650e0c127b1d"
GRAPH_ID = "agents-platform"

COL_PGID = 0; COL_GOODS_NAME = 20; COL_AUDIT_REQ = 31
COL_AI_RESULT = 32; COL_AI_REASON = 34
COL_HUMAN_RESULT = 38; COL_HUMAN_REASON = 37
COL_SCENARIO = 39; COL_FIDELITY = 40; COL_DATA_CHANGED = 41


def read_tsv(path, n=10):
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()
    merged = []; buf = ""
    for line in raw.split('\n'):
        clean = line.rstrip('\r')
        ft = clean.find('\t')
        if ft > 10 and clean[:ft].isdigit() and len(clean[:ft]) >= 15:
            if buf: merged.append(buf); buf = clean
        else:
            if buf: buf += "\n" + clean
            elif clean.strip(): buf = clean
    if buf: merged.append(buf)
    rows = []
    for line in merged:
        cols = line.split('\t')
        if len(cols) >= 38:
            rows.append(cols)
        if len(rows) >= n: break
    return rows


def fix_json(s):
    try: return json.loads(s)
    except:
        fixed = s.replace('\\\\"', '\\\\\\"')
        try: return json.loads(fixed)
        except: return json.loads(re.sub(r'(?<=.)\\"(?=[^,\}\]])', '\\\\\\"', fixed))


def normalize(v):
    return "1" if str(v).strip() in ('2', '1') else "0"


def call_api(audit_json_str, timeout=10):
    rd = fix_json(audit_json_str)
    prompt = json.dumps(rd, ensure_ascii=False)
    body = json.dumps({"assistant_id": GRAPH_ID,
        "input": {"messages": [{"role": "user",
            "content": "请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，返回JSON：\n" + prompt}]},
        "config": {"configurable": {"agent_id": AGENT_ID, "recursion_limit": 100}},
        "metadata": {"agent_id": AGENT_ID, "graph_id": GRAPH_ID}}).encode('utf-8')

    start = time.time()
    try:
        req = urllib.request.Request(f"{BASE_URL}/runs/wait", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
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


def gold(sc, ai, hu):
    if sc in ('SCENARIO_2_AI_REJECT_HUMAN_PASS', 'SCENARIO_1_AI_PASS_HUMAN_REJECT'):
        return normalize(hu), "human"
    return normalize(ai), "both" if sc in ('CONSISTENT_PASS','SCENARIO_3_BOTH_REJECT') else "ai"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/mnt/d/项目/gitlib/智能审核/doc/线上数据/061501.csv"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    print(f"Reading {path} ({n} items)...", flush=True)
    raw = read_tsv(path, n)

    results = []
    for idx, r in enumerate(raw):
        gs = lambda i, d='': r[i].strip() if i < len(r) else d
        sc = gs(COL_SCENARIO)
        ai_code = gs(COL_AI_RESULT); hu_code = gs(COL_HUMAN_RESULT)
        gld, gsrc = gold(sc, ai_code, hu_code)
        fast = normalize(ai_code); human = normalize(hu_code)

        print(f"[{idx+1}/{len(raw)}] {gs(COL_PGID)} sc={sc} fast={fast} human={human}", flush=True)
        api = call_api(gs(COL_AUDIT_REQ))
        skill = api.get('result', 'ERR')
        match = "1" if api['ok'] and skill == human else "0"
        sym = "✓" if match == "1" else "✗"
        print(f"  skill={skill} {sym} ({api.get('elapsed',0):.1f}s)", flush=True)

        results.append({'idx': idx+1, 'pid': gs(COL_PGID), 'name': gs(COL_GOODS_NAME)[:50],
            'sc': sc, 'fid': gs(COL_FIDELITY), 'fast': fast, 'human': human,
            'skill': skill, 'match': match, 'elapsed': api.get('elapsed',0)})

    matched = sum(1 for r in results if r['match'] == '1')
    print(f"\n=== DONE: {len(results)} items, {matched} matched ({round(matched/len(results)*100,1)}%) ===", flush=True)
    for r in results:
        sym = "✓" if r['match'] == '1' else "✗"
        print(f"  [{r['idx']}] {r['name'][:40]} fast={r['fast']} human={r['human']} skill={r['skill']} {sym}", flush=True)

if __name__ == '__main__':
    main()
