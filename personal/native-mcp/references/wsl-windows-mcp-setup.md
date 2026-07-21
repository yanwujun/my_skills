# WSL + Windows MCP Server Setup

When the MCP server lives in the **Windows filesystem** (`D:\\...`, `C:\\Users\\...`) and Hermes Agent runs inside **WSL**, these patterns apply.

## Path Translation

Windows paths under WSL mount: `/mnt/d/...` = `D:\\...`

```yaml
mcp_servers:
  mysql:
    command: "python3"   # use WSL's python3, NOT Windows Python
    args: ["/mnt/d/mcp-server/mcp-mysql-python/server.py"]
```

## Python Pitfall: Windows venv is unusable from WSL

A virtual environment created with `python -m venv .venv` on **Windows** creates:
- `Scripts/python.exe` (Windows exe)
- NOT `bin/python` (Linux binary)
- The `.venv` directory's `pyvenv.cfg` points to a Windows Python path

**WSL cannot use a Windows venv.** When the server requires `mcp`, `pymysql`, etc.:

- ❌ Do NOT try to use `.venv/bin/python` — it doesn't exist
- ✅ Install deps to system Python with `--break-system-packages`:

```bash
pip3 install mcp pymysql python-dotenv --break-system-packages
```

## MySQL Multi-Connection MCP Server

The `mcp-mysql-python` server at `D:\\mcp-server\\mcp-mysql-python\\` supports multiple database connections via the `MYSQL_CONNECTIONS` env var (a JSON dict), instead of single-connection env vars (`MYSQL_HOST`, `MYSQL_USER`, etc.).

### Config pattern for Hermes Agent

```yaml
mcp_servers:
  mysql:
    command: "python3"
    args: ["/mnt/d/mcp-server/mcp-mysql-python/server.py"]
    env:
      MYSQL_CONNECTIONS: '{
        "default":{"host":"192.168.2.37","port":31004,"user":"root","password":"mysql","database":"xcj_mall_base"},
        "ezc":{"host":"192.168.2.37","port":31004,"user":"root","password":"mysql","database":"ezc"},
        "trade":{"host":"192.168.2.37","port":31004,"user":"root","password":"mysql","database":"trade"},
        "stddata":{"host":"192.168.2.37","port":31004,"user":"root","password":"mysql","database":"stddata"}
      }'
    timeout: 60
```

### Available tool names (after restart)

| Tool | Hermes name | Description |
|------|-------------|-------------|
| `list_connections` | `mcp_mysql_list_connections` | List configured connection IDs |
| `execute_query` | `mcp_mysql_execute_query` | SELECT only. Params: `query`, `connection_id` |
| `list_tables` | `mcp_mysql_list_tables` | SHOW TABLES. Param: `connection_id` |
| `describe_table` | `mcp_mysql_describe_table` | DESCRIBE + SHOW CREATE TABLE. Params: `table_name`, `connection_id` |
| `execute_write` | `mcp_mysql_execute_write` | INSERT/UPDATE/DELETE. Params: `query`, `connection_id` |

### Connection IDs for this user's setup

| connection_id | database | tables | notes |
|---------------|----------|--------|-------|
| `default` | xcj_mall_base | 326 | 直采商城主库（商品、供应商、订单合同、目录授权等） |
| `ezc` | ezc | 59 | 框架协议核心（征集项目、协议商品、导购目录等） |
| `trade` | trade | 307 | 商品/订单共享 |
| `stddata` | stddata | 60 | 标准数据 |

### Verification command (before adding to config)

```python
import pymysql
from pymysql.cursors import DictCursor

for name, cfg in [("name", {"host":"...","port":3306,"user":"root","password":"...","database":"...", "cursorclass":DictCursor})]:
    conn = pymysql.connect(**cfg)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s", (cfg["database"],))
    r = cur.fetchone()
    print(f"{name}: {r['cnt']} tables")
```

(Note: pymysql 2.x defaults to tuple cursors; you MUST pass `cursorclass=DictCursor` to get dict-style results like `r["cnt"]`.)

## Cursor MCP Config (separate from Hermes)

Cursor IDE has its own MCP config at `C:\Users\<user>\.cursor\mcp.json`. If accidentally modified, restore it from known working values.

### MySQL MCP Server for Cursor

Same server binary as Hermes MCP (`D:\mcp-server\mcp-mysql-python\server.py`), but configured in Cursor's mcp.json with inline env vars:

```json
{
  "mcpServers": {
    "mcp-mermaid": {
      "command": "npx -y mcp-mermaid",
      "env": {},
      "args": []
    },
    "mysql": {
      "command": "python",
      "args": ["D:/mcp-server/mcp-mysql-python/server.py"],
      "env": {
        "MYSQL_CONNECTIONS": "{\"default\":{\"host\":\"192.168.2.37\",\"port\":31004,\"user\":\"root\",\"password\":\"mysql\",\"database\":\"xcj_mall_base\"},\"trade\":{\"host\":\"192.168.2.37\",\"port\":31004,\"user\":\"root\",\"password\":\"mysql\",\"database\":\"trade\"},\"ezc\":{\"host\":\"192.168.2.37\",\"port\":31004,\"user\":\"root\",\"password\":\"mysql\",\"database\":\"ezc\"}}"
      }
    }
  }
}
```

### Restoration when mcp.json is lost/broken

- Cursor's `.cursor/mcp.json` has **no git backup** by default
- To restore, get the server path from `D:\mcp-server\mcp-mysql-python\`
- Database credentials can be found in the project's `env.example` (plaintext) or Navicat export XML (encrypted — use `mysql` as the common password)
- Multi-connection mode via `MYSQL_CONNECTIONS` JSON string
- The server uses `python` (Windows Python), not `python3` (WSL Python) — Cursor runs on Windows
- The `.env` file in the server directory has the database config, but Cursor needs the env vars inline in mcp.json

### Multi-environment Navicat reference for this user

From Navicat export XML, the environments and their port conventions:

| Environment | 行采 port | 政采 port | Host |
|-------------|----------|----------|------|
| show1 | 31004 | 31404 | 192.168.2.37 |
| dev1 | 33004 | 33404 | 192.168.2.17 |
| test3 | 31004 | 32004 | 192.168.2.2 |

行采 = xcj_mall_base/trade/ezc, 政采 = zcj_* databases.
Common password: `mysql` (verify per environment before production use).

### Pitfall: no backup

There is no `.git` in `.cursor/` by default. If the user needs protection, suggest initializing git there:
```bash
cd /mnt/c/Users/Administrator/.cursor
git init
git add mcp.json
git commit -m "initial mcp config backup"
```

## MCP server requires agent restart

MCP servers are connected during agent startup. Adding/removing `mcp_servers` in `~/.hermes/config.yaml` requires **restarting Hermes Agent**. No hot-reload.

## Browser note

Hermes has built-in browser tools (`browser_navigate`, `browser_click`, etc.) — no separate MCP browser server needed. If you need a headless Playwright/Puppeteer MCP server, use `@modelcontextprotocol/server-puppeteer` via npx.
