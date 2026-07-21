# WSL Proxy, Windows CMD Access & Verification Checklist

> Absorbed from the archived `wsl-agent-tooling` skill. These patterns are
> environment-specific but useful for this dual-setup user.

## WSL Network Proxy (Pitfall 0)

This WSL environment sits behind an HTTP proxy at `http://127.0.0.1:8888`.
**Without proxy, all outbound connections time out** — `git clone`, `npm install`,
`curl`, `pip install`, everything. Always test connectivity before diagnosing
tool-specific failures:

```bash
# Quick proxy check
curl -sI --connect-timeout 5 https://github.com -o /dev/null -w "%{http_code}"
# → "000" = no connectivity → need proxy
# → "200" = already working

# Activate proxy for current command
export https_proxy=http://127.0.0.1:8888 http_proxy=http://127.0.0.1:8888
```

**Git with proxy:**
```bash
git clone -c http.proxy=http://127.0.0.1:8888 https://github.com/org/repo.git
# Or set per-repo:
git config http.proxy http://127.0.0.1:8888
```

**npm with proxy:**
```bash
https_proxy=http://127.0.0.1:8888 npm install -g package-name
```

**SSH is blocked:** SSH (port 22 and 443) is blocked by the proxy. Do NOT try
SSH-based git remotes (`git@github.com:...`) — they will hang forever. Use
HTTPS remotes + proxy + token.

Proxy env vars may be unset by default — never assume they're set.
Always `env | grep -i proxy` to check.

## Running WSL Tools from Windows cmd

When the user runs a WSL-installed command from Windows cmd/powershell and
gets `'command' 不是内部或外部命令`:

**Fix 1 — Use WSL directly from cmd:**
```cmd
wsl <command> [args]
```
Example: `wsl codegraph init -i`

**Fix 2 — Switch to WSL terminal:**
```bash
cd /mnt/d/path/to/project
<command> [args]
```

The WSL terminal has full access to the Windows filesystem via `/mnt/`.

## Verification Checklist

After installing a new tool, verify in this order:

1. **WSL**: `which <command>` — binary accessible in WSL
2. **Hermes**: `hermes mcp test <name>` — MCP server connects and discovers tools
3. **Hermes**: `hermes config check` — YAML not corrupted
4. **Cursor**: Open `mcp.json` and verify JSON validity
5. **Cursor**: Check `.cursor/skills/` has junctions for skill-based plugins
6. **User**: Remind them to restart Cursor / do `/reset` in Hermes for changes to take effect
