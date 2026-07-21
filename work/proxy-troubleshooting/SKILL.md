---
name: proxy-troubleshooting
description: "Diagnose and fix proxy connectivity issues in WSL + Windows hybrid environments with Sing-box, Proxifier, and AI tools (Cursor, Hermes)."
version: 1.0.0
category: devops
---

# Proxy Troubleshooting (WSL + Windows Hybrid)

Trigger when: AI tools (Cursor, Hermes, etc.) running on Windows through Proxifier → Sing-box SOCKS5 proxy show connection errors (HTTP 464, TLS abort, "general SOCKS server failure"). Also when the proxy seems to work for some apps but not others, or when connections succeed intermittently.

## Quick Diagnostic Flow

### Step 1: Check Proxifier Logs

Proxifier logs tell you immediately whether it's the proxy or the app:

```
# Healthy: connections have reasonable lifetime and byte counts
cursor.exe - 127.0.0.1:8888 close, 2676 bytes sent, 4985 bytes received, lifetime 2s

# Dead: lifetime <1 sec, fixed 343 sent / 39 received = SOCKS5 error response
cursor.exe - 127.0.0.1:8888 close, 343 bytes sent, 39 bytes received, lifetime <1 sec
cursor.exe - api2.cursor.sh:443 error : Could not connect through proxy - general SOCKS server failure
```

**343 sent / 39 received with lifetime <1s** is the fingerprint of a SOCKS5 rejection. The proxy is up but refusing connections.

### Step 2: Isolate — Test Proxy from WSL

```bash
# Test if the proxy itself can reach targets (bypasses the Windows app)
curl -x socks5h://127.0.0.1:8888 -s -o /dev/null -w "HTTP %{http_code} TLS %{time_appconnect}s\n" --connect-timeout 10 https://api.deepseek.com/v1/models

# If this works but Proxifier fails → the proxy intermittently rejects high-concurrency connections
# If this also fails → proxy outbound is broken entirely
```

### Step 3: Check Sing-box Logs

```bash
# On Windows, check Sing-box's terminal output or log file
# Look for DNS timeout errors on node/airport domains:
# "lookup us-akko.july-wind.cc: context deadline exceeded"
```

## Sing-box DNS Deadlock (Most Common Root Cause)

### Symptom

```
error: connection: open connection to <target>:443 using outbound/vless[US-REALITY]:
lookup <node-domain>: (exchange4: context deadline exceeded | exchange6: context deadline exceeded)
```

### Root Cause: Chicken-and-Egg DNS

When Sing-box DNS `final` points to a server that routes through the proxy, but the proxy node domains themselves need DNS resolution:

```
dns.final = Remote-DNS-Resolver  (8.8.8.8 via 🚀 节点选择)
                                  ↓
                     needs to connect to proxy first
                                  ↓
                     proxy needs DNS for node domain (us-akko.july-wind.cc)
                                  ↓
                     falls to dns.final → 8.8.8.8 via proxy → 💀 DEADLOCK
```

Three contributing factors:
1. **`disable_cache: true`** — every connection triggers fresh DNS lookup, amplifying the deadlock
2. **Airport domains not in any DNS rule** — custom domains like `july-wind.cc` aren't in `GeoSite-CN` or `GeoLocation-!CN`, so they fall through to `final`
3. **DNS servers with `detour` through proxy** — e.g., `PUBLIC_LOCAL-Resolver` with `detour: "🚀 节点选择"` also deadlocks

### Fix (Minimal, Preserves Split-DNS Architecture)

Add ONE rule before the `GeoLocation-!CN` rule in `dns.rules`:

```json
{
  "action": "route",
  "domain_suffix": ["july-wind.cc"],
  "server": "Local-DNS",
  "strategy": "ipv4_only"
}
```

Also change `dns.disable_cache` from `true` to `false`.

This preserves the existing internal/external DNS split — airport domains resolve via local DNS (no proxy dependency), all other foreign domains still go through Remote-DNS.

### Pitfalls

- **Don't change `dns.final` from Remote-DNS to Local-DNS** unless the user doesn't care about DNS anti-pollution for foreign domains. The minimal fix is just adding the airport domain rule.
- **Don't add `detour: proxy` to any DNS server used for airport domains** — that recreates the deadlock.
- **`disable_cache: true` amplifies DNS deadlocks** — every connection retries the failing DNS query.
- **The fix goes in `dns.rules`, not `route.rules`** — these are different sections. DNS rules control which DNS server resolves which domain; route rules control which outbound carries the traffic.

## NPM/Pnpm Registry Issues via Proxy

When `pnpm install` or `npm install` produces repeated ECONNRESET from `registry.npmjs.org` while other HTTP traffic works, the proxy is dropping the connections (Sing-box handles many small npm tarball downloads poorly).

**Workaround: switch to npmmirror (China mirror, no proxy needed):**

```bash
pnpm config set registry https://registry.npmmirror.com
```

For one-off use: `pnpm install --registry https://registry.npmmirror.com`

## Testing After Fix

1. Restart Sing-box
2. Check Proxifier logs for `general SOCKS server failure` — should be gone
3. Test Cursor/Hermes with a streaming request — should complete without TLS abort or HTTP 464
