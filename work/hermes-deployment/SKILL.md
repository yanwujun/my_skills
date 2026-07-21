---
name: hermes-deployment
description: "Deploy, daemonize, and operate Hermes Agent as a long-running server service — background processes, SSH remote access, Web UI frontend (Open WebUI), autostart strategies, and production hardening."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, devops, deployment, daemon, ssh, autostart, systemd, wsl, production]
    related_skills: [hermes-agent, webhook-subscriptions]
---

# Hermes Deployment & Operations

Production readiness for Hermes Agent — making it survive reboots, SSH disconnects, and run persistently in the background.

## Quick Reference

```bash
# Check current state
systemctl --user status hermes-gateway
loginctl show-user $USER | grep Linger
ps aux | grep -i hermes | grep -v grep
```

---

## 1. Background Running

### A. Gateway Daemon (recommended — most capable)

The gateway is a long-running background process that supports messaging platforms AND stays alive for cron tasks.

```bash
hermes gateway install       # Install as systemd --user service
hermes gateway start         # Start the service
hermes gateway stop          # Stop
hermes gateway restart       # Restart
hermes gateway status        # Check if running
hermes gateway run           # Run foreground (for testing)
```

Gateway logs: `~/.hermes/logs/gateway.log`

**CRITICAL: Enable lingering** — without this, systemd --user services die on SSH logout:
```bash
sudo loginctl enable-linger $USER
# Verify: loginctl show-user $USER | grep Linger
# Should show: Linger=yes
```

### B. Cron Jobs (fire-and-forget)

Cron jobs are managed by the gateway scheduler and run at specified intervals:

```bash
hermes cron list              # List all jobs
hermes cron create "0 9 * * *" --prompt "Daily task" --skills "skill-name"
hermes cron status            # Scheduler status
```

Cron jobs survive gateway restarts — they're stored in the session database.

### C. tmux Detached Session (manual/adhoc)

For when you want a persistent interactive session you can reattach to:

```bash
tmux new-session -d -s hermes 'hermes'                    # Start detached
tmux attach -t hermes                                     # Reattach
tmux send-keys -t hermes '/skill ruankao-assistant' Enter # Send commands
tmux capture-pane -t hermes -p | tail -30                 # Read output
tmux kill-session -t hermes                               # Kill
```

### D. MCP Serve (multiple instances)

The user's environment shows multiple `hermes mcp serve` processes — these are MCP servers for IDE/tool integration. They are independent of the main gateway and can run alongside each other. Each process serves one tool.

---

## 2. SSH Remote Access

Since Hermes is a CLI tool running in a terminal, SSH is a first-class access method.

### A. Direct SSH Session

```bash
ssh user@server
hermes                       # Interactive chat
hermes --continue            # Resume most recent session
hermes -r <session_id>       # Resume specific session
```

### B. Remote Gateway (access via messaging platforms)

The gateway can connect to Telegram/Discord/Slack/etc. This means you NEVER need to expose SSH — just message the bot:

```bash
hermes gateway setup         # Configure platforms
hermes gateway run           # Verify connections
hermes gateway install       # Permanent service
```

Supported platforms: Telegram, Discord, Slack, WhatsApp, Signal, DingTalk, Feishu, WeCom, Matrix, Email, SMS, and more.

### C. ssh-based Remote Control

```bash
# Run one-shot query remotely
ssh user@server "hermes chat -q 'Check server status'"

# Trigger a cron job remotely
ssh user@server "hermes cron run <job_id>"

# Check gateway health remotely
ssh user@server "hermes gateway status"
```

### D. Session Resume Over SSH

```bash
# Remote server
hermes                      # Start session, work...

# Disconnect, reconnect later:
ssh user@server
hermes --continue           # Picks up right where you left off
# or
hermes session list         # Find the session ID
hermes -r <session_id>      # Resume by ID
```

---

## 3. Autostart Strategies

### A. Linux Server with systemd (best — recommended)

Gateway install already creates the service. Just ensure lingering is enabled:

```bash
hermes gateway install        # Creates ~/.config/systemd/user/hermes-gateway.service
sudo loginctl enable-linger $USER
systemctl --user enable hermes-gateway    # Enable on boot
systemctl --user start hermes-gateway     # Start now
```

The service automatically restarts on failure (Restart=on-failure in the unit file).

### B. crontab @reboot (universal fallback)

Works on any Unix system:

