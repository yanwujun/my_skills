# Worked Example: MiMo Local API

Adding a local MiMo API endpoint as a custom provider.

## Endpoint

- URL: `http://192.168.2.18:8080/v1`
- API Key: provided by user
- Format: OpenAI-compatible (`/v1/chat/completions`, `/v1/models`)

## Available Models (from `/v1/models`)

| Model ID | Type | Use in OpenCode |
|---|---|---|
| mimo-v2.5-pro | chat | ✅ |
| mimo-v2.5 | chat | ✅ |
| mimo-v2-pro | chat | ✅ |
| mimo-v2-omni | chat | ✅ |
| mimo-v2-tts | TTS | ❌ skip |
| mimo-v2.5-tts | TTS | ❌ skip |
| mimo-v2.5-asr | ASR | ❌ skip |
| mimo-v2.5-tts-voiceclone | TTS | ❌ skip |
| mimo-v2.5-tts-voicedesign | TTS | ❌ skip |

## Final Config

### ~/.config/opencode/opencode.jsonc

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "mimo-local": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "MiMo 本地",
      "options": {
        "baseURL": "http://192.168.2.18:8080/v1",
        "apiKey": "sk-..."
      },
      "models": {
        "mimo-v2.5-pro": { "name": "MiMo v2.5 Pro" },
        "mimo-v2.5": { "name": "MiMo v2.5" },
        "mimo-v2-pro": { "name": "MiMo v2 Pro" },
        "mimo-v2-omni": { "name": "MiMo v2 Omni" }
      }
    }
  },
  "mcp": {
    "codegraph": {
      "type": "local",
      "command": ["codegraph", "serve", "--mcp"],
      "enabled": true
    }
  }
}
```

### ~/.local/share/opencode/auth.json

```json
{
  "deepseek": {
    "type": "api",
    "key": "sk-6b7...0ddc"
  },
  "mimo-local": {
    "type": "api",
    "key": "sk-136...068c"
  }
}
```

## Verification

```
$ opencode models mimo-local
mimo-local/mimo-v2-omni
mimo-local/mimo-v2-pro
mimo-local/mimo-v2.5
mimo-local/mimo-v2.5-pro

$ opencode providers list
┌  Credentials ~/.local/share/opencode/auth.json
│
●  DeepSeek api
│
●  mimo-local api
│
└  2 credentials
```

## Usage

```bash
opencode -m mimo-local/mimo-v2.5-pro    # CLI mode
# Or in TUI: /models → select mimo-local model
```
