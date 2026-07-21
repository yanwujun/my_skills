# -*- coding: utf-8 -*-
"""Single-item audit test — runs from Windows when WSL can't reach 192.168.2.166.

Usage: python test_single_windows.py <json_path> [idx]

Reads the standardized test data JSON, picks one item, embeds images as
image_url blocks, calls the agents-platform API in stateless mode, parses
and displays the result.

Adapted from the batch test patterns in run_xml_batch_v2.py.
"""
import json, urllib.request, re, time, sys, io
from urllib.parse import urlparse, parse_qs, unquote

# Force UTF-8 to avoid GBK encoding crashes in cmd.exe pipe
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://192.168.2.166:30030/agents-platform/api"
AGENT_ID = "6000bb28-36cc-426c-a676-3f1b7708d187"
IMG_BASE = "https://www.ccgp-chongqing.gov.cn/djc-gateway/files"
IMG_BUSINESS = "kjxyfile50m"

def make_img_url(path):
    if not path: return path
    path = path.strip().strip('"').strip("'")
    if path.startswith('http'): return path
    path = re.sub(r'^/+file\.ccgp-chongqing\.gov\.cn/', '', path)
    path = re.sub(r'^/+www\.ccgp-chongqing\.gov\.cn/', '', path)
    path = path.lstrip('/')
    fname = path.split('/')[-1] if '/' in path else path
    return f"{IMG_BASE}?filePath={path}&business={IMG_BUSINESS}&fileName={fname}"

def extract_detail_urls(html_text):
    if not html_text: return []
    urls = []
    for m in re.finditer(r"""<img[^>]+src=["']([^"']+)["']""", str(html_text), re.I):
        src = m.group(1)
        if 'filePath=' in src:
            q = urlparse(src).query
            fp = parse_qs(q).get('filePath', [None])[0]
            if fp: src = unquote(fp)
        urls.append(src)
    return urls

def fix_json(s):
    try: return json.loads(s)
    except:
        try: return json.loads(s.replace('\\\\"', '\\"'))
        except: return None

def norm(v):
    v = str(v).strip()
    if v in ('-1','0','FALSE','false','False','fail','FAIL','reject','REJECT'): return "0"
    if v in ('2','1','TRUE','true','True','pass','PASS'): return "1"
    return v

def main():
    data_file = sys.argv[1] if len(sys.argv) > 1 else r"D:\平时处理文件\2026年7月\直采商城\test_data_audit_log_103.json"
    idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = [i for i in data["items"] if i["test_type"] == "regression"]
    if idx >= len(items):
        print("Index %d out of range (%d items)" % (idx, len(items)))
        sys.exit(1)

    item = items[idx]
    gold = item.get("gold_auditResult", "?")

    print("=" * 60)
    print("#%d %s %s (%s) gold=%s" % (item["idx"], item["brand"], item["model"], item["cat"], gold))
    print("Original: %s" % ((item.get("gold_auditReason") or "")[:150]))

    rd = fix_json(item["audit_request_json"])
    if not rd:
        print("ERROR: cannot parse request JSON")
        sys.exit(1)

    main_imgs = [make_img_url(u) for u in (rd.get('imageUrls') or []) if u]
    detail_raw = extract_detail_urls(rd.get('goodsDetailHtml', ''))
    detail_imgs = [make_img_url(u) for u in detail_raw if u]

    content_parts = [{
        "type": "text",
        "text": "请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，严格按 Skill 输出格式返回 JSON（含 auditResult、auditReason）：\n" + item["audit_request_json"]
    }]
    for u in main_imgs:
        content_parts.append({"type": "image_url", "image_url": {"url": u}})
    for u in detail_imgs:
        content_parts.append({"type": "image_url", "image_url": {"url": u}})

    print("Images: %d main + %d detail" % (len(main_imgs), len(detail_imgs)))

    body = {
        "assistant_id": "agents-platform",
        "input": {"messages": [{"role": "user", "content": content_parts}]},
        "config": {"configurable": {"agent_id": AGENT_ID, "recursion_limit": 100}},
        "metadata": {"agent_id": AGENT_ID, "graph_id": "agents-platform"}
    }
    body_str = json.dumps(body, ensure_ascii=False)

    print("Sending (%d bytes)..." % len(body_str), end="", flush=True)
    start = time.time()
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/runs/wait",
            data=body_str.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = resp.read().decode("utf-8")
        elapsed = round(time.time() - start, 2)
        print(" done (%ss)" % elapsed)
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        print(" FAILED (%ss): %s" % (elapsed, str(e)[:150]))
        sys.exit(1)

    rj = json.loads(result)
    msgs = rj.get("messages", [])
    content = ""
    for m in reversed(msgs):
        if m.get("type") == "ai" and not m.get("tool_calls"):
            raw = m.get("content", "")
            if isinstance(raw, list):
                raw = "\n".join(b.get("text", "") for b in raw if isinstance(b, dict))
            content = raw
            break

    clean = content
    if "```json" in clean:
        clean = clean.split("```json")[1].split("```")[0].strip()
    elif "```" in clean:
        ps = [p for i, p in enumerate(clean.split("```")) if i % 2 == 1]
        if ps: clean = max(ps, key=len).strip()

    pred_val = None
    reason = ""
    try:
        pred = json.loads(clean)
        pred_val = norm(str(pred.get("auditResult", "?")))
        reason = pred.get("auditReason", "")
    except:
        m = re.search(r'"auditResult"\s*:\s*"?(\d+|PASS|FAIL|pass|fail|True|False|true|false)"?', content)
        if m:
            v = m.group(1)
            pred_val = "1" if v in ('1','PASS','pass','True','true') else "0"
        elif "不通过" in content[:200] and "通过" not in content[:200]:
            pred_val = "0"
        elif "通过" in content[:200]:
            pred_val = "1"
        else:
            pred_val = "parse_err"
        reason = content[:300]

    match = "MATCH" if pred_val == gold else "MISMATCH"
    print("\ngold=%s pred=%s %s (%ss)" % (gold, pred_val, match, elapsed))
    print("Reason: %s" % reason[:300])

    # Save result
    with open(r"C:\Users\Public\test_result.txt", "w", encoding="utf-8") as f:
        f.write("gold=%s\npred=%s\nmatch=%s\nelapsed=%ss\nreason=%s\n" % (gold, pred_val, match, elapsed, reason))

if __name__ == "__main__":
    main()
