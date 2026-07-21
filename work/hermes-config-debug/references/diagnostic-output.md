# Real diagnostic output examples

## Log sample: auxiliary_client OpenRouter failures

When OPENROUTER_API_KEY is not set and auxiliary tasks use `auto`:

```
2026-06-24 09:12:33,092 WARNING agent.auxiliary_client: Auxiliary: marking openrouter unhealthy for 60s (payment / credit error). Subsequent auxiliary calls will skip it until 09:13:33.
2026-06-24 09:12:33,095 WARNING agent.auxiliary_client: Auxiliary: marking openrouter unhealthy for 60s (payment / credit error). Subsequent auxiliary calls will skip it until 09:13:33.
```

Note: multiple failures within the same second (many auxiliary tasks all try OpenRouter simultaneously).

## Status bar during session

```
⚠️  Provider resolver returned an empty API key. Set OPENROUTER_API_KEY or run: hermes setup
 ⚕ mimo-v2.5-pro │ 158K/1M │ [██░░░░░░░░] 16% │ 36m │ ⏲ 18m 40s │ ✓ 16m
```

Key observation: the model IS running (mimo-v2.5-pro shows usage). The warning is about OpenRouter, not the main model.

## hermes doctor output

```
◆ API Connectivity
  ⚠ OpenRouter API (not configured)
  ✓ DeepSeek
```

OpenRouter not configured is expected if you don't use it.

## hermes config check output

```
○ OPENROUTER_API_KEY → vision_analyze, mixture_of_agents
✓ DEEPSEEK_API_KEY
```

Shows which features depend on OPENROUTER_API_KEY.

## Before fix: auxiliary providers all auto

```
auxiliary:
  vision:
    provider: auto       # ← triggers OpenRouter probe
  web_extract:
    provider: auto
  compression:
    provider: auto
  ... (11 more)
```

## After fix: all pointed to available provider

```bash
$ grep -c 'provider: auto' ~/.hermes/config.yaml
0
```
