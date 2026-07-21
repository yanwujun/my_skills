# Cursor Token Consumption Optimization

## When to load this reference

- User asks how to reduce/save Cursor token usage or subscription consumption
- User asks about tools (CodeGraph, MCP) that can cut Cursor costs
- User wants to know practical strategies beyond basic tips

## Strategy 1: CodeGraph MCP — the single biggest win

### Why it matters

In a Java/Spring Boot project, understanding one feature flow typically requires Cursor to read 10-20 files (controller → service → impl → mapper → XML). Each `read_file` burns tokens and clutters context. CodeGraph replaces that with ONE MCP call.

Before: 6-15 tool calls, 10K+ tokens
After: 1 `codegraph_explore()` call, 200-2K tokens

### How it works

CodeGraph pre-indexes your project (`.codegraph/` directory). The `codegraph_explore` tool accepts natural-language queries and returns focused source code with call paths — grouped by file, already readable. Cursor doesn't need to re-open those files.

### Cursor MCP config

Create `.cursor/mcp.json` in project root:

```json
{
  "mcpServers": {
    "codegraph": {
      "command": "codegraph",
      "args": ["serve", "--mcp", "--no-watch"]
    }
  }
}
```

### WSL2 pitfall: --no-watch

WSL2 accessing Windows filesystem (`/mnt/d/`) has broken inotify. Without `--no-watch`, CodeGraph's file watcher burns CPU or produces stale indexes. Always use `--no-watch` on WSL2. Re-index manually after major changes: `codegraph index`.

### First-time indexing

```bash
cd /mnt/d/your-project
codegraph index
```

### Verifying it works

In Hermes: `hermes mcp test codegraph`
In Cursor: Settings → MCP → check codegraph shows as connected

## Strategy 2: Good .cursorrules = fewer exploratory reads

A precise `.cursorrules` tells Cursor your conventions upfront. Without it, every session starts with Cursor probing the codebase to learn your patterns — wasted tokens.

For a Java/Spring Boot project, include:
- Package naming conventions
- MyBatis XML location patterns
- Redis vs JVM lock policy
- Cross-database query conventions (occurPlatCode/platDomain)
- MVP-first approach

## Strategy 3: .cursorignore = don't index junk

Exclude from Cursor's indexing:
- `node_modules/`, `target/`, `vendor/`
- `*.log`, `*.min.js`, `*.min.css`
- Generated code directories
- Test fixtures if not currently relevant

## Strategy 4: Chat vs Agent mode

Agent mode makes tool calls (read_file, search, terminal) every turn — 3-5x more expensive than Chat.
- **Chat**: for questions, explanations, code review discussions
- **Agent**: only when code changes or command execution is needed

## Strategy 5: @file/@folder precision

Instead of "fix the order service", use "@file:OrderServiceImpl.java fix the submitOrder method". This prevents Cursor from scanning the entire project to locate the target.

## Strategy 6: Understand (Hermes) as pre-exploration

Run `/understand` in Hermes before starting a Cursor session. The generated knowledge graph gives you architecture clarity without burning Cursor tokens on exploration. Then in Cursor, use `@file` to jump straight to the right files.

## GitHub repos (verified, high-star)

- **PatrickJS/awesome-cursorrules** — largest .cursorrules template collection, by language/framework
- **cursor.directory** — community-driven rules sharing site with GitHub mirror
- Various `.cursorignore` template repos — search "cursorignore template" on GitHub

## Quick-reference: optimization priority

| Priority | Action | Token savings |
|----------|--------|---------------|
| 1 | CodeGraph MCP in Cursor | 50-80% fewer file reads |
| 2 | Good .cursorrules | 20-30% fewer exploratory reads |
| 3 | .cursorignore | 10-20% less indexing noise |
| 4 | Chat mode for simple tasks | 3-5x cheaper than Agent |
| 5 | @file precision | 30-50% less context per prompt |
