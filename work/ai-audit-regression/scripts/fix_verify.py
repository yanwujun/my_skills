#!/usr/bin/env python3
"""
Fix verification: re-test 3-5 specific items after skill update.
Reads cached JSON, runs threaded for session links.
Usage: Edit TARGETS below, then run.
"""
import json, subprocess, os, time, re
from urllib.parse import urlparse, parse_qs, unquote

# ====== CONFIG ======
DATA = "/mnt/d/项目/gitlib/智能审核/doc/线上数据/test_data_164.json"
BASE_URL = "http://192.168.2.166:30030/agents-platform/api"
AGENT_ID = "6000bb28-36cc-426c-a676-3f1b7708d187"
GRAPH_ID = "agents-platform"
IMG_BASE = "https://www.ccgp-chongqing.gov.cn/djc-gateway/files"
IMG_BUSINESS = "kjxyfile50m"
WEB_UI = "http://192.168.2.166:5175"
TIMEOUT = 180

# Edit these: (catalog, brand) pairs to re-test
TARGETS = [
    ("A4彩色打印机", "佳能（Canon）"),
    ("复印纸", "夏丘印务"),
    ("越野车（含SUV）", "小鹏"),
]

# ====== HELPERS ======
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

def detail_imgs(html_text):
    if not html_text: return []
    urls = []
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', str(html_text), re.I):
        src = m.group(1)
        if 'filePath=' in src:
            q = urlparse(src).query
            fp = parse_qs(q).get('filePath', [None])[0]
            if fp: src = unquote(fp)
        urls.append(src)
    return urls

def curl_post(url, data, timeout=TIMEOUT):
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
        return None, round(time.time()-start, 2), "timeout"

def parse_response(resp_json):
    msgs = resp_json.get("messages", [])
    c = ""
    for m in reversed(msgs):
        if m.get("type") == "ai" and not m.get("tool_calls"):
            raw = m.get("content", "")
            if isinstance(raw, list):
                raw = "\n".join(b.get("text", "") for b in raw if isinstance(b, dict))
            c = raw; break
    clean = c
    if "```json" in clean: clean = clean.split("```json")[1].split("```")[0].strip()
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

# ====== MAIN ======
data = json.load(open(DATA, encoding='utf-8'))
target_set = set(TARGETS)
found = {}
for item in data['items']:
    key = (item['cat'], item['brand'])
    if key in target_set and key not in found:
        found[key] = item

print(f"Found {len(found)}/{len(TARGETS)} targets\n")
for (cat, brand), item in found.items():
    human = norm(item['human'])
    fast = norm(item['fast'])
    rd = json.loads(item['audit_request_json'])
    imgs = [make_img_url(u) for u in (rd.get('imageUrls') or []) if u]
    detail_raw = detail_imgs(rd.get('goodsDetailHtml', ''))
    detail_img_urls = [make_img_url(u) for u in detail_raw if u]
    if detail_img_urls: rd['detailImageUrls'] = detail_raw

    parts = [{"type":"text","text":"请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，严格按 Skill 输出格式返回 JSON（含 auditResult、auditReason）：\n"+json.dumps(rd,ensure_ascii=False)}]
    for u in imgs: parts.append({"type":"image_url","image_url":{"url":u}})
    for u in detail_img_urls: parts.append({"type":"image_url","image_url":{"url":u}})

    meta = json.dumps({"assistant_id":GRAPH_ID,"metadata":{"agent_id":AGENT_ID,"agent_name":"kjxy-goods-audit","owner":"dev-user","user_name":"Dev User","graph_id":GRAPH_ID,"tag":f"fix-{cat}"}})
    tresp, _, _ = curl_post(f"{BASE_URL}/threads", meta, 10)
    tid = json.loads(tresp).get("thread_id","") if tresp else ""

    body = json.dumps({"assistant_id":GRAPH_ID,"input":{"messages":[{"role":"user","content":parts}]},"config":{"configurable":{"agent_id":AGENT_ID,"recursion_limit":100}},"metadata":{"agent_id":AGENT_ID,"graph_id":GRAPH_ID}}, ensure_ascii=False)
    resp, elapsed, http_code = curl_post(f"{BASE_URL}/threads/{tid}/runs/wait", body, TIMEOUT)

    if not resp:
        pred = "T/O" if "timeout" in http_code else f"ERR({http_code})"; reason = ""
    else:
        pred, reason = parse_response(json.loads(resp))

    mark = "✅" if pred == human else "❌"
    print(f"{cat} / {brand}  人工={human} fast={fast} pred={pred} {mark} {elapsed}s")
    if reason: print(f"  reason: {reason[:200]}")
    print(f"  {WEB_UI}/?thread_id={tid}\n")

print("Done.")
