# Code Intelligence Plugins for AI Coding Agents

Installation and configuration patterns for code intelligence tools — MCP servers (CodeGraph) and skills/plugins (Understand-Anything) — across AI coding agents.

## Agent Comparison: How Each Tool Works

| Tool | Hermes Agent | Cursor |
|------|-------------|--------|
| **CodeGraph** | MCP server (`hermes mcp test codegraph`). Tools auto-available in session. | MCP server in `mcp.json`. Needs `codegraph install --target cursor` or manual JSON entry. |
| **Understand-Anything** | Hermes skills (`/understand`, `/understand-dashboard`, etc.). Symlinked into `~/.hermes/skills/`. | Auto-discovered via `.cursor-plugin/plugin.json` when repo is opened in Cursor. |

## CodeGraph

### What it provides

10 MCP tools: `codegraph_search`, `codegraph_context`, `codegraph_callers`, `codegraph_callees`, `codegraph_impact`, `codegraph_node`, `codegraph_explore`, `codegraph_status`, `codegraph_files`, `codegraph_trace`.

Key tool: `codegraph_context` — call this FIRST for any "how does X work" question. Composes search + node + callers + callees in one call.

### Installation

```bash
# Step 1: Install CLI
npm i -g @colbymchenry/codegraph

# Step 2: Auto-configure for detected agents
codegraph install --target auto --yes

# Step 3: Initialize in a project
cd your-project
codegraph init -i
```

The installer auto-detects: Claude Code, Codex CLI, OpenCode CLI, Hermes Agent, Cursor, Gemini CLI, Antigravity IDE, and Kiro. For Hermes, it adds the MCP server to `~/.hermes/config.yaml`. Always verify after:

```bash
hermes config check          # Check YAML integrity
hermes mcp test codegraph    # Verify connection + tool discovery
```

### Cursor manual config

If auto-install didn't detect Cursor (common in WSL), add to `C:\Users\<user>\.cursor\mcp.json`:

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "wsl.exe",
      "args": ["-e", "bash", "-lc", "codegraph"]
    }
  }
}
```

### Per-project usage

```bash
codegraph init -i    # Create .codegraph/ index
codegraph status     # Check index health
codegraph upgrade    # Update CLI
```

### Pitfalls

- `codegraph install` can corrupt `~/.hermes/config.yaml` indentation (especially `platform_toolsets:`). Always run `hermes config check` after.
- `npm i -g` may not put binary in PATH if using `n`/`fnm` version managers. Symlink: `ln -sf $(npm root -g)/@colbymchenry/codegraph/bin/codegraph.js ~/.local/bin/codegraph`

## Understand-Anything

### What it provides

8 Hermes skills: `understand`, `understand-chat`, `understand-dashboard`, `understand-diff`, `understand-domain`, `understand-explain`, `understand-knowledge`, `understand-onboard`.

### Installation for Hermes

```bash
# Clone repo
git clone https://github.com/Egonex-AI/Understand-Anything.git

# Create skill symlink
ln -sfn <repo>/understand-anything-plugin/skills ~/.hermes/skills/understand-anything

# Create universal plugin root symlink
ln -sfn <repo>/understand-anything-plugin ~/.understand-anything-plugin
```

The install script (`install.sh hermes`) does these same steps automatically but uses `~/.understand-anything/repo/` as the clone destination.

### Cursor auto-discovery

Cursor reads `.cursor-plugin/plugin.json` from the repo. Opening the repo directory in Cursor auto-discovers the plugin. To use across ALL Cursor projects, either:
- Run the install script: `install.sh vscode` (also works for Cursor)
- Or symlink skills into `~/.cursor/skills/`

### Usage

```bash
# Hermes: slash commands
/understand                          # Analyze current project
/understand --language zh            # Chinese output
/understand src/frontend             # Subdirectory scope
/understand-dashboard                # Interactive graph
/understand-chat How does X work?    # Ask about codebase
/understand-explain src/auth.ts      # Deep-dive a file
/understand-diff                     # Git diff impact
/understand-onboard                  # New member guide

# Cursor: via plugin UI or command palette
```

### Incremental updates

```bash
/understand              # Re-run — incremental by default
/understand --full       # Force full rebuild
/understand --auto-update  # Post-commit hook auto-update
```

### Pitfalls

- First run needs `pnpm install` and build in the plugin root. If `pnpm` missing: `npm install -g pnpm`.
- The knowledge graph JSON can be large (10+ MB for big projects). Track with `git-lfs` if committing.
- Knowlege graph output dir: `.understand-anything/` in the project root.
