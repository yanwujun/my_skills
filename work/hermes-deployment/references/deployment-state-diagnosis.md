# Deployment State Diagnosis — Real-World Reference

This file documents the actual outputs and interpretations from a working Hermes deployment on WSL2 + Ubuntu, serving as a reference for what a healthy deployment looks like.

## Health Check Commands

```bash
systemctl --user list-units --type=service | grep hermes
loginctl show-user $USER | grep Linger
which tmux
ps aux | grep -i hermes | grep -v grep
```

## Healthy Output (reference)

```
hermes-gateway.service loaded active running Hermes Agent Gateway - Messaging Platform Integration
Linger=yes
/usr/bin/tmux
user      301  0.0  0.4 303088 69948 pts/0    Ssl+ 13:58  0:16 ... hermes mcp serve
user     3921  2.1  1.0 1011716 169760 ?      Ssl  18:36  0:04 ... hermes_cli.main gateway run --replace
```

## Process Interpretation

| Process | Role | Expected count | Memory |
|---------|------|----------------|--------|
| `hermes_cli.main gateway run --replace` | Main daemon (gateway) | 1 | ~170MB RSS |
| `hermes mcp serve` | MCP server per tool | 1+ (1 per open session/tool) | ~70MB RSS each |
| `hermes` (no subcommand) | Interactive CLI session | 0-1 per terminal | ~270MB RSS |
| `hermes chat` | One-shot query | 0-N transient | ~270MB RSS transient |

## Interpretation Rules

1. **Gateway** always shows `?` for TTY (it's a daemon) and `Ssl` state (sleeping, multi-threaded, locked)
2. **MCP serve** shows `pts/*` TTY if started from a terminal session; will persist until the parent session exits
3. **Multiple MCP serves is normal** — each Hermes interactive session opens its own MCP connections
4. **Gateway + cron tasks** — cron jobs run inside the gateway process, not as separate processes
5. **Older gateway instances** — `--replace` flag in the process args means it killed a previous instance and took over (normal)
