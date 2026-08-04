---
name: coding-agent-hermes-config
description: "Configure Hermes to allow coding agents (Codex/OpenCode/Claude Code) to run without approval timeouts, plus free-model fallback and auth setup."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [coding-agent, hermes-config, approval, opencode, codex, claude-code]
    related_skills: [coding-agents, hermes-agent]
---

# Coding Agent Hermes Configuration

When running external coding agents (`opencode run`, `codex exec`, `claude`) from within Hermes, the agent's write operations trigger Hermes security approval dialogs. Default settings cause these to fail silently.

## Fix: Approval timeout + allowlist

```bash
# 1. Increase timeout from 60s → 300s (coding agent runs can take minutes)
hermes config set approvals.timeout 300

# 2. Whitelist coding agent CLI commands so they skip approval popups
hermes config set command_allowlist '["opencode run", "codex exec", "claude"]'
```

**Without this**, commands that modify files get killed with:
```
BLOCKED: Command timed out without user response.
The user has NOT consented to this action.
```

Chinese text in prompts triggers an additional "Confusable Unicode" security scan — the allowlist (step 2) resolves this too.

## OpenCode: free model fallback

When paid API keys are expired (DeepSeek 401, MiMo timeout), OpenCode's free tier works:

```bash
# Check available free models
opencode models | grep opencode/
# → opencode/deepseek-v4-flash-free, opencode/mimo-v2.5-free, etc.

# One-shot with free model
opencode run "task" --model opencode/deepseek-v4-flash-free

# Set as default: add to ~/.config/opencode/opencode.jsonc
#   "model": "opencode/deepseek-v4-flash-free"
```

## Codex: auth required

Codex needs `OPENAI_API_KEY` or `codex login`. Without it, all commands 401.

```bash
export OPENAI_API_KEY="sk-..."
# or
echo "$OPENAI_API_KEY" | codex login --with-api-key

# Verify: codex doctor
```

## OpenCode: verify auth

```bash
opencode auth list          # shows configured providers
opencode models             # shows all available models
```

## Verification

After config, test with a write operation:

```bash
cd /tmp/test && git init
opencode run 'create a file hello.txt with content "hello world"'
```

Should succeed without approval dialog.
