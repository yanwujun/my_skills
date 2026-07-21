---
name: coding-agents
description: "Delegate coding tasks to external AI coding agents: Claude Code, Codex CLI, OpenCode CLI, and Cursor Agent. Covers one-shot mode, interactive sessions, PR review, and parallel work patterns."
version: 1.0.0
author: Hermes Agent (consolidated)
license: MIT
metadata:
  hermes:
    tags: [coding-agent, claude, codex, opencode, cursor, automation, PR, refactoring]
    related_skills: [hermes-agent]
---

# External Coding Agent Integration

Delegate coding, refactoring, and code review to external AI coding agent CLIs. Four supported backends — pick the one available on the system. Each supports one-shot (print mode) and interactive (TUI) patterns.

## Agent Comparison

| Feature | Claude Code | Codex CLI | OpenCode CLI | Cursor Agent |
|---------|------------|-----------|--------------|--------------|
| One-shot (`-p`) | ✅ `claude -p "..."` | ✅ `codex exec "..."` | ✅ `opencode run "..."` | ❌ no equivalent |
| JSON output | ✅ `--output-format json` | ❌ | ✅ `--format json` | ❌ |
| Interactive TUI | ✅ tmux-recommended | ✅ pty=true | ✅ pty=true | ✅ pty=true (WSL-limited) |
| PR review | ✅ built-in | ✅ via worktree | ✅ `opencode pr N` | ❌ headless |
| Parallel work | ✅ tmux multi-session | ✅ git worktrees | ✅ separate workdirs | ❌ |
| Needs git repo | ❌ | ✅ required | ❌ | N/A |
| WSL/Windows support | ✅ WSL | ✅ WSL | ✅ WSL | ✅ Windows-native |

## Prerequisites (all agents)

Verify CLI availability and auth before delegating:

### Golden rule: analyze first, delegate second

Before sending a code-analysis task to any external agent, FIRST use local tools to understand the codebase structure:

1. **CodeGraph** (MCP) — `mcp_codegraph_codegraph_files()` lists project tree; `codegraph_context()` provides symbol/architecture overview
2. **Understand-Anything skills** — `understand` skill generates an interactive knowledge graph of the codebase
3. **Direct exploration** — `terminal` or `search_files` for quick project layout (`find ... -type d | sort`, `ls -1`, etc.)

Then feed that structured analysis as context to the external agent via `-f` / `--file` or inline in the prompt. This avoids the agent wasting time/tokens re-discovering project layout and prevents the "I don't know this project" cold-start problem.

PITFALL: Jumping directly to an external agent with a bare project path for "analyze this project" is expensive and wasteful — the agent re-discovers structure that local tools already know. Use local structural analysis FIRST, delegate DEEPER analysis SECOND.

```bash
# Claude Code
npm install -g @anthropic-ai/claude-code && claude --version
claude auth status --text  # or set ANTHROPIC_API_KEY

# Codex
npm install -g @openai/codex && codex --version
# Auth via OPENAI_API_KEY or codex OAuth

# OpenCode
npm install -g opencode-ai@latest && opencode --version
opencode auth list  # or set DEEPSEEK_APIKEY/OPENROUTER_API_KEY

# Cursor Agent (WSL→Windows)
cmd.exe /c "d:\path\to\cursor\resources\app\bin\cursor.cmd --version"
# Must cd to Windows drive first to avoid UNC path error
```

---

## Section A: Claude Code

Anthropic's autonomous coding agent. Full TUI with slash commands, MCP support, and subagents.

### Print mode (preferred for automation)

```bash
terminal(command="claude -p 'Add error handling to API calls' --allowedTools 'Read,Edit' --max-turns 10", workdir="/project", timeout=120)
```

Structured JSON: `--output-format json` returns `session_id`, `num_turns`, `total_cost_usd`, `usage`.

### Interactive mode (via tmux)

```bash
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")
terminal(command="tmux send-keys -t claude-work 'cd /project && claude' Enter")
terminal(command="sleep 5 && tmux send-keys -t claude-work 'Refactor auth module' Enter")
terminal(command="tmux capture-pane -t claude-work -p -S -50")
```

### Dialog handling

Claude Code shows trust and permissions dialogs on first launch:
- Trust dialog: default is "Yes" — just send Enter
- Permissions dialog (`--dangerously-skip-permissions`): default is "No" — must send Down then Enter

### Settings hierarchy

