# Open WebUI — Lost Data Directory Troubleshooting

## Symptom

User reports "Open WebUI 不正常" — page loads but:
- Must re-register account every time Open WebUI restarts
- Connection config (API URL) is gone after restart
- Chat history disappeared

## Root Cause

Open WebUI stores its SQLite database (`webui.db`) in an auto-detected data directory. Without an explicit `DATA_DIR` environment variable, the default location varies:

| Installation Method | Default Data Dir |
|-------------------|-----------------|
| `pip install open-webui` | `~/.local/lib/python3.x/site-packages/open_webui/data/` |
| Docker | `/app/backend/data/` |
| Manual git clone | `./data/` |

**Problem:** After process restart (especially if killed and restarted in a different working directory or by a different user/shell), the data directory detection may differ, effectively creating a *new* database. The old database still exists but isn't found.

## Fix

### 1. Set explicit DATA_DIR

```bash
mkdir -p ~/.open-webui-data

OPENAI_API_BASE_URLS="http://127.0.0.1:8642/v1" \
OPENAI_API_KEYS="" \
DATA_DIR="$HOME/.open-webui-data" \
open-webui serve --host 127.0.0.1 --port 3000
```

With `DATA_DIR` set, Open WebUI stores everything in `~/.open-webui-data/webui.db` regardless of working directory or shell context. Survives restarts.

### 2. If you already have data to preserve

Find the old DB and copy it:

```bash
# Find old database files
find /home/administrator -name "webui.db" -type f 2>/dev/null

# Copy to the new data dir
cp /path/to/old/webui.db ~/.open-webui-data/webui.db

# Then restart with DATA_DIR set
```

### 3. Our current live setup (from 2026-05-07 session)

- Data directory: `/home/administrator/.open-webui-data`
- PID at last restart: 7605
- API Server: `http://127.0.0.1:8642/v1`
- Open WebUI: `http://127.0.0.1:3000`

## Verification

```bash
# Check Open WebUI is running and health endpoint returns 200
curl -sf http://127.0.0.1:3000/health

# Check the DB exists in the expected location
ls -la ~/.open-webui-data/webui.db
```
