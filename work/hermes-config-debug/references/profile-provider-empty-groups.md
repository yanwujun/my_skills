# Profile Provider Configuration: Diagnostic Example

## Scenario

User cloned profiles from default, but the Web UI doesn't show any provider for them.

## Observed state

```
$ hermes profile list
Profile          Model              Gateway      Alias
 ───────────────    ───────────────    ───────────    ───────────
 ◆default         deepseek-v4-pro     running      —
  econ-master     deepseek-v4-pro     stopped      econ-master
  sdd-architect   deepseek-v4-pro     running      sdd-architect
```

All 7 non-default profiles have model set in config.yaml but show nothing in Web UI.

## Web UI provider state (from available-models API)

```json
{
  "profiles": [
    {
      "profile": "default",
      "groups": [
        {"provider": "deepseek", "api_key": "sk-placeholder", ...},
        {"provider": "custom:192.168.2.18:8080", ...}
      ]
    },
    {
      "profile": "sdd-architect",
      "default": "deepseek-v4-pro",
      "default_provider": "deepseek",
      "groups": []   // ← EMPTY
    },
    // ... all other cloned profiles also have groups: []
  ]
}
```

## Root cause analysis

**Two independent provider stores:**
- **CLI** reads `config.yaml` → `model.default: deepseek-v4-pro`, `model.provider: deepseek` ✓
- **Web UI** has its own per-profile credential store → `groups: []` ✗

`hermes profile create --clone` copies config.yaml but does NOT touch the Web UI's credential store. The CLI works fine because it only needs config.yaml; the Web UI needs both.

## Fix attempts

### Manual Web UI (SUCCESS)

1. Open Web UI → switch to target profile
2. Settings → Model Providers → DeepSeek → enter API key
3. Set default model → Save
4. Result: Models page shows provider and model immediately

### API/MCP (FAILED for non-default profile)

Attempted `hermes_studio_use_provider_add(profile="sdd-architect", ...)` — returned **401 Unauthorized**. The MCP server uses the default profile's token; the Web UI rejects cross-profile provider operations. Even after:
- Switching active profile to sdd-architect
- Restarting sdd-architect gateway
- Passing X-Hermes-Profile header

All returned 401. The provider API is strictly token-scoped — only `hermes_studio_use_provider_add` (no profile) for the default profile works.

## Key insight

**Manual Web UI setup is the ONLY reliable path for non-default profiles.** `hermes config set --profile <name>` only updates config.yaml — the Web UI provider list (`groups`) is completely separate and must be configured in the UI.
