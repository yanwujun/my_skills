# Sing-box DNS Fix: Proxy Node Domain Resolution

## Problem

Sing-box times out resolving proxy node domains (e.g., `us-akko.july-wind.cc`) because DNS queries for these domains route through the proxy itself, creating a circular dependency.

Error:
```
lookup us-akko.july-wind.cc: (exchange4: context deadline exceeded | exchange6: context deadline exceeded)
```

## Fix: Three Targeted Changes to `dns` Section

### 1. Add a direct DNS server (no proxy detour)

```json
{
  "tag": "Public-DNS",
  "type": "udp",
  "server": "223.5.5.5",
  "server_port": 53
}
```

### 2. Add DNS rule for proxy node domains

Insert this rule BEFORE `GeoSite-CN` in `dns.rules`:

```json
{
  "action": "route",
  "domain_suffix": ["july-wind.cc"],
  "server": "Public-DNS",
  "strategy": "ipv4_only"
}
```

### 3. Enable DNS caching

```json
"disable_cache": false
```

## Complete `dns` Section (After Fix)

```json
{
  "dns": {
    "servers": [
      {
        "tag": "Local-DNS",
        "type": "udp",
        "server_port": 53,
        "server": "192.168.2.10"
      },
      {
        "tag": "Public-DNS",
        "type": "udp",
        "server": "223.5.5.5",
        "server_port": 53
      },
      {
        "tag": "Remote-DNS",
        "type": "tls",
        "detour": "🚀 节点选择",
        "server_port": 853,
        "server": "8.8.8.8"
      }
    ],
    "rules": [
      {
        "action": "route",
        "clash_mode": "direct",
        "server": "Local-DNS"
      },
      {
        "action": "route",
        "clash_mode": "global",
        "server": "Remote-DNS"
      },
      {
        "action": "route",
        "domain_suffix": ["july-wind.cc"],
        "server": "Public-DNS",
        "strategy": "ipv4_only"
      },
      {
        "action": "route",
        "rule_set": ["GeoSite-CN"],
        "server": "Local-DNS"
      },
      {
        "action": "route",
        "rule_set": ["GeoLocation-!CN"],
        "server": "Remote-DNS"
      }
    ],
    "disable_cache": false,
    "final": "Remote-DNS-Resolver",
    "strategy": "prefer_ipv4"
  }
}
```

## What Was NOT Changed

- `Local-DNS` (internal DNS, 192.168.2.10) — UNCHANGED
- `Remote-DNS` (foreign via proxy) — UNCHANGED
- `final` DNS server — UNCHANGED
- Internal/foreign split-routing architecture — UNCHANGED

Only added: one direct DNS server + one rule. Zero disruption to existing DNS flow.
