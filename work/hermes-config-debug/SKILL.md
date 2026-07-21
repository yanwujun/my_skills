---
name: hermes-config-debug
description: "Diagnose and fix Hermes Agent configuration issues — OpenRouter key warnings, auxiliary provider resolution, provider connectivity, and common misconfigurations."
version: 1.0.0
category: devops
---

# Hermes Configuration Debugging

Trigger when: Hermes shows warnings/errors about providers, API keys, or configuration at startup or during sessions. Covers "Provider resolver returned an empty API key", auxiliary model failures, and provider misconfiguration.

## Diagnostic Toolkit

### 1. Check overall health

```bash
hermes doctor          # Full health check
hermes config check    # Config validation + env var status
hermes status --deep   # Deep component check
```

### 2. Trace the log for provider warnings

```bash
# Find OpenRouter/auxiliary warnings
grep -i "openrouter\|empty API key\|marking.*unhealthy\|OPENROUTER" ~/.hermes/logs/agent.log | tail -30

# See which session/model had the warning
grep "Provider resolver returned" ~/.hermes/logs/agent.log | tail -10
```

### 3. Check auxiliary provider status

```bash
grep -c 'provider: auto' ~/.hermes/config.yaml   # returns 0 = all configured
grep -A2 'provider: auto' ~/.hermes/config.yaml   # find which tasks are still auto
```

## "Provider resolver returned an empty API key" Warning

### Root cause

The status-bar warning "Provider resolver returned an empty API key. Set OPENROUTER_API_KEY" almost always comes from the **auxiliary client** (`agent/auxiliary_client.py`), NOT the main model. When auxiliary tasks are set to `provider: auto`, Hermes tries all available providers including OpenRouter. If `OPENROUTER_API_KEY` is empty or commented out in `.env`, it logs:

```
WARNING agent.auxiliary_client: Auxiliary: marking openrouter unhealthy for 60s (payment / credit error)
```

### The main model is usually fine

The warning does NOT mean your main model is broken. Check:
- The status bar shows your model running (e.g., `mimo-v2.5-pro │ 0/1M`)
- `hermes doctor` shows `✓ <YourProvider>` under API Connectivity

### All 14 auxiliary tasks that may be set to `auto`

| Task | Purpose |
|------|---------|
| `vision` | Image analysis |
| `web_extract` | Web page content extraction |
| `compression` | Conversation context compression |
| `skills_hub` | Skills market search |
| `approval` | Smart command approval |
| `mcp` | MCP tool operations |
| `title_generation` | Session title generation |
| `tts_audio_tags` | TTS audio tagging |
| `triage_specifier` | Task triage/specification |
| `kanban_decomposer` | Kanban task decomposition |
| `profile_describer` | Profile description |
| `curator` | Skill curation |
| `monitor` | System monitoring |
| `session_search` | Session search |

### Fix: Point all auxiliary tasks to your available provider

```bash
# Set ALL 14 auxiliary providers at once
for task in vision web_extract compression skills_hub approval mcp \
            title_generation tts_audio_tags triage_specifier \
            kanban_decomposer profile_describer curator monitor \
            session_search; do
    hermes config set "auxiliary.${task}.provider" deepseek
done
```

Then `/reset` to start a new session. The warning should disappear.

### Verification

```bash
grep -c 'provider: auto' ~/.hermes/config.yaml   # should return 0 (no auto found)
hermes doctor | grep -A3 "API Connectivity"      # should show your provider as ✓
```

## Support Files

- `references/diagnostic-output.md` — real log samples from this class of issue
- `references/profile-provider-empty-groups.md` — step-by-step fix for cloned profiles missing Web UI provider credentials
- `scripts/fix-auxiliary-providers.sh` — one-shot script to set all 14 auxiliary providers

## Profile Provider Not Showing in Web UI

### Symptom

`hermes profile list` shows a model for the profile, but the Web UI's Models page (`/hermes/models`) shows no available providers. The `groups` array for the profile is `[]` in the Web UI's `available-models` API response.

### Root cause

When profiles are cloned (`hermes profile create <name> --clone`), only `config.yaml` model settings are copied. The Web UI has its **own independent per-profile provider credential store** — `groups` in the API — and this is NOT touched by CLI profile operations. The CLI works because it reads config.yaml directly; the Web UI requires its own provider credential entry to be present.

**The Web UI and CLI have completely separate provider credential stores.** `hermes config set --profile` only updates CLI config.yaml; it has zero effect on the Web UI's provider list.

### Fix (manual via Web UI — PRIMARY, always works)

1. Open Web UI: `http://localhost:8648`
2. Switch to the target profile
3. Go to **Settings → Model Providers** (or the **Models** page)
4. Find the provider (e.g. DeepSeek), enter API key
5. Set default model (e.g. `deepseek-v4-pro`)
6. Save — refresh, model should appear

**All cloned profiles** (not just the one you notice) will have `groups: []`. After fixing one, check others — they all need the same treatment.

### Fix attempt (API/MCP — fails for non-default profiles)

The `hermes_studio_use_provider_add` MCP tool targets providers via profile-scoped auth. The MCP server is bound to the Hermes session's profile (usually default). When trying to add a provider for another profile (e.g. sdd-architect), the API returns **401 Unauthorized** — the default profile's token is rejected for cross-profile provider operations.

Even after switching the Web UI's active profile, restarting the target gateway, or passing `X-Hermes-Profile` headers, the MCP token stays bound to the default profile and the operation fails. This is a hard limitation of the current MCP auth model — the provider API is strictly token-scoped.

**Bottom line:** the manual Web UI approach is the reliable path for non-default profiles. Only use the MCP/API approach when the session itself runs as the target profile (uncommon in practice).

### Verification

```bash
# CLI side — model should be set in config
hermes config get --profile <name> model.default

# Web UI side — query available-models; check the target profile in the "profiles" array
# The target profile's "groups" should NOT be [] — it should have at least one provider entry
```

Then refresh Web UI. The Models page should now show the configured provider and model.

## Pitfalls

- **Profile cloning doesn't copy Web UI provider credentials.** After cloning, always add the provider via Web UI Settings (not CLI — `hermes config set --profile` only affects config.yaml, not the Web UI).
- **Adding providers for non-default profiles via MCP/API fails with 401.** The MCP server's token is bound to the default profile; cross-profile provider operations are rejected. Manual Web UI setup is the reliable path.
- **Don't confuse main-model issues with auxiliary issues.** If the status bar shows your model name and usage, the main model works.
- **`hermes config set` takes effect on next session**, not mid-session. `/reset` is required.
- **`hermes doctor` checks OpenRouter connectivity separately** — this is a connectivity test, not necessarily an error if you don't use OpenRouter.
- **MoA (mixture_of_agents) needs OPENROUTER_API_KEY** — if not needed, disable with `hermes tools disable moa`.
- **The warning may appear intermittently** because auxiliary tasks are called lazily (only when needed).