```bash
crontab -e
# Add:
@reboot sleep 10 && export PATH="$HOME/.local/bin:$PATH" && tmux new-session -d -s hermes 'hermes'
# Or for gateway:
@reboot sleep 15 && export PATH="$HOME/.local/bin:$PATH" && cd && hermes gateway run > ~/.hermes/logs/autostart.log 2>&1 &
```

The `sleep` gives the network/system time to initialize before Hermes starts.

### C. WSL/Windows (your environment)

WSL requires special handling because it terminates background processes when all shell sessions close.

**Option 1: systemd in WSL (recommended)**
```bash
# /etc/wsl.conf
[boot]
systemd=true
```
Then gateway service works normally.

**Option 2: Windows Task Scheduler**
Create a task that runs at startup:
- Trigger: At startup
- Action: `wsl -d Ubuntu -u <user> hermes gateway run`
- Or: `wsl -d Ubuntu -u <user> tmux new-session -d -s hermes 'hermes'`

**Option 3: bashrc autostart**
```bash
# ~/.bashrc — starts Hermes in tmux if not already running
if [ -z "$TMUX" ] && [ -z "$HERMES_AUTOSTARTED" ]; then
    export HERMES_AUTOSTARTED=1
    tmux new-session -d -s hermes 'hermes' 2>/dev/null || true
fi
```

---

## 4. Production Hardening

### Health Checks

```bash
# Quick status
hermes doctor                  # Full dependency check
hermes gateway status          # Service status
hermes status --all            # All component statuses
hermes cron status             # Scheduler health
```

### Log Monitoring

```bash
# Gateway logs
tail -f ~/.hermes/logs/gateway.log

# Error filtering
grep -i "error\|failed\|exception" ~/.hermes/logs/gateway.log | tail -30

# Session store stats
hermes sessions stats
```

### Recovery

```bash
# Service crash
systemctl --user reset-failed hermes-gateway
hermes gateway restart

# Configuration corruption
hermes config check            # Find issues
hermes config migrate          # Fix outdated config
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak  # Backup first!

# Credential issues
hermes doctor --fix            # Auto-fix common problems
hermes auth list <provider>    # Check credential pools
```

### Resource Limits

Hermes gateway is not memory-intensive. The user's environment shows:
- Gateway daemon: ~170MB RSS (Python process)
- MCP serve per instance: ~70MB RSS
- These persist from session to session

For long-running servers, consider:
- `ulimit -n` (file descriptors) — gateway uses WebSocket connections
- `ulimit -u` (processes) — if spawning sub-agents

---

## 5. Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| **SSH logout kills gateway** | Gateway stops when you disconnect | `sudo loginctl enable-linger $USER` |
| **WSL2 terminates on session close** | Processes die after you close Terminal | Enable `systemd=true` in `/etc/wsl.conf` |
| **Two gateway instances** | "Address already in use" | `hermes gateway restart` not `run`; kill stale processes |
| **Gateway crash loop** | Service restarts immediately and fails again | `systemctl --user reset-failed hermes-gateway` then investigate logs |
| **Cron jobs stop after reboot** | No scheduled tasks run | Ensure gateway service is enabled: `systemctl --user enable hermes-gateway` |
| **MCP serve processes accumulate** | Many `hermes mcp serve` processes idle | Killed when parent session exits; manual `kill` if orphaned |
| **Multiple Python processes** | Confusion about which is which | `ps aux \| grep hermes \| grep -v grep` to see each PID and role |
| **`.env` not read by services** | Gateway can't find API keys | `.env` must be at `~/.hermes/.env` — systemd --user inherits HOME correctly |
| **Slow startup after reboot** | Gateway fails because network isn't ready | Use `RestartSec=10` or `sleep` in crontab |

---

## 6. Architecture Overview

Typical production deployment:

```
User
 ├── SSH ──→ hermes chat (interactive CLI session)
 ├── Telegram/Discord ──→ Gateway (background daemon, PID 1 of agent)
 │                           ├── Scheduled tasks (cron scheduler)
 │                           ├── Messaging platforms (Telegram, etc.)
 │                           └── MCP servers (IDE integration)
 ├── Browser ──→ Open WebUI ──→ Hermes API Server (port 8642, OpenAI-compatible)
 └── cron/scheduled ──→ hermes cron (runs inside gateway process)
```

