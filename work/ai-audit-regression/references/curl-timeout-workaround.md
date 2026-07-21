# Curl-Based Timeout vs urllib — Practical Experience

## The problem

`urllib.request.urlopen(url, timeout=60)` does NOT reliably enforce timeouts on 
`/threads/{id}/runs/wait` calls where the server holds the connection open without 
sending data. This causes batch test scripts to hang indefinitely.

## The fix

Use `subprocess.run` with `curl --max-time N` instead. Curl exit code 28 
("operation timed out") fires reliably even on connections that don't send data.

## Measured behavior

| Approach | Item that triggers Step5/6 LLM | Item that triggers Step2 termination |
|----------|-------------------------------|--------------------------------------|
| urllib timeout=60 | Hangs indefinitely (bug) | Returns in <0.1s (works) |
| curl --max-time 60 | Returns after 60s with exit code 28 | Returns in <0.1s (works) |

## Thread degradation with sequential runs

When running 10+ `/threads/{id}/runs/wait` calls on the SAME thread:
- Items 1-3: 0.01s response time
- Items 4-7: 0.01s response time (still fast)
- Items 8-10: response time still fast, but subsequent runs on the same thread 
  may start getting curl timeout errors on items that previously completed in 0.01s

**Observed pattern:** After ~2 batches of 10 items on the same thread, items that 
should trigger Step2 termination (fast path) started consistently timing out at 60s.
Creating a fresh thread resolved the issue.

**Recommended approach:** 
- One thread per catalog (not one thread for all items)
- Create a new thread if testing more than 10 items sequentially
- Thread creation + metadata is fast (<0.5s)

## curl helper function (copy-paste ready)

```python
import subprocess, json, time, os

def curl_post(url, data, timeout=60):
    tmp_out = f"/tmp/audit_{int(time.time()*1000000)}.json"
    cmd = ["curl", "-s", "-X", "POST", url,
           "-H", "Content-Type: application/json",
           "-d", data,
           "--max-time", str(timeout),
           "-o", tmp_out,
           "-w", "%{http_code}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
    http_code = r.stdout.strip()
    if r.returncode == 28:  # curl timeout
        return None, timeout, "curl_timeout"
    if not os.path.exists(tmp_out) or os.path.getsize(tmp_out) == 0:
        return None, 0, f"http_{http_code}"
    with open(tmp_out, 'r') as f:
        content = f.read()
    try: os.remove(tmp_out)
    except: pass
    return content, 0, http_code
```
