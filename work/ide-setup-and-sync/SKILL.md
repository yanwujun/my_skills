---
name: ide-setup-and-sync
description: "Windows: install Claude Code/Pi CLI, sync Cursor to VS Code."
trigger: Use when installing Claude Code/Pi/coding CLI tools on Windows, syncing Cursor config to VS Code, or batch-migrating extensions between editors.
---

# IDE Setup & Config Sync

Install CLI coding agents on Windows from WSL and sync IDE configurations between Cursor and VS Code.

## 1. CLI Coding Agents — Install on Windows from WSL

Use `cmd.exe /c "npm install -g <package>"` to install into the Windows npm global directory.

| Agent | npm Package | Command |
|-------|------------|--------|
| Claude Code | `@anthropic-ai/claude-code` | `cmd.exe /c "npm install -g @anthropic-ai/claude-code"` |
| Pi | `@earendil-works/pi-coding-agent` | `cmd.exe /c "npm install -g @earendil-works/pi-coding-agent"` |

Pi is also available as a standalone winget package (`EarendilWorks.pi`), but the npm version is preferred for consistency with the Hermes WSL install.

After install, verify with `cmd.exe /c "where pi"` or `cmd.exe /c "where claude"`. If not in PATH, the user needs to restart their shell.

## 2. IDE Config Locations

| File | Cursor | VS Code |
|------|--------|---------|
| settings.json | `C:\Users\<user>\AppData\Roaming\Cursor\User\settings.json` | `C:\Users\<user>\AppData\Roaming\Code\User\settings.json` |
| keybindings.json | same directory | same directory |

Access from WSL as `/mnt/c/Users/<user>/AppData/Roaming/{Cursor,Code}/User/`.

## 3. Sync Cursor → VS Code

### Settings
Copy settings.json but strip Cursor-specific keys: `cursor.agent_layout_browser_beta_setting`, `cursor.cpp.disabledLanguages`, and any `cursor.*` prefixed setting.

### Keybindings
Direct copy is safe — Cursor keybindings are VS Code compatible.

### Extensions — Batch Migration
1. List both: `cmd.exe /c "cursor --list-extensions"` and `cmd.exe /c "code --list-extensions"`
2. Diff: `comm -23 <(cursor list | tr '[:upper:]' '[:lower:]' | sort) <(code list | tr '[:upper:]' '[:lower:]' | sort)`
3. Filter out `anysphere` prefixed extensions (Cursor vendor-specific)
4. Batch install: loop `cmd.exe /c "code --install-extension <id>"`

### Claude Code Extension for VS Code
`cmd.exe /c "code --install-extension anthropic.claude-code"` — works from WSL despite UNC path warning.

## 4. Claude Code 百炼配置（settings.json openai-compatible 已验证）

Claude Code **支持** openai-compatible provider。在 `C:/Users/<user>/.claude/settings.json` 写入：

```json
{
  "apiProvider": "openai-compatible",
  "openaiBaseURL": "https://ws-ihxin469w7ur3e6y.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
  "openaiApiKey": "sk-ws-...",
  "model": "qwen3.7-max"
}
```

验证：`cmd.exe /C "claude -p \"say hi in one word\""` 能正常返回即配置成功。会有模型名 warning（如 `deepseek-v4.1-flash` 不在 Claude Code 内置列表），不影响功能。

## 5. Pi 配置

Pi 认证用 `pi login openai`（交互式输入 API key），key 存入 `C:/Users/<user>/.pi/agent/auth.json`。环境变量方式无效。

验证：`cmd.exe /C "pi --provider openai --model qwen3.7-max -p \"say hi\""`。

## 6. Cursor 规则/技能迁移到 Claude Code

### 规则迁移
- Cursor `.cursor/rules/*.mdc`（YAML frontmatter + markdown body）→ Claude Code `C:/Users/<user>/.claude/CLAUDE.md`
- 只迁移 `alwaysApply: true` 的规则，合并为一个文件
- 提取方式：用 `grep -r "alwaysApply: true"` 找出所有始终生效规则，拼接内容写入 CLAUDE.md

### 技能迁移
- Cursor `.cursor/skills/<name>/SKILL.md` → Claude Code `C:/Users/<user>/.claude/commands/<name>.md`
- 每个 skill 一个 .md 文件，去掉 YAML frontmatter，保留纯 markdown body
- Claude Code 中用 `/skill-name` 调用
- 批量复制：`for d in ~/.cursor/skills/*/; do cp "$d/SKILL.md" ~/.claude/commands/"$(basename $d).md"; done`

## Pitfalls

- **Windows 环境变量不能从 WSL setx 写入。** `setx` 在 WSL 里执行会因 UNC 路径不支持而失败。正确方式：写 key 到 `/tmp/.keyfile`，然后用 PowerShell `Get-Content` 读 temp 文件写注册表 `HKCU\Environment`。
- **Pi 不读环境变量做认证。** `OPENAI_API_KEY` 等环境变量对 Pi 无效，必须 `pi login openai` 交互式输入，key 存 `.pi/agent/auth.json`。`setx` 设置的环境变量即使写入了 Pi 也不认。
- **用户偏好"告诉我哪里配置我自己去配置"。** 对于 API key、密码等敏感配置，告诉用户配置文件路径和字段名，让用户自己填写，不要尝试自动写入。
- Winget `EarendilWorks.pi` installs a standalone zip; npm `@earendil-works/pi-coding-agent` installs via Node and matches the Hermes WSL install — prefer npm.
- UNC path warning from `cmd.exe /c "npm ..."` when run from WSL is cosmetic, does not affect install.
- Batch extension installs timeout in one giant loop — set timeout 300s+ or run in background with notify.
- Cursor settings contain `//` comments which are valid in VS Code JSONC but fail strict JSON parsers — use `write_file` directly.
- Preserve Windows double-backslash paths (`D:\\baseSoftware\\...`) when copying settings — forward slashes break Java/Maven/SVN configs.
