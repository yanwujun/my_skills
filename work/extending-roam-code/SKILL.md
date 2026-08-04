---
name: extending-roam-code
description: Add new CLI commands, modules, MCP tools, and interactive dashboards to roam-code based projects (business-rule-graph, etc.). Covers CLI registration, capability decorator, module structure, and the single-file dashboard pattern.
---

# Extending roam-code

How to add new features to a roam-code based project (business-rule-graph, etc.).

## Architecture Overview

roam-code uses Click's `LazyGroup` for CLI command registration. Each command lives in `src/roam/commands/cmd_<name>.py` and is registered in `src/roam/cli.py`.

```
src/roam/
  cli.py              # CLI entry point — register commands here
  commands/           # cmd_*.py — one command per file
  dashboard/          # example new module
    __init__.py
    serve.py          # core logic
    templates/        # static assets (HTML, etc.)
```

## Adding a New CLI Command

### 1. Create the command module

```python
# src/roam/commands/cmd_<name>.py
import click
from roam.capability import roam_capability

@roam_capability(
    name="my-command",          # CLI name (hyphenated)
    category="architecture",    # grouping in --help
    summary="What it does",
    maturity="alpha",           # alpha | beta | stable
    mcp_expose=True,            # also expose as MCP tool
    mcp_preset=("core",),
    side_effect=True,
    requires_index=True,        # needs .roam/index.db
)
@click.command(name="my-command")
@click.option("--port", type=int, default=8765)
@click.option("--no-open", is_flag=True)
@click.pass_context
def my_command(ctx, port, no_open):
    """Docstring becomes --help text."""
    ...
```

### 2. Register in cli.py

Two places in `src/roam/cli.py`:

```python
# (a) In _LAZY_COMMANDS dict (~line 100-400):
"my-command": ("roam.commands.cmd_my_command", "my_command"),

# (b) In the categorised --help panel list (~line 500-600):
"my-command",
```

### 3. Install and test

```bash
pip install -e . --break-system-packages
roam my-command --help
```

## Creating a New Module (e.g., dashboard/)

Standard Python package structure:

```
src/roam/<module>/
  __init__.py           # re-export public API
  <core>.py             # main logic
  templates/            # static files served at runtime
```

Imports within the module use relative paths: `from .serve import ...`

## Interactive Dashboard Pattern

For browser-based dashboards, use this lightweight pattern.
See `references/dashboard-architecture-decisions.md` for design rationale
and `references/roam-db-schema.md` for the full roam DB schema.

### serve.py — export + HTTP server

```python
import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent / "templates"

def export_data(db_path: str) -> dict:
    """Read roam DB, return JSON-serializable dict."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # ... query and build nodes/edges ...
    conn.close()
    return {"nodes": [...], "edges": [...]}

class _Handler(SimpleHTTPRequestHandler):
    graph_json: bytes = b"{}"

    def do_GET(self):
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(self.graph_json)
        elif self.path == "/":
            content = (_TEMPLATE_DIR / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(content)

def start_server(db_path, port=8765):
    data = json.dumps(export_data(db_path), ensure_ascii=False).encode()
    handler = type("_H", (_Handler,), {"graph_json": data})
    server = HTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}"
```

### templates/index.html — single-file frontend

Use vis.js CDN for graph visualization:
```html
<script src="https://visjs.github.io/vis-network/standalone/umd/vis-network.min.js"></script>
```

Key vis.js patterns:
- `new vis.Network(container, {nodes, edges}, options)` — create graph
- `network.on('click', fn)` — node click → show details
- `network.selectNodes(ids)` — programmatic selection
- `network.focus(id, {scale, animation})` — zoom to node
- `physics: { solver: 'forceAtlas2Based' }` — force layout
- `layout: { hierarchical: { direction: 'LR' } }` — hierarchical layout

### Performance: limit exported data

roam indexes can have 40K+ symbols. Always limit exports:
- Top N by pagerank (`ORDER BY pagerank DESC LIMIT 2000`)
- Only include file nodes referenced by top symbols
- Filter edges to only those between included nodes
- Frontend caps: `MAX_NODES = 500` in JS

## Extending an Existing Command (new flag/option)

When adding a new feature to an existing command (e.g., `--onboard` flag for `roam tour`):

1. Add the `@click.option(...)` decorator to the existing command function
2. Add the new parameter to the function signature
3. Pass the flag through to helper functions that need it
4. No CLI registration changes needed (already registered)
5. No new `@roam_capability` needed (belongs to the existing capability)

Example — adding `--onboard` to `roam tour`:
```python
@click.option(
    "--onboard",
    "onboard_mode",
    is_flag=True,
    default=False,
    help="Generate a full onboarding guide.",
)
# ...
def tour_command(ctx, write_file, mermaid_mode, onboard_mode, focus_path):
    # ... existing logic ...
    if onboard_mode:
        hotspots = _complexity_hotspots(conn)
        output = _render_onboard_markdown(output, ...)
```

## Common Pitfalls

1. **`pip install -e .` needs `--break-system-packages`** on modern Ubuntu/PEP 668 systems.
2. **`python` vs `python3`**: WSL Ubuntu 24.04 only has `python3`; use `python3` or set up an alias.
3. **`detect_layers(G: nx.DiGraph)`** takes a NetworkX graph, not a DB connection. Build the graph first with `build_symbol_graph(conn)`.
4. **DB path for project name**: `Path(db_path).parent` is `.roam/`; use `.parent.parent` for the project root.
5. **LSP false positives on new modules**: Pyright reports unresolved imports until the module is installed with `pip install -e .`
6. **CLI registration requires TWO entries in cli.py**: the lazy-load dict AND the categorised panel list.
7. **`@click.pass_context` + `ctx.obj`**: roam injects `{"json": bool}` into ctx.obj. Check for json mode with `ctx.obj.get("json")` if ctx.obj is not None.
