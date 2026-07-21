# -*- coding: utf-8 -*-
"""Simple 37-cat test - saves to TXT, robust to errors"""
import json, urllib.request, re, time, sys, io, os
from urllib.parse import urlparse, parse_qs, unquote
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://192.168.2.166:30030/agents-platform/api"
AGENT = "6000bb28-36cc-426c-a676-3f1b7708d187"

def mu(path):
    if not path: return path
    path = path.strip().strip('"').strip("'")
    if path.startswith('http'): return path
    path = re.sub(r'^/+file\.ccgp-chongqing\.gov\.cn/', '', path)
    path = re.sub(r'^/+www\.ccgp-chongqing\.gov\.cn/', '', path)
    path = path.lstrip('/')
    fn = path.split('/')[-1] if '/' in path else path
    return "https://www.ccgp-chongqing.gov.cn/djc-gateway/files?filePath=%s&business=kjxyfile50m&fileName=%s" % (path, fn)

def edu(html):
    if not html: return []
    urls = []
    for m in re.finditer(r"""<img[^>]+src=["']([^"']+)["']""", str(html), re.I):
        s = m.group(1)
        if 'filePath=' in s:
            q = urlparse(s).query
            fp = parse_qs(q).get('filePath', [None])[0]
            if fp: s = unquote(fp)
        urls.append(s)
    return urls

def fj(s):
    try: return json.loads(s)
    except:
        try: return json.loads(s.replace('\\\\"', '\\"'))
        except: return None

def np(v):
    v = str(v).strip()
    if v in ('-1','0','false','False','FALSE','FAIL','fail','reject','REJECT','no','NO'): return "0"
    if v in ('1','2','true','True','TRUE','PASS','pass','yes','YES','通过','审核通过'): return "1"
    if '不通过' in v or '退回' in v: return "0"
    return v

# Load
with open(r"D:\项目\gitlib\智能审核\doc\线上数据\test_data_164.json", encoding="utf-8") as f:
    data = json.load(f)

from collections import defaultdict
by_cat = defaultdict(list)
for item in data["items"]:
    by_cat[item["cat"]].append(item)

picks = []
for cat in sorted(by_cat):
    items = by_cat[cat]
    s2 = [i for i in items if "SCENARIO_2" in i.get("scenario","")]
    pick = s2[0] if s2 else items[0]
    picks.append(pick)

# Already done
done_cats = {"A3彩色打印机","A3黑白打印机","A4彩色打印机","A4黑白打印机","不间断电源（UPS）","会议桌","会议椅","便携式计算机","其他打印机（存折打印机）","其他打印机（证卡打印机）","办公桌","办公椅"}

outf = r"C:\Users\Public\test_37cat_v3.txt"
t0 = time.time()

for i, item in enumerate(picks):
    cat = item["cat"]
    if cat in done_cats:
        continue

    brand = item["brand"]
    model = item["model"]
    gold = "1"

    rd = fj(item["audit_request_json"])
    if not rd: continue

    imgs = [mu(u) for u in (rd.get('imageUrls') or []) if u]
    dimgs = [mu(u) for u in edu(rd.get('goodsDetailHtml', '')) if u]

    cp = [{"type":"text","text":"请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，严格按 Skill 输出格式返回 JSON（含 auditResult、auditReason）：\n"+item["audit_request_json"]}]
    for u in imgs: cp.append({"type":"image_url","image_url":{"url":u}})
    for u in dimgs: cp.append({"type":"image_url","image_url":{"url":u}})

    # Thread
    tb = json.dumps({"assistant_id":"agents-platform","metadata":{"agent_id":AGENT,"agent_name":"kjxy-goods-audit","graph_id":"agents-platform","tag":"v3_%d"%i}}, ensure_ascii=False).encode("utf-8")
    try:
        req = urllib.request.Request(BASE+"/threads", data=tb, headers={"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            tid = json.loads(r.read().decode("utf-8"))["thread_id"]
    except:
        with open(outf, "a", encoding="utf-8") as f:
            f.write("%s|%s|%s|THREAD_ERR|ERROR|0|\n" % (cat, brand, model))
        continue

    # Run
    rb = json.dumps({"assistant_id":"agents-platform","input":{"messages":[{"role":"user","content":cp}]},"config":{"configurable":{"agent_id":AGENT,"recursion_limit":100}},"metadata":{"agent_id":AGENT,"graph_id":"agents-platform"}}, ensure_ascii=False).encode("utf-8")
    start = time.time()
    try:
        req = urllib.request.Request(BASE+"/threads/"+tid+"/runs/wait", data=rb, headers={"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=300) as r:
            resp = r.read().decode("utf-8")
        elapsed = round(time.time()-start, 2)
    except Exception as e:
        elapsed = round(time.time()-start, 2)
        with open(outf, "a", encoding="utf-8") as f:
            f.write("%s|%s|%s|TIMEOUT|ERROR|%s|%s\n" % (cat, brand, model, elapsed, tid))
        continue

    rj = json.loads(resp)
    content = ""
    for m in reversed(rj.get("messages",[])):
        if m.get("type")=="ai" and not m.get("tool_calls"):
            raw = m.get("content","")
            if isinstance(raw, list): raw = "\n".join(b.get("text","") for b in raw if isinstance(b,dict))
            content = raw; break

    clean = content
    if "```json" in clean: clean = clean.split("```json")[1].split("```")[0].strip()
    elif "```" in clean:
        ps = [p for i,p in enumerate(clean.split("```")) if i%2==1]
        if ps: clean = max(ps, key=len).strip()

    pred_val = None
    reason = ""
    try:
        pj = json.loads(clean)
        pred_val = np(pj.get("auditResult","?"))
        reason = pj.get("auditReason","")
    except:
        pass
    if pred_val not in ('0','1'):
        m = re.search(r'"auditResult"\s*:\s*"?(\S+?)"?(?:\s*[,}])', content)
        pred_val = np(m.group(1)) if m else None
    if pred_val not in ('0','1'):
        pred_val = "0" if ("不通过" in content[:200] and "通过" not in content[:100]) else ("1" if ("通过" in content[:200] or "PASS" in content[:200]) else "?")

    match = "MATCH" if pred_val == gold else "MISMATCH"
    reason = (reason or content)[:200].replace("\n"," ").replace("|","/")
    
    line = "%s|%s|%s|%s|%s|%s|%s|%s\n" % (cat, brand, model, gold, pred_val, match, elapsed, tid)
    with open(outf, "a", encoding="utf-8") as f:
        f.write(line)
    
    total = len([l for l in open(outf, encoding="utf-8").readlines() if l.strip()]) + len(done_cats)
    print("[%d/37] %s | gold=%s pred=%s %s %ss" % (total, cat, gold, pred_val, match, elapsed), flush=True)

elapsed = round(time.time()-t0, 1)
print("\nDONE: %ss" % elapsed)
