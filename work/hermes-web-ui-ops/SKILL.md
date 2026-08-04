---
name: hermes-web-ui-ops
description: "Operate and troubleshoot the built-in Hermes Studio Web UI (hermes-web-ui npm service, port 8648) — start/stop/status, stale PID recovery, autostart gap, proxy-safe verification, login reset, and self-update."
version: 1.0.0
category: devops
---

# Hermes Studio Web UI Operations

Trigger when: user says "hermesui 无法访问" / Web UI won't open / login lost / want to update the UI. Governs the **built-in Hermes Studio web UI** (`hermes-web-ui` npm package, default port **8648**, default login `admin / 123456`). This is a SEPARATE service from:
- `hermes serve` — JSON-RPC/WebSocket backend (port 9119) for desktop/remote clients
- Open WebUI frontend (port 3000 + Hermes API server 8642) — documented in the hermes-deployment skill

## Service model

- Runs as a standalone node daemon managed by the `hermes-web-ui` CLI (bin from the n-managed node tree: `export PATH=~/.local/n/bin:$PATH`).
- State & logs live in `~/.hermes-web-ui/`: `server.pid`, `server.log`, `config.json`, `cache/`.
- The gateway does NOT pull it up — a running gateway + 8648 down means the UI died or never started.
- MCP blocks in `config.yaml` (`hermes-studio-api` / `-devices` / `-use`) point at `HERMES_WEB_UI_URL=http://127.0.0.1:8648`; when 8648 is down, the Studio MCP tools fail too.

## Commands

```bash
export PATH=~/.local/n/bin:$PATH
hermes-web-ui status               # Reads server.pid — CAN LIE if the process died (see stale PID)
hermes-web-ui start --no-open      # Start (default port 8648). --no-open skips browser launch.
hermes-web-ui stop                 # Stop; also clears a stale pidfile
hermes-web-ui restart              # Restart
hermes-web-ui reset-default-login  # Recreate admin / 123456
hermes-web-ui update               # Self-update to latest version and restart
```

## Diagnostic path (worked example Aug 2026)

Symptom: browser can't reach `localhost:8648`.

1. `hermes-web-ui status` → claims "running (PID: N)" but the port is dead → **stale pidfile**: process died (crash/reboot) leaving `server.pid` behind. `status`/`start` trust the file, so `start` refuses with `"already running (PID: N)"`.
2. Confirm dead: `ps -p N -o pid,etime,cmd --no-headers` → empty; `ss -tlnp | grep 8648` → nothing.
3. Fix: `hermes-web-ui stop` (cleans pidfile) → `hermes-web-ui start --no-open` → new PID.
4. Verify: `ss -tlnp | grep 8648` shows LISTEN; `curl -s --noproxy '*' -o /dev/null -w '%{http_code}' http://127.0.0.1:8648/` → 200; page HTML contains `<title>Hermes Studio</title>`; LAN IP `http://<host>:8648` also 200.

## Pitfalls

- **Stale pidfile is the classic "already running" lie.** Always cross-check with `ss -tlnp` + `ps -p <pid>` before believing `status`.
- **Proxy interference on loopback checks.** With `http_proxy` set (e.g. sing-box on 127.0.0.1:8888), plain `curl http://127.0.0.1:8648/` goes THROUGH the proxy and returns a misleading `502 Bad Gateway` even when nothing listens (or 200 from the proxy's own error page). Always use `curl --noproxy '*'` for loopback health checks in this environment.
- **No autostart.** Rebooting the machine brings up the gateway but NOT the web UI — it stays down until started manually (this is exactly how the Aug 2026 outage happened: PID from weeks ago, server.log stopped, nobody restarted it). If the UI must survive boots, wire `hermes-web-ui start --no-open` into systemd/crontab/Task Scheduler.
- **systemd --user 托管方案(已验证 Aug 2026):** 网关不拉起 UI 是设计行为(两者独立服务,gateway 无拉起 8648 的逻辑)。想开机自启,建 `~/.config/systemd/user/hermes-web-ui.service`,注意两点:(1) **不要用 `Type=forking` + CLI start**——daemon 崩溃后 pidfile 残留,Restart=always 会卡 "already running" 死循环。用 `Type=simple` 直接前台托管 server 本体: `ExecStart=/home/administrator/.hermes/node/bin/node /home/administrator/.hermes/node/lib/node_modules/hermes-web-ui/dist/server/index.js`(用 ~/.hermes/node 这套,与 CLI daemon 实际运行一致;双 node 机器勿用 PATH 里的 ~/.local/n 版本,先 `ps -p $(cat ~/.hermes-web-ui/server.pid)` 确认真实入口)。(2) `ExecStartPost=/bin/sh -c 'echo $MAINPID > /home/administrator/.hermes-web-ui/server.pid'` 同步 PID,保住 CLI status/stop 兼容。bootstrap 需 ~6s 才监听 8648,健康检查要等。升级: `hermes-web-ui update` 装新包后必须 `systemctl --user restart hermes-web-ui`(update 自带 restart 是 CLI 语义,spawn 的 detached 进程绕过 systemd,不 restart 会 PID 错乱/端口冲突)。
- **server.log is the state marker.** Last-write timestamp of `~/.hermes-web-ui/server.log` tells you when the service last did anything — a stale date confirms the daemon is gone before you even check ports.
- **Update notices** appear in server.log (`Update available: X → Y`); apply with `hermes-web-ui update`.
- **Login lockouts**: `.login-lock.json` in `~/.hermes-web-ui/` tracks IP-based login locks; `hermes-web-ui clear-login-locks` clears them, `reset-default-login` resets credentials to admin/123456.
