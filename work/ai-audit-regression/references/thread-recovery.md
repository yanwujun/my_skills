# Thread Recovery After Test Completion

## Problem

Thread IDs were not logged during a test run, but the threads still exist on the agents-platform server. The Web UI (port 5175) can display thread content if you have the UUID, but there is no "list my threads" endpoint in the public API.

## Solution: `POST /api/threads/search`

There IS an undocumented list endpoint:

```
POST /agents-platform/api/threads/search
Content-Type: application/json

{"agent_id": "<AGENT_UUID>", "limit": 250}
```

Returns an array of threads for that agent, most recent first. This works even though:
- `GET /api/threads` returns `405 Method Not Allowed`
- `GET /api/web/threads` returns `404 Not Found`
- The endpoint name `search` suggests parameter search but with `agent_id` it acts as a full list

## Matching Threads to Test Items

Once you have the thread list, match each thread to a test item by extracting the `baseBrand` from the run's input messages:

```python
import re, json, urllib.request

BASE_URL = "http://<host>:30030/agents-platform/api"

# Step 1: List threads
req = urllib.request.Request(f"{BASE_URL}/threads/search",
    data=json.dumps({"agent_id": "<AGENT_UUID>", "limit": 250}).encode(),
    headers={"Content-Type":"application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as resp:
    threads = json.loads(resp.read().decode())

# Step 2: For each thread, get runs and extract brand
matched = []
for t in threads:
    tid = t['thread_id']
    req = urllib.request.Request(f"{BASE_URL}/threads/{tid}/runs", method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        runs = json.loads(resp.read().decode())
    if not runs or runs[0].get('status') != 'success':
        continue

    # Extract brand from user message
    msgs = runs[0].get('kwargs',{}).get('input',{}).get('messages',[])
    for m in msgs:
        c = m.get('content', [])
        if isinstance(c, list):
            for part in c:
                if isinstance(part, dict) and part.get('type') == 'text':
                    text = part.get('text', '')
                    bm = re.search(r'"baseBrand"\s*:\s*"([^"]+)"', text)
                    if bm:
                        matched.append((tid, bm.group(1)))
                    break
        break
```

## Limitations

| Aspect | Available? | Notes |
|--------|:----------:|-------|
| Thread ID | ✅ Yes | From `threads_search` response |
| Brand/model of tested product | ✅ Yes | Extract from `kwargs.input.messages[].content` text payload |
| Catalog name | ✅ Yes | Extract from `"baseCatalog"` field in the same JSON payload |
| **Audit result (pass/fail)** | **❌ No** | `run.output` is always `{}` — result not persisted |
| **Audit reason** | **❌ No** | Only available in the live `/runs/wait` response |

**The audit result and reason are NOT stored in the run record.** This is a critical limitation: thread recovery can tell you WHICH product was tested and give you the thread ID for Web UI viewing, but it cannot tell you WHAT the agent decided or WHY.

## Mitigation: Always Log `tid=` in Real-time

```python
# In per-item print:
print(f"  [{idx}/{total}] {brand} {model} fast={fast} 人工={human} skill={pred} {match} {elapsed}s tid={tid}")

# In results dict:
all_results.append({"cat":cat, "tid":tid, "pred":pred, "reason":reason, ...})
```

Without this, only the thread link is recoverable — the actual audit judgment is lost forever.

## Key API Endpoint Summary

| Method | Endpoint | Purpose | Notes |
|--------|----------|---------|-------|
| `POST` | `/threads/search` | List threads by agent | Default limit is low, pass `"limit": 250` |
| `GET` | `/threads/{id}/runs` | Get run(s) for a thread | Only `GET` works, `POST` returns 422 |
| `GET` | `/threads/{id}` | Get thread metadata | Includes `created_at`, `updated_at`, `status` |
| `POST` | `/threads/{id}/runs/wait` | Run an audit (live) | This is where the result comes from — not persisted |
