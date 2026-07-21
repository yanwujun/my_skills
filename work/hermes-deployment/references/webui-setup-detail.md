# Open WebUI pip Installation on WSL — Detailed Notes

This captures the actual session that set up Open WebUI v0.9.2 via pip on WSL2 (Ubuntu, Python 3.12) connecting to Hermes API Server.

## Environment

- **OS:** WSL2 (Linux DESKTOP-JREHGHM 6.6.87.2-microsoft-standard-WSL2)
- **Hermes:** v0.11.0 (2026.4.23), Python 3.11.15
- **Open WebUI:** v0.9.2 (pip install)
- **Provider:** DeepSeek (deepseek-chat via api.deepseek.com)
- **Python:** 3.12 (system), 3.11 (Hermes venv)

## Installation Steps That Worked

```bash
# Install Open WebUI (Debian requires --break-system-packages)
pip3 install open-webui --break-system-packages
```

This pulls many deps: fastapi, uvicorn, sqlalchemy, alembic, aiohttp, authlib, chromadb, etc. The install is large (~500+ packages) and can take 2+ minutes on slower connections.

## Configuration

### config.yaml for api_server

Added to `~/.hermes/config.yaml` at the `platforms:` section:

```yaml
platforms:
  api_server:
    host: 127.0.0.1
    port: 8642
    key: ''
    enabled: true
```

Also added corresponding `platform_toolsets.api_server:` list.

### Starting the services

Gateway must be restarted to pick up new config:

```bash
hermes gateway run --replace
```

Open WebUI with preset connection:

```bash
OPENAI_API_BASE_URLS="http://127.0.0.1:8642/v1" \
OPENAI_API_KEYS="" \
open-webui serve --host 127.0.0.1 --port 3000
```

## API Server Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health check → `{"status": "ok"}` |
| `GET /v1/models` | List models → `hermes-agent` |
| `POST /v1/chat/completions` | Chat completions (OpenAI format) |
| `GET /v1/capabilities` | Machine-readable capabilities |
| `POST /v1/runs` | Start a structured run |
| `GET /v1/runs/{id}/events` | SSE event stream |

## Database Location

Open WebUI stores data at:
```
/home/administrator/.local/lib/python3.12/site-packages/open_webui/data/webui.db
```

Default secret key file (auto-generated):
```
/home/administrator/.webui_secret_key
```

## First-Time User Flow

1. Open `http://localhost:3000`
2. Register first account (becomes admin)
3. Settings → Connections should show Hermes connection preset via `OPENAI_API_BASE_URLS`
4. Select model `hermes-agent` when chatting
5. Conversation works immediately — API Server proxies to Hermes Agent which uses configured provider (DeepSeek)

## Known Issues

- When Open WebUI starts, alembic runs database migrations that can take 30-60s on first launch
- The API Server logs show up in `~/.hermes/logs/gateway.log`
- Open WebUI logs go to stdout
- No Docker available in this WSL environment — pip install was the only option
- `hermes gateway run --replace` replaces ALL gateway instances (including QQ bot, etc.)