1. CLI flags > `.claude/settings.local.json` > `.claude/settings.json` > `~/.claude/settings.json`
2. CLAUDE.md: `~/.claude/CLAUDE.md` (global) > `./CLAUDE.md` (project) > `.claude/CLAUDE.local.md` (personal)

### Session commands

| Command | Purpose |
|---------|---------|
| `/compact` | Compress context to save tokens |
| `/review` | Code review of current changes |
| `/plan` | Enter plan mode |
| `/model` | Switch model mid-session |
| `/exit` or Ctrl+D | End session |

### Key flags

`-p/--print` (one-shot), `-c/--continue` (resume), `--model`, `--max-turns`, `--allowedTools`, `--dangerously-skip-permissions`, `--output-format json`, `--bare` (skip plugins/hooks/MCP).

**References:** `references/claude-code/llm-gateway-deepseek-caveats.md` — LLM gateway investigation notes.

---

## Section B: Codex CLI

OpenAI's autonomous coding agent CLI.

### One-shot

```bash
terminal(command="codex exec 'Add dark mode toggle'", workdir="~/project", pty=true)
```

Codex requires a git repo. For scratch work: `cd $(mktemp -d) && git init && codex exec 'Build snake game'`.

### Key flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution |
| `--full-auto` | Sandboxed, auto-approves file changes |
| `--yolo` | No sandbox, no approvals |

### PR review

```bash
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")
terminal(command="codex exec 'Review PR #86: git diff main...origin/pr/86'", workdir="~/project", pty=true)
```

### Parallel issue fixing

```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
terminal(command="codex --yolo exec 'Fix issue #78'", workdir="/tmp/issue-78", background=true, pty=true)
```

### Rules

- Always use `pty=true` — Codex hangs without a PTY
- Git repo required — use `mktemp -d && git init` for scratch
- Use `exec` for one-shots
- Background for long tasks, monitor with `process` tool

---

## Section C: OpenCode CLI

Provider-agnostic open-source coding agent. Supports `--agent plan` for analysis-only mode.

### One-shot

```bash
terminal(command="opencode run 'Add retry logic to API calls'", workdir="~/project")
terminal(command="opencode run 'Analyze project structure' --agent plan", workdir="~/project")
```

### Workspace creation (setting up analysis directories)

```bash
# Use opencode run to create workspace files/directories (not bare mkdir)
terminal(command="opencode run 'Create a readme.md recording project paths and purpose'",
  workdir="/path/to/workspace", pty=true, timeout=120)

# Attach related projects so OpenCode understands the codebase context
terminal(command="opencode run 'List workspace contents' -f /path/to/proj1 -f /path/to/proj2",
  workdir="/path/to/workspace", pty=true, timeout=120)
```

### Web UI (persistent workspace)

```bash
# Start from the workspace directory so the web UI shows that project
terminal(command="opencode web --port 4096", workdir="/path/to/workspace", background=true)
# Access at http://127.0.0.1:4096/Lw/session
# Kill old instance if port in use: kill $(lsof -ti:4096)
```

### Interactive (background)

```bash
terminal(command="opencode", workdir="~/project", background=true, pty=true)
process(action="submit", session_id="<id>", data="Implement OAuth refresh")
process(action="poll", session_id="<id>")
process(action="write", session_id="<id>", data="\x03")  # Ctrl+C to exit
```

### Key flags

| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot |
| `--agent plan` | Analysis only, no file changes |
| `--model provider/model` | Force specific model |
| `--thinking` | Show model thinking |
| `--file path` / `-f` | Attach file context |

### PR review

