# agents-platform API Modes & Web UI

## Thread Creation with Web UI Metadata

Threads created without `agent_id` and `agent_name` in metadata will NOT appear in the Web UI. The API accepts the creation but the Web UI filters by these fields.

**Correct thread creation (Web UI visible):**
```python
import json, urllib.request

BASE_URL = "http://<host>:30030/agents-platform/api"
thread_body = json.dumps({
    "assistant_id": "agents-platform",
    "metadata": {
        "agent_id": "341aa4fd-c0ae-4c89-b469-650e0c127b1d",
        "agent_name": "kjxy-goods-audit",
        "owner": "dev-user",
        "user_name": "Dev User",
        "graph_id": "agents-platform",
        "tag": "061601-便携式计算机"     # Optional: label for organization
    }
}).encode('utf-8')

req = urllib.request.Request(f"{BASE_URL}/threads", data=thread_body,
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=10) as resp:
    tid = json.loads(resp.read().decode('utf-8'))["thread_id"]
```

**Per-catalog convention:** When testing multiple catalogs, create one thread per catalog. Use `metadata.tag` to label each thread (e.g. `"061601-A3彩色打印机"`). The Web UI shows each thread as a separate conversation.

## Image URL Construction for Web UI Threads

When testing via threaded mode with image LLM analysis, image URLs must be full external URLs:

```python
def make_image_url(path):
    if not path: return path
    path = path.strip().strip('"').strip("'")
    if path.startswith('http'): return path
    fname = path.split('/')[-1]
    return f"https://www.ccgp-chongqing.gov.cn/djc-gateway/files?filePath={path}&business=kjxyfile50m&fileName={fname}"
```

Apply `make_image_url` to all elements in `req_data['imageUrls']` and `req_data['detailImageUrls']` before serializing the audit request into the thread message.

## API Endpoints

| # | Method | Path | Purpose | Persistence |
|---|--------|------|---------|-------------|
| 0 | GET | `/ok` | Health check | — |
| 1 | GET | `/web/agents` | List agents | — |
| 2 | POST | `/runs/wait` | **Stateless audit (recommended for batch)** | ❌ No thread |
| 3 | POST | `/runs/stream` | SSE streaming (debug) | ❌ |
| 4 | POST | `/threads` | Create session thread | ✅ |
| 5 | POST | `/threads/{id}/runs/wait` | Stateful audit | ✅ |

## Web UI

- **URL**: `http://<host>:5176` or `http://<host>:5177` (environment-dependent; check which port is running)
- **Thread URL format**: `http://<host>:5177/?thread_id=<uuid>` — use the `?thread_id=` parameter to jump directly to a specific thread
- Shows threads with full conversation history
- Only shows items tested via threaded mode (endpoint #4 → #5)
- **Stateless `/runs/wait` calls do NOT appear in the Web UI**

## Proven Config

| Parameter | Value |
|-----------|-------|
| Agent ID | `341aa4fd-c0ae-4c89-b469-650e0c127b1d` |
| Agent name | `kjxy-goods-audit` |
| Graph ID | `agents-platform` |
| Base URL | `http://localhost:30030/agents-platform/api` |

## Single-Item Testing via User's Existing Thread

When the user wants to test **one specific item** and see the result in their Web UI:

### Workflow

1. **Get the item's `audit_request_json` from XML/CSV** — parse it, fix escaping (XML=`html.unescape`, CSV=`\\\\\"` → `\\\\\\\"`)
2. **Ask the user for their thread_id** — they get it from the Web UI URL (`?thread_id=<uuid>`) or already shared it
3. **Write the full request body to a file** (avoids shell escaping issues with JSON-in-JSON):
   ```bash
   python3 -c "
   import json
   body = {
     'assistant_id': 'agents-platform',
     'input': {'messages': [{'role': 'user',
       'content': '请按框架协议商品智能审核 Skill 审核以下 GoodsAiAuditRequestDTO，返回 JSON：\n' + json.dumps(PARSED_AUDIT_REQUEST)}]},
     'config': {'configurable': {'agent_id': '<AGENT_UUID>', 'recursion_limit': 100}},
     'metadata': {'agent_id': '<AGENT_UUID>', 'graph_id': 'agents-platform'}
   }
   with open('/tmp/audit_body.json', 'w', encoding='utf-8') as f:
       json.dump(body, f, ensure_ascii=False)
   "
   ```
4. **Call the API using the user's thread**:
   ```bash
   curl -s -X POST "http://<host>:30030/agents-platform/api/threads/${THREAD_ID}/runs/wait" \
     -H "Content-Type: application/json" -d @/tmp/audit_body.json
   ```
5. **Confirm in Web UI**: User refreshes their `http://<host>:5177/?thread_id=<uuid>` page and sees the new result

### Key Rules

- **ALWAYS use the user's existing thread_id** — never create a new thread for single-item debugging. If the user provides a thread_id from the Web UI, use it.
- **Do NOT create a new thread** — results on a different thread won't appear in the user's Web UI view.
- **File-based body** is safer than inline JSON due to nested escaping (JSON containing JSON strings with Chinese characters).
- Parse the API response to extract the audit result immediately — don't rely on the Web UI alone for the answer.

## Threaded Mode Pitfalls**: Some items that pass Step2 (brand/model/catalog check) trigger Step5/6 LLM analysis and cause `/threads/{id}/runs/wait` to hang indefinitely, even with `urlopen(timeout=N)` set to 120s.
- **Partial results**: If a thread was created but some items timeout, the thread STILL appears in the Web UI with whatever results were persisted before the hang. The partial thread is useful for debugging the first item(s) even if later items failed.
- **Stateless workaround**: Use `/runs/wait` (endpoint #2) for batch regression; it's more reliable and handles timeouts better.
- **Web UI checking**: Browse to `http://<host>:5176` to see all threads. Each catalog gets its own thread row. If an item returned a result, its conversation will appear in the thread's message history.
- **Thread creation**: `POST /threads` with `{"assistant_id": "agents-platform"}` returns `{"thread_id": "..."}`. Thread IDs are UUIDs like `5b2abb73-26e9-4380-8...`.

## Cross-Host Deployment

The agents-platform API and the Web UI may run on different hosts (e.g. API in WSL, Web UI on Windows). To make threads visible:

1. Verify API connectivity: `curl http://<host>:30030/agents-platform/api/ok`
2. If the Web UI's Vite proxy targets `localhost:30030` (Windows), but the API runs in WSL, use port forwarding:
   ```
   # On Windows (as admin):
   netsh interface portproxy add v4tov4 listenport=30030 listenaddress=127.0.0.1 connectport=30030 connectaddress=<WSL_IP>
   ```
3. If the API is on the same machine as the test runner, `BASE_URL=http://localhost:30030/agents-platform/api` works directly.
