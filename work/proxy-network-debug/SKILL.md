---
name: proxy-network-debug
description: "Diagnose and fix proxy/DNS issues affecting AI tools (Cursor, Hermes, etc.) in WSL/Windows hybrid environments — Sing-box, Clash, V2Ray, Proxifier."
version: 1.0.0
category: devops
---

# Proxy Network Debugging (WSL + Windows)

Trigger when: AI tools (Cursor, Hermes, etc.) report connection errors through a local proxy stack, especially in Chinese network environments with Proxifier + Sing-box/Clash/V2Ray.

## Symptom Recognition

### Cursor / AI Tool Symptoms
- `ConnectError: [unknown] HTTP 464`
- `ConnectError: [aborted] Client network socket disconnected before secure TLS connection was established`
- First message succeeds, subsequent messages fail (streaming connection killed)

### Proxifier Symptoms
- `general SOCKS server failure`
- Connections with `lifetime <1 sec`, fixed byte patterns (343 sent / 39 received = SOCKS5 error response)

### Sing-box / Proxy Symptoms
- `lookup <node-domain>: context deadline exceeded`
- `exchange4: context deadline exceeded | exchange6: context deadline exceeded`

## Diagnostic Path (top to bottom)

1. **Curl direct test** from WSL: bypass the proxy stack entirely
   ```bash
   curl -s -o /dev/null -w "HTTP %{http_code}\n" --connect-timeout 10 https://api.deepseek.com/v1/models
   ```

2. **Curl through proxy** from WSL: test proxy chain
   ```bash
   curl -x socks5h://127.0.0.1:8888 -s -o /dev/null -w "HTTP %{http_code}\n" --connect-timeout 10 https://api.deepseek.com/v1/models
   ```

3. **Check proxy logs** (Sing-box): look for DNS timeout errors on node domains

4. **Test DNS directly** against each DNS server:
   ```python
   import socket, struct, random
   # Build and send DNS query to target server, check response
   ```

## Root Cause: DNS Chicken-and-Egg

Proxy node domains (e.g. `us-akko.july-wind.cc`) need DNS resolution, but if the DNS server routes through the proxy itself, it creates a circular dependency:

```
resolve node domain → DNS server → needs proxy → needs node domain → deadlock
```

This happens when:
- `dns.final` points to a server with `detour: proxy`
- The proxy node domain isn't in any DNS rule, so it falls through to `final`
- `disable_cache: true` makes it trigger on every connection

## Fix Pattern (Sing-box)

### 1. Add a direct (non-proxy) DNS server

In `dns.servers`, create a new entry with NO `detour`:

```json
{
  "tag": "Public-DNS",
  "type": "udp",
  "server": "223.5.5.5",
  "server_port": 53
}
```

### 2. Route proxy node domains to it

In `dns.rules`, add BEFORE other catch-all rules:

```json
{
  "action": "route",
  "domain_suffix": ["july-wind.cc"],
  "server": "Public-DNS",
  "strategy": "ipv4_only"
}
```

### 3. Enable DNS caching

Set `"disable_cache": false` in `dns` section — reduces repeated lookups and narrows the failure window.

### Key Principle

**Do NOT change the overall split-routing architecture.** The fix is a targeted addition:
- Internal domains → `Local-DNS` (unchanged)
- Proxy node domains → `Public-DNS` (NEW, no proxy detour)
- Foreign domains → `Remote-DNS` via proxy (unchanged)

## SSH over HTTP Proxy (nc ProxyCommand)

When direct port 22 connections are blocked but HTTP/HTTPS traffic works through the proxy, use `nc` (netcat) to tunnel SSH:

```bash
# Test (one-off):
ssh -o "ProxyCommand nc -X connect -x 127.0.0.1:8888 %h %p" -T git@github.com

# Permanent (~/.ssh/config):
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    ProxyCommand nc -X connect -x 127.0.0.1:8888 %h %p
```

**How it works:** `nc -X connect` wraps the SSH TCP stream inside an HTTP CONNECT request tunneled through the proxy (`-x`). The proxy handles the outbound connection; SSH thinks it's talking directly. Works with any HTTP/HTTPS proxy (sing-box, Clash, V2Ray in HTTP mode).

**Diagnostics:** `ssh -v git@github.com` will show `debug1: Connecting to github.com [20.205.243.166] port 22.` followed by timeout if the proxy isn't working. With ProxyCommand, you'll see `debug1: Executing proxy command` instead.

- **Proxifier is rarely the culprit.** The Proxifier log showing `general SOCKS server failure` means the downstream proxy (Sing-box) rejected the connection. Fix the proxy, not Proxifier.
- **WSL can reach DNS servers that Windows/Sing-box cannot.** Always test DNS from the proxy's network context, not from WSL.
- **`dns.final` is the default, not a fallback.** It's used when no rule matches — not "if the first server fails, try this one."
- **`route.default_domain_resolver` vs `dns.rules`.** These are different layers. `dns.rules` governs application DNS queries; `default_domain_resolver` governs Sing-box's own outbound resolution. Both matter.
- **Changing DNS architecture (like `final`) is unnecessary.** The problem is a missing rule, not wrong architecture. Keep internal/foreign split intact.
- **Restart required.** Sing-box must be restarted after DNS config changes. Saving in the web UI is not enough.

## gh CLI Install Without Sudo

```bash
curl -fsSL "https://github.com/cli/cli/releases/download/v2.63.2/gh_2.63.2_linux_amd64.tar.gz" -o /tmp/gh.tar.gz
tar -xzf /tmp/gh.tar.gz -C /tmp
cp /tmp/gh_2.63.2_linux_amd64/bin/gh ~/.local/bin/gh
chmod +x ~/.local/bin/gh
```

## References

- `references/singbox-dns-fix.md` — Full Sing-box DNS config example with the fix applied