```bash
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

### Pitfalls

- Enter may need to be pressed twice to submit in TUI
- `opencode auth login` TUI is hard to automate — use env vars instead
- `/exit` is NOT a valid command — use Ctrl+C
- `opencode run` times out past ~120s on large analysis — split into smaller prompts or use `--agent plan`
- `opencode web` is persistent; `opencode run` is one-shot — pick the right mode
- **Port conflict**: `opencode web --port PORT` silently starts on the port but a **previous instance on the same port** serves its old working directory. If the Web UI shows wrong workspace, check `ls -la /proc/$(lsof -ti:PORT)/cwd` to see which directory the server is actually running from, and kill the old instance first. The new `opencode web` process will take the port correctly.
- **Workspace is directory, not a UI entity**: OpenCode has no named "workspace" concept in the web UI — the workspace IS the current working directory. To add projects to a workspace, update `readme.md` in the workspace directory; use `opencode run` with `-f /path/to/project` to give OpenCode file-level context for analysis.
- **Security approval needed for Chinese paths**: `opencode run` prompts containing Chinese characters (paths, filenames, prompts) trigger a "Confusable Unicode" security scan. The user must approve these; account for the extra step.

**References:** `references/opencode/provider-auth.md`, `references/opencode/workspace-patterns.md`

---

## Section D: Cursor Agent

For WSL→Windows cross-platform orchestration. Cursor 3.x `cursor agent` is an interactive TUI.

### Binary resolution (WSL)

```
cmd.exe /c "d:\path\to\cursor\resources\app\bin\cursor.cmd"
```
Always `cd /mnt/c/Users/Public` first to avoid cmd.exe UNC path error.

### CLI commands

```bash
# Open file at line
cd /mnt/c/Users/Public && cmd.exe /c "d:\path\to\cursor.cmd -g file.py:42"

# Open project
cd /mnt/c/Users/Public && cmd.exe /c "d:\path\to\cursor.cmd -n d:\project\path"

# Start agent interactive TUI
cd /mnt/c/Users/Public && cmd.exe /c "d:\path\to\cursor.cmd agent"
```

Cursor has NO one-shot mode, NO piped input, NO JSON output.

### Orchestration strategies

1. **File Handoff** (most reliable) — Hermes analyzes/modifies files, opens in Cursor
2. **Interactive Agent** (experimental via tmux) — start in background
3. **File-Based Collaboration** — Hermes analyzes, writes to file, opens in Cursor

### Pitfalls

- `cmd.exe` cannot start from WSL network path (`\\wsl.localhost\...`) — always cd to /mnt/c/ first
- No PTY passthrough reliably across WSL→Windows
- Use `-w` flag to wait for file close (blocking)
- Cursor Server auto-install (~200MB) often fails on slow networks

**References:** `references/cursor-agent/opencli-cursor-integration.md`, `references/cursor-agent/wsl-windows-cross-calls.md`, `references/cursor-agent/hermes-cursor-bidirectional.md`

### Installing code intelligence plugins (CodeGraph, Understand-Anything)

Both CodeGraph (MCP server) and Understand-Anything (skills/plugin) can be installed into Cursor and Hermes Agent. See `references/code-intelligence-plugins.md` for per-tool installation steps, configuration patterns, and usage.

---

## Common Workflow Patterns

### PR Review (all agents)

```bash
# Quick review via pipe
terminal(command="git diff main...HEAD | claude -p 'Review this diff' --max-turns 1", timeout=60)

# Deep review with worktree
terminal(command="git worktree add -b review /tmp/review main && cd /tmp/review && codex exec 'Review PR #42'", pty=true)
```

### Parallel task execution

```bash
# Claude Code via tmux
terminal(command="tmux new-session -d -s task1 'claude -p \"Fix bug A\"'")
terminal(command="tmux new-session -d -s task2 'claude -p \"Fix bug B\"'")

# Codex via worktrees
git worktree add -b fix/a /tmp/a main && git worktree add -b fix/b /tmp/b main
terminal(command="codex --yolo exec 'fix A'", workdir="/tmp/a", background=true, pty=true)
terminal(command="codex --yolo exec 'fix B'", workdir="/tmp/b", background=true, pty=true)

# OpenCode via separate workdirs
terminal(command="opencode run 'fix A'", workdir="/tmp/a", background=true, pty=true)
terminal(command="opencode run 'fix B'", workdir="/tmp/b", background=true, pty=true)
```

### Multi-Project Workspace (cross-cut analysis)

```bash
# 1. Analyze each project with local tools first (CodeGraph/Understand)
# 2. Create workspace
terminal(command="mkdir -p /workspace", timeout=5)
terminal(command="opencode run 'Create readme.md recording both project paths'",
  workdir="/workspace", pty=true, timeout=120)

# 3. Start persistent web UI from workspace directory
terminal(command="opencode web --port 4096", workdir="/workspace", background=true)

# 4. Delegate analysis with project context attached
terminal(command="opencode run 'Analyze cross-project impact of feature X' \\
  -f /path/to/project1 -f /path/to/project2",
  workdir="/workspace", pty=true, timeout=180)
```

### Cleanup

```bash
tmux kill-session -t task1; tmux kill-session -t task2
git worktree remove /tmp/a; git worktree remove /tmp/b
```