The gateway process is the backbone — it keeps the scheduler alive, listens on messaging platforms, and maintains persistent state. The `hermes chat` interactive sessions are ephemeral frontends that can join/resume/leave without affecting the gateway.

---

## 7. Web UI Frontend (Open WebUI)

Hermes Agent has a built-in OpenAI-compatible API Server adapter that lets any OpenAI-compatible frontend connect to it.

### Architecture

```
Browser (http://localhost:3000)
    │
    ▼
Open WebUI (or LobeChat, LibreChat, NextChat, etc.)
    │  OpenAI-compatible API call
    ▼
Hermes API Server (port 8642 — inside gateway)
    │
    ▼
Hermes Agent (DeepSeek / any provider)
```

### Quick Setup

**1. Enable API Server** in `~/.hermes/config.yaml`:
```yaml
platforms:
  api_server:
    host: 127.0.0.1
    port: 8642
    key: ''                           # set a key for production!
    enabled: true
```

**2. Start gateway** (API Server auto-starts):
```bash
hermes gateway run --replace
```

Verify:
```bash
curl http://127.0.0.1:8642/health
curl http://127.0.0.1:8642/v1/models
```

**3. Install Open WebUI** (pip — no Docker needed):
```bash
pip3 install open-webui --break-system-packages
mkdir -p ~/.open-webui-data
OPENAI_API_BASE_URLS="http://127.0.0.1:8642/v1" \
OPENAI_API_KEYS="" \
DATA_DIR="$HOME/.open-webui-data" \
open-webui serve --host 127.0.0.1 --port 3000
```

> **CRITICAL:** Always set `DATA_DIR` to an explicit persistent path. Without it, Open WebUI auto-detects the data directory based on shell context — after restarts it may detect a different directory, creating a *new* empty database and losing all data.

**4. First-time setup:** Open http://localhost:3000 → register admin account → Settings → Connections → verify Hermes connection.

**5. Full pipeline test:**
```bash
curl -s http://127.0.0.1:8642/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'
```

### Toolsets Configuration

The API Server can restrict which tools are available via WebUI:
```yaml
platforms:
  api_server:
    toolsets:
      - web
      - terminal
      - file
      - skills
      - memory
      - session_search
```
Default: all available tools are exposed.

### Alternative Frontends

Any OpenAI-compatible frontend works — point at `http://127.0.0.1:8642/v1`: LobeChat, LibreChat, NextChat, ChatBox, AnythingLLM.

### Common Pitfalls (WebUI-specific)

| Pitfall | Fix |
|---------|-----|
| Gateway restart kills connection | Wait for restart, retry |
| "Model not found" | Check `curl http://127.0.0.1:8642/v1/models` |
| Two gateway instances | `hermes gateway run --replace` |
| Open WebUI startup hangs | Normal for first-run DB migration; wait 30-60s |
| API Server refuses to start on 0.0.0.0 | Set a real API key or bind to 127.0.0.1 |
| Data directory lost after restart | Always set `DATA_DIR` to a fixed path |
| User says "not working" but vague | Run triage: check ports, health, models, direct API test |

### Detailed Reference

For full Open WebUI setup transcript, troubleshooting guide, and environment-specific notes:
- `references/webui-setup-detail.md` — full setup transcript from actual WSL pip installation
- `references/webui-data-dir-troubleshooting.md` — lost data directory recovery

## Reference Files

For real-world deployment state diagnosis (process patterns, memory usage, interpretation rules):
- `references/deployment-state-diagnosis.md` — annotated `ps aux` output from a healthy WSL2 deployment

## 8. Verification Checklist

After setting up deployment:

- [ ] `systemctl --user is-active hermes-gateway` → `active`
- [ ] `loginctl show-user $USER | grep Linger` → `Linger=yes`
- [ ] `systemctl --user is-enabled hermes-gateway` → `enabled`
- [ ] Reboot test: `sudo reboot && sleep 30 && ssh user@server "systemctl --user is-active hermes-gateway"` → `active`
- [ ] SSH test: connect, disconnect, reconnect, `hermes --continue` resumes correctly
- [ ] Cron test: `hermes cron status` reports scheduler running
- [ ] WebUI test: `curl http://127.0.0.1:8642/health` → `{"status": "ok"}`
- [ ] WebUI test: `curl http://127.0.0.1:3000/health` → service running
- [ ] Model test: `curl http://127.0.0.1:8642/v1/models` → returns `hermes-agent`
