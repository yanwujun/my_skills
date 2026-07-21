# -*- coding: utf-8 -*-
"""Test audit items with image_url blocks - fixed image URL construction"""
import json, urllib.request, re, time, sys, io
from urllib.parse import urlparse, parse_qs, unquote
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://192.168.2.166:30030/agents-platform/api"
AGENT = "6000bb28-36cc-426c-a676-3f1b7708d187"
IMG_BASE = "https://www.ccgp-chongqing.gov.cn/djc-gateway/files"
IMG_BUSINESS = "kjxyfile50m"

def make_img_url(path):
    if not path: return path
    path = path.strip().strip('"').strip("'")
    if path.startswith('http'): return path
    # Strip leading //file.ccgp-chongqing.gov.cn/ or //www.ccgp-chongqing.gov.cn/
    path = re.sub(r'^/+file\.ccgp-chongqing\.gov\.cn/', '', path)
    path = re.sub(r'^/+www\.ccgp-chongqing\.gov\.cn/', '', path)
    # Also strip any remaining leading slashes
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

data_file = r"D:\平时处理文件\2026年7月\直采商城\test_data_audit_log_103.json"
with open(data_file, "r", encoding="utf-8") as f:
    data = json.load(f)

idx_map = {i["idx"]: i for i in data["items"]}

tests = [
    (112, "品类不一致"),
    (56, "名称格式不规范"),
    (72, "图片数量不足"),
    (39, "URL不可访问"),
    (44, "通过(复印机)"),
]

results = []
t0 = time.time()

for idx, label in tests:
    item = idx_map[idx]
    gold = item.get("gold_auditResult", "?")
    print("\n" + "="*60)
    print("#%d [%s] %s %s (%s) gold=%s" % (idx, label, item["brand"], item["model"], item["cat"], gold))

    rd = fix_json(item["audit_request_json"])
    if not rd:
        print("ERROR: cannot parse request JSON")
        continue

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

    # Show first image URL for verification
    print("Images: %d main + %d detail" % (len(main_imgs), len(detail_imgs)))
    if main_imgs:
        print("  Sample: %s" % main_imgs[0][:100])

    # Create thread
    tb = json.dumps({"assistant_id":"agents-platform","metadata":{"agent_id":AGENT,"agent_name":"kjxy-goods-audit","graph_id":"agents-platform","tag":"v2_%d"%idx}}, ensure_ascii=False)
    req = urllib.request.Request(BASE+"/threads", data=tb.encode("utf-8"), headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        tid = json.loads(r.read().decode("utf-8"))["thread_id"]
    print("Thread: %s" % tid)

    # Build request body
    body = {
        "assistant_id":"agents-platform",
        "input":{"messages":[{"role":"user","content":content_parts}]},
        "config":{"configurable":{"agent_id":AGENT,"recursion_limit":100}},
        "metadata":{"agent_id":AGENT,"graph_id":"agents-platform"}
    }
    # Don't include metadata in thread creation body - it goes in runs/wait
    rb = json.dumps(body, ensure_ascii=False)

    print("Sending (%dB, %d blocks)..." % (len(rb), len(content_parts)), end="", flush=True)
    start = time.time()
    try:
        req = urllib.request.Request(BASE+"/threads/"+tid+"/runs/wait", data=rb.encode("utf-8"), headers={"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = r.read().decode("utf-8")
        elapsed = round(time.time()-start, 2)
        print(" done (%ss)" % elapsed)
    except Exception as e:
        elapsed = round(time.time()-start, 2)
        print(" FAILED: %s" % str(e)[:150])
        results.append({"idx":idx,"label":label,"gold":gold,"pred":"ERROR","elapsed":elapsed,"tid":tid})
        continue

    # Parse response
    rj = json.loads(resp)
    msgs = rj.get("messages",[])
    content = ""
    for m in reversed(msgs):
        if m.get("type")=="ai" and not m.get("tool_calls"):
            raw = m.get("content","")
            if isinstance(raw, list):
                raw = "\n".join(b.get("text","") for b in raw if isinstance(b,dict))
            content = raw
            break

    # Parse auditResult from content
    clean = content
    if "```json" in clean:
        clean = clean.split("```json")[1].split("```")[0].strip()
    elif "```" in clean:
        ps = [p for i,p in enumerate(clean.split("```")) if i%2==1]
        if ps: clean = max(ps, key=len).strip()

    result = None
    reason = ""
    try:
        pred = json.loads(clean)
        result = str(pred.get("auditResult","?"))
        reason = pred.get("auditReason","")
    except:
        # Try regex extraction
        m = re.search(r'"auditResult"\s*:\s*"?(\d+|PASS|FAIL|pass|fail|True|False|true|false)"?', content)
        if m:
            v = m.group(1)
            if v in ('1','PASS','pass','True','true'): result = "1"
            elif v in ('0','-1','FAIL','fail','False','false'): result = "0"

    if result is None:
        if "通过" in content[:200] and "不通过" not in content[:200]:
            result = "1"
        elif "不通过" in content[:200] or "退回" in content[:200]:
            result = "0"
        else:
            result = "parse_err"

    if not reason:
        reason = content[:300]

    match = "MATCH" if result == str(gold) else "MISMATCH"
    print("gold=%s pred=%s %s" % (gold, result, match))
    print("Reason: %s" % reason[:250])
    print("Web UI: http://192.168.2.166:5175/?thread_id=%s" % tid)

    results.append({"idx":idx,"label":label,"gold":gold,"pred":result,"match":match,"elapsed":elapsed,"tid":tid,"reason":reason[:300],"images":"%d+%d"%(len(main_imgs),len(detail_imgs))})

# Summary
print("\n" + "="*60)
print("SUMMARY (%d items, %ss)" % (len(results), round(time.time()-t0,1)))
for r in results:
    print("  #%d [%s] gold=%s pred=%s %s %ss" % (r["idx"], r["label"], r["gold"], r["pred"], r["match"], r["elapsed"]))
    print("       http://192.168.2.166:5175/?thread_id=%s" % r["tid"])

matched = sum(1 for r in results if r["match"]=="MATCH")
print("\nMatch: %d/%d" % (matched, len(results)))
