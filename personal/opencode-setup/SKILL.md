---
name: opencode-setup
description: Configure OpenCode — custom providers, MCP servers, agents, auth, and troubleshooting.
triggers:
  - opencode config
  - opencode provider
  - opencode model
  - opencode auth
  - add provider to opencode
  - custom model opencode
---

# OpenCode Configuration

## File Locations

| What | Path |
|---|---|
| Project config | `./opencode.jsonc` (per-project) or `~/.config/opencode/opencode.jsonc` (global) |
| Auth/credentials | `~/.local/share/opencode/auth.json` |
| Logs | `~/.local/share/opencode/log/` |
| Database | `~/.local/share/opencode/opencode.db` |
| Data dir | `~/.local/share/opencode/` |
| Cache | `~/.cache/opencode/` |

## Adding a Custom OpenAI-Compatible Provider

### Step 1: Update opencode.jsonc

Add a `provider` block. Use `@ai-sdk/openai-compatible` for `/v1/chat/completions` endpoints, `@ai-sdk/openai` for `/v1/responses`.

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "my-provider": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Display Name",
      "options": {
        "baseURL": "http://HOST:PORT/v1",
        "apiKey": "sk-..."  // optional if using auth.json
      },
      "models": {
        "model-id": {
          "name": "Model Display Name",
          "limit": {             // optional
            "context": 200000,
            "output": 65536
          }
        }
      }
    }
  }
}
```

**Key fields:**
- `npm`: `@ai-sdk/openai-compatible` for standard `/v1/chat/completions`. `@ai-sdk/openai` for `/v1/responses`. Can override per-model via `provider.npm`.
- `options.baseURL`: Full URL including `/v1`.
- `options.apiKey`: Can use `{env:VAR_NAME}` syntax.
- `options.headers`: Custom headers dict.
- `limit.context` / `limit.output`: Token limits. Standard providers auto-fetch from models.dev; custom providers need these set manually.

### Step 2: Add credentials to auth.json

```json
{
  "my-provider": {
    "type": "api",
    "key": "sk-..."
  }
}
```

Provider ID in auth.json **must match** the key in opencode.jsonc's `provider` block.

### Step 3: Verify

```bash
opencode models                    # list all models
opencode models my-provider        # list models for specific provider
opencode providers list            # show configured credentials
opencode debug config              # show resolved config
opencode debug v2                  # show v2 catalog and built-in plugins
```

## Pitfalls

- **`opencode providers login <url>` is interactive-only** — it prompts for input and cannot be scripted. Manually edit `auth.json` + `opencode.jsonc` instead.
- **Provider ID mismatch**: the key in `opencode.jsonc` → `provider.<id>` must match `auth.json` → `<id>`. Case-sensitive.
- **Custom providers need `limit` fields** set manually — standard providers auto-fetch from models.dev, but custom endpoints won't have that metadata.
- **TTS/ASR/embedding models** from an endpoint should NOT be listed in the `models` block — only chat/completion models. Listing non-chat models causes them to appear in `/models` but fail at runtime.

## Useful Debug Commands

```bash
opencode debug config       # resolved configuration
opencode debug v2           # v2 catalog, built-in plugins, provider registry
opencode debug paths        # all data/config/cache paths
opencode debug info         # system info
```

## References

- See `references/custom-provider-example.md` for a complete worked example with MiMo local API.
