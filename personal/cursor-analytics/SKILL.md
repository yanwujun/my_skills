---
name: cursor-analytics
description: Extract and analyze Cursor AI session data from the internal state.vscdb SQLite database. Use when the user wants to review their Cursor usage patterns, analyze conversation history, or audit AI-assisted development activity.
---

# Cursor Session Analytics

Extract, query, and analyze Cursor editor's AI conversation history stored in its internal SQLite database.

## Trigger conditions

- User asks to analyze Cursor conversation/session history
- User asks "what have I been using Cursor for"
- User wants to audit or review Cursor AI usage patterns
- User asks to extract chat data from Cursor
- **User asks how to reduce/save Cursor token consumption or optimize Cursor usage** → load `references/cursor-token-optimization.md` for full strategy guide including CodeGraph MCP integration, .cursorrules best practices, and WSL2 pitfalls

## Data location

| Platform | Path |
|----------|------|
| Windows | `%APPDATA%/Roaming/Cursor/User/globalStorage/state.vscdb` |
| macOS | `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` |
| Linux | `~/.config/Cursor/User/globalStorage/state.vscdb` |

The file is typically 2-5 GB. Cursor locks it while running — always copy before querying.

## Step 1: Copy the database

```bash
cp "$CURSOR_DB_PATH" /tmp/cursor_state_copy.vscdb
```

Verify the copy: `stat -c%s /tmp/cursor_state_copy.vscdb` should match the original.

## Step 2: Understand the schema

Two tables:

| Table | Rows (typical) | Content |
|-------|---------------|---------|
| `ItemTable` | ~1,500 | VSCode extension state (key-value) |
| `cursorDiskKV` | ~260,000 | **Cursor AI data** (key-value) |

The `cursorDiskKV` table has columns `key` (TEXT) and `value` (BLOB, JSON).

### Key patterns in cursorDiskKV

| Key prefix | What it stores | Count |
|-----------|---------------|-------|
| `composerData:<uuid>` | Session metadata (one per conversation) | ~1,800 |
| `bubbleId:<deviceId>:<uuid>` | Individual messages | ~100,000 |
| `agentKv:blob:<hash>` | Agent state blobs | ~130,000 |
| `codeBlockDiff:...` | Code diffs generated | varies |
| `messageRequestContext:...` | Message context metadata | varies |

### Bubble message structure

Each `bubbleId` value is a JSON object with these key fields:

| Field | Meaning |
|-------|---------|
| `type` | `1` = user message, `2` = assistant message |
| `text` | Plain text content (may be empty if richText is used) |
| `richText` | Structured rich text (extract `root.children[].children[].text`) |
| `createdAt` | ISO 8601 timestamp string |
| `unifiedMode` | `chat` or `agent` or numeric code |
| `workspaceProjectDir` | Project directory path |
| `thinking` | AI thinking/reasoning block (assistant only) |
| `tokenCount` | `{inputTokens, outputTokens}` |

## Step 3: Query with Python

Use `execute_code` with sqlite3. Key queries:

### Count sessions by month

```python
import sqlite3, json
from datetime import datetime
from collections import defaultdict

db = "/tmp/cursor_state_copy.vscdb"
conn = sqlite3.connect(db)
cur = conn.cursor()

monthly = defaultdict(int)
cur.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'")
for key, value in cur.fetchall():
    data = json.loads(value)
    ts = data.get('createdAt', 0)
    if ts:
        dt = datetime.fromtimestamp(ts / 1000)
        monthly[dt.strftime('%Y-%m')] += 1

for m in sorted(monthly):
    print(f"{m}: {monthly[m]} sessions")
```

### Sample user messages by month

```python
cur.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'bubbleId:%' AND value IS NOT NULL")
for key, value in cur.fetchall():
    data = json.loads(value)
    if data.get('type') != 1:  # user messages only
        continue
    text = data.get('text', '')
    # Extract from richText if text is empty
    if not text:
        rt = data.get('richText', {})
        for child in rt.get('root', {}).get('children', []):
            for c in child.get('children', []):
                if c.get('text'):
                    text += c['text']
    if len(text.strip()) < 3:
        continue
    created = data.get('createdAt', '')
    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
    print(f"[{dt.strftime('%Y-%m-%d %H:%M')}] {text[:200]}")
```

### Get project context

```python
workspace = data.get('workspaceProjectDir', '')
# Simplify: take last path component
proj = workspace.split('\\')[-1] if '\\' in workspace else workspace.split('/')[-1]
```

## Step 4: Analysis patterns

When analyzing, group by month and look for:

1. **Topic clusters** — repeated keywords indicating recurring work types
2. **Mode shift** — chat vs agent ratio over time
3. **Project diversity** — how many different workspaces
4. **Message density** — sessions with 10+ turns (deep work)
5. **Recurring commands** — `/review-svn`, specific file references

## Pitfalls

- **DB locked**: Always copy the file first; Cursor holds a write lock while running.
- **Null values**: Some `bubbleId` rows have NULL values — filter with `WHERE value IS NOT NULL`.
- **Empty text**: Many messages store content in `richText` (LEXICAL editor format), not `text`. Fall back to richText extraction.
- **4GB+ file**: Queries can be slow. Use indexed queries and limit result sets.
- **Multiple device IDs**: `bubbleId` keys contain a device UUID prefix. The device with most bubbles is the primary machine.

## References

- `references/schema-details.md` — Full schema exploration notes and edge cases
- `references/cursor-token-optimization.md` — Token consumption optimization: CodeGraph MCP, .cursorrules, Agent vs Chat, WSL2 pitfalls
