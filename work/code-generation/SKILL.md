---
name: code-generation
description: "Code generation workflow: route coding tasks to external agents (Codex/OpenCode) when available, with documented fallback to direct tool writing."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [code-generation, coding-agent, codex, opencode, fallback]
    related_skills: [coding-agents]
---

# Code Generation Workflow

How to generate code for this user: route to the right tool, verify it can work, and fall back when it can't.

## Routing

| Task type | Tool | Command |
|---|---|---|
| Simple scripts, single-file, small utilities | Codex | `codex exec "..."` |
| Multi-file refactors, architecture, cross-module analysis | OpenCode | `opencode run "..."` |

## Pre-flight (mandatory before delegating)

Coding agent CLIs are independent of Hermes — their auth is NOT inherited from Hermes providers. Check before delegating:

```bash
# Codex — needs OPENAI_API_KEY
codex --version && [ -n "$OPENAI_API_KEY" ] && echo "OK" || echo "MISSING KEY"

# OpenCode
opencode auth list 2>&1 | head -5

# Claude Code
claude auth status --text 2>&1 | head -5
```

**Codex 401 = no key.** Codex hits `api.openai.com` directly. The 401 says `Missing bearer or basic authentication in header`. Fix: `export OPENAI_API_KEY=...`.

**Codex needs a git repo.** For scratch work: `mkdir -p dir && cd dir && git init` first.

## Fallback protocol

When both Codex and OpenCode are unavailable:

1. **Report** which agent failed and why (one line each)
2. **Fall back** to `write_file` + `patch` — write code directly
3. **Do NOT retry** the same agent expecting a different result

```
Codex → 401 (no API key)
OpenCode → timeout/blocked
→ Fallback: write_file directly
```

## Pitfalls

- Codex 401 is always auth — never a transient network error
- Hermes provider config (e.g. custom:192.168.x.x) does NOT apply to Codex CLI
- OpenCode with Chinese prompts triggers "Confusable Unicode" security scan and requires user approval — factor in the extra latency
- `opencode run` with `pty=true` may time out waiting for approval in non-interactive contexts
