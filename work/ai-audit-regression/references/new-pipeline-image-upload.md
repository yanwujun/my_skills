# New Pipeline: Image Delivery to Agent (3 Approaches)

As of 2026-06, the `ai_audit_training_README.md` documents multiple approaches for delivering product images to the agent during Step5 (image LLM analysis). This reference supersedes the original "upload to workspace" as the sole approach.

## Approach A: External URL Construction

Construct full CCGP gateway URLs from relative paths stored in `imageUrls`/`detailImageUrls`. The LLM fetches images directly from the gateway.
- **Overhead:** None
- **Reliability:** Medium — depends on LLM's ability to reach the gateway
- **When to use:** Quick rule-layer tests, Step5 not critical

## Approach B: `image_url` Block Embedding (Recommended)

**Proven effective 2026-06-16.** Embed images directly in the conversation context as `image_url` blocks in `messages[].content`. The agent reads them from the conversation history — no workspace upload, no `read_file`, no external URL access needed.

### Proven Results
In a 10-item test across 10 catalogs, this approach enabled the agent to:
- Detect "ASUSPRO" branding in 联硕弘道 portable computer images → brand mismatch flagged
- Detect "fujitsu" branding in DPK printer images → brand mismatch flagged
- Detect "富士通" branding in another DPK printer → brand mismatch flagged

These brand mismatches were **missed by the old JSON-only approach** (where images were listed in the DTO but not accessible to the LLM).

### Request Format
```json
{
  "role": "user",
  "content": [
    {"type": "text", "text": "请审核以下商品数据，返回JSON: ..."},
    {"type": "image_url", "image_url": {"url": "https://ccgp.../filePath=...&business=kjxyfile50m"}},
    {"type": "image_url", "image_url": {"url": "https://ccgp.../filePath=...&business=kjxyfile50m"}}
  ]
}
```

### ⚠️ Thread Creation Without Metadata
The API returns **422 Unprocessable Content** if `metadata` (with agent_id, agent_name, etc.) is included in the POST body when creating a thread. Thread creation requires only:
```json
{"assistant_id": "agents-platform"}
```
The agent_id/graph_id metadata goes into the **runs/wait** body, not the thread creation body.

## Approach C: Download & Upload to Workspace (Original New Pipeline)

Download images, upload to thread workspace, rewrite payload.

### Key Scripts

#### enrich_audit_training_data.py
Generates `*_dataset.jsonl` from SQL-exported CSV. Converts relative image paths.

#### run_audit_regression.py
The full regression runner. Per-item workflow:
1. Create thread (or reuse per-catalog thread)
2. Download images → upload to workspace → get /uploads/ paths
3. Rewrite request payload
4. POST /threads/{id}/runs/wait
5. Parse response, compare with gold_label

**Invocation:**
```powershell
pip install -r requirements-training.txt
python run_audit_regression.py --input training_output\query5_export_dataset.jsonl `
  --thread-mode per_catalog --limit 10 --ccgp-gateway
```

### Image Upload API
```python
resp = session.post(
    f"{base_url}/web/threads/{thread_id}/workspace/uploads",
    files={"file": (filename, image_bytes, content_type)}
)
```

## Decision Guide

| Approach | Overhead | Reliability | Speed | Best For |
|----------|----------|-------------|-------|----------|
| A: External URL | None | Medium | Instant | Step1-4 only, quick checks |
| **B: image_url blocks** | **Minimal** | **High** | **Instant** | **General Step5 testing** |
| C: Workspace upload | High | Highest | Slow | Production batch regression |

## Known Issues

- Thread creation 422s if metadata is included. Strip to bare `{"assistant_id": "agents-platform"}`.
- The API may return "PASS"/"FAIL" (string) instead of "1"/"0" for auditResult. Always normalize both formats.
- Agent UUID is not stable across service restarts. Always call `GET /web/agents` to discover the current ID dynamically.
