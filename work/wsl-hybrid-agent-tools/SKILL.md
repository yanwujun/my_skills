---
name: wsl-hybrid-agent-tools
description: Install and configure AI agent tools (MCP servers, skills, plugins) across WSL + Windows dual environments — WSL (Hermes) + Windows (Cursor)
trigger: |
  用户要求安装/配置 AI 辅助工具（MCP 服务器、Hermes 技能、Cursor 插件），
  且环境是 WSL (Hermes Agent) + Windows (Cursor) 双端设置。
---

# WSL Hybrid Agent Tools

Install AI agent tools in a dual WSL+Windows environment where Hermes Agent runs in WSL and Cursor (or other Windows-native agents) runs on Windows.

## Architecture Overview

```
Windows (Cursor)                         WSL (Hermes Agent)
  │                                            │
  ├─ MCP via wsl.exe bridge                    ├─ MCP via codegraph install / manual
  │  C:\Users\<user>\.cursor\mcp.json          │  ~/.hermes/config.yaml
  │                                            │
  ├─ MCP via native .cmd (preferred)           ├─ skills symlinks (Hermes is in WSL
  │  D:\baseSoftware\nodejs\npm-global\        │  so Linux paths work fine)
  │                                            │  ~/.hermes/skills/
  ├─ skills via Windows junctions              │
  │  (NOT WSL ln -s — see Pitfall #8)          ├─ npm global installs
  │  C:\Users\<user>\.cursor\skills\           │  /home/<user>/.local/bin/
  │                                            │
  └─ source code                               │
     D:\baseSoftware\                           │
```

## General Workflow

### 1. Get the source

Two options:

**Git clone to D:\baseSoftware (for reference / future use):**
```bash
cd /mnt/d/baseSoftware
git clone -c http.proxy=http://127.0.0.1:8888 https://github.com/org/repo.git
```

**npm global install (for CLI commands / MCP servers):**
```bash
# WSL side
npm i -g @scope/package

# Windows side — run from Windows cmd (WSL can't exec .exe directly)
D:\baseSoftware\nodejs\npm.cmd i -g @scope/package
```

### 2. Configure for Hermes Agent (WSL)

**MCP Server (e.g. CodeGraph):**
```bash
npm i -g @colbymchenry/codegraph
codegraph install --target auto --yes
# Verify: hermes config check && hermes mcp test <name>
```

**Skill (e.g. Understand-Anything):**
```bash
ln -sfn /mnt/d/baseSoftware/<repo>/<plugin>/skills ~/.hermes/skills/<skill-group-name>
# If plugin root needed:
ln -sfn /mnt/d/baseSoftware/<repo>/<plugin> ~/.<plugin-link-name>
# Verify: hermes skills list | grep <name>
```

### 3. Configure for Cursor (Windows)

**Option A — MCP Server via WSL bridge (use when tool is only in WSL):**
Edit `C:\Users\<username>\.cursor\mcp.json`:
```json
"server-name": {
  "command": "C:\\Windows\\System32\\wsl.exe",
  "args": ["-e", "bash", "-lc", "<tool-command>"],
  "env": { "PATH": "/usr/local/bin:/usr/bin:/bin:/home/<user>/.local/bin" }
}
```
Limitation: every MCP request starts a new WSL process — slightly slower.

**Option B — MCP Server via Windows native (preferred when tool is on Windows too):**
Install the tool on Windows via npm, then point to it directly in mcp.json:
```json
"server-name": {
  "command": "D:\\baseSoftware\\nodejs\\npm-global\\<tool>.cmd",
  "args": []
}
```
Example (CodeGraph installed from Windows cmd: `D:\baseSoftware\nodejs\npm.cmd i -g @colbymchenry/codegraph`):
```json
"codegraph": {
  "command": "D:\\baseSoftware\\nodejs\\npm-global\\codegraph.cmd",
  "args": []
}
```

**Skills — use Windows directory junctions, NOT WSL ln -s symlinks:**

Critical: `ln -s` from WSL creates symlinks with Linux-path targets (`/mnt/d/...`). Windows apps like Cursor CANNOT resolve these paths. The skills appear broken/invisible — they are not "just a display issue".

Since WSL interop is often disabled, you cannot run `cmd.exe /c mklink` from WSL either. Instead, generate a PowerShell fix script on the Windows desktop. A reusable script is available in this skill's `scripts/` directory: `create-cursor-skills-junctions.ps1` — copy it to the desktop, edit the `$PluginName` and `$SkillNames` parameters, and tell the user to right-click → Run with PowerShell (Admin).

```powershell
# fix-cursor-skills.ps1 — run as Administrator
$cursorSkills = "$env:USERPROFILE\.cursor\skills"
$sourceBase = "D:\baseSoftware\<repo>\<plugin>\skills"
$skills = @("skill1", "skill2", ...)
foreach ($skill in $skills) {
    $target = "$sourceBase\$skill"
    $link = "$cursorSkills\$skill"
    if (Test-Path $link) { Remove-Item $link -Force -Recurse }
    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
}
```
User runs it from Windows: right-click → Run with PowerShell, or `powershell -ExecutionPolicy Bypass -File ...ps1`.

Validate JSON after mcp.json edit:
```bash
python3 -c "import json; json.load(open('/mnt/c/Users/<username>/.cursor/mcp.json')); print('OK')"
```

### 4. Project-Level Initialization

For tools that need per-project indexing (e.g. CodeGraph), run from WSL:
```bash
cd /mnt/d/项目/your-project
codegraph init -i
```
Note: live file watching is disabled on /mnt/ drives. Run `codegraph sync` after changes.

## CodeGraph-Specific

| Step | Command | Notes |
|------|---------|-------|
| Install (WSL) | `npm i -g @colbymchenry/codegraph` | |
| Install (Windows) | From cmd: `D:\baseSoftware\nodejs\npm.cmd i -g @colbymchenry/codegraph` | WSL can't run .cmd/.exe directly |
| Configure Hermes | `codegraph install --target auto --yes` | May corrupt YAML — verify after |
| Verify Hermes | `hermes config check; hermes mcp test codegraph` | 10 tools expected |
| Configure Cursor | Option A: wsl.exe bridge (if only in WSL) | See "Configure for Cursor" above |
| Configure Cursor | Option B: point to codegraph.cmd directly (if on Windows) | Faster, native |
| Init project | `codegraph init -i` | In project dir from WSL |
| Re-sync | `codegraph sync` | Needed after changes on /mnt/ drives |

## Understand-Anything-Specific

| Step | Command | Notes |
|------|---------|-------|
| Get source | `git clone` to D:\baseSoftware | Repo: Egonex-AI/Understand-Anything |
| Hermes skills | `ln -sfn <repo>/understand-anything-plugin/skills ~/.hermes/skills/understand-anything` | Folder-style link |
| Hermes plugin root | `ln -sfn <repo>/understand-anything-plugin ~/.understand-anything-plugin` | Needed by build scripts |
| Cursor skills | Windows junctions from `D:\baseSoftware\...\skills\` | NOT ln -s — see Pitfall #8 |

Available skills: understand, understand-chat, understand-dashboard, understand-diff, understand-domain, understand-explain, understand-knowledge, understand-onboard.

### Understand-Anything Dashboard (Runtime)

After installation, to view the knowledge graph as an interactive web dashboard:

1. **Install pnpm** (if missing):
   ```bash
   npm install -g pnpm
   ```
   Note: pnpm installs to `/home/<user>/.local/n/bin/pnpm` — may not be in PATH. Use full path or `PATH="/home/<user>/.local/n/bin:$PATH"` prefix.

2. **Install dependencies** in the plugin root:
   ```bash
   cd /mnt/d/baseSoftware/Understand-Anything/understand-anything-plugin
   PATH="/home/<user>/.local/n/bin:$PATH" pnpm install --no-frozen-lockfile
   ```
   `--no-frozen-lockfile` is needed when the lockfile is out of sync from the repo.

3. **Build the core package** (needed once):
   ```bash
   cd /mnt/d/baseSoftware/Understand-Anything/understand-anything-plugin/packages/core
   PATH="/home/<user>/.local/n/bin:$PATH" npx tsc
   ```
   Or from plugin root:
   ```bash
   PATH="/home/<user>/.local/n/bin:$PATH" pnpm --filter @understand-anything/core build
   ```

4. **Start the dashboard** (background):
   ```bash
   cd /mnt/d/baseSoftware/Understand-Anything/understand-anything-plugin/packages/dashboard
   GRAPH_DIR="/path/to/project" UNDERSTAND_ACCESS_TOKEN="my-token" PATH="/home/<user>/.local/n/bin:$PATH" npx vite --host 127.0.0.1 --port 5173
   ```
   - `GRAPH_DIR` = project root containing `.understand-anything/knowledge-graph.json`
   - `UNDERSTAND_ACCESS_TOKEN` = set a known token so you can share the URL. Without it, a random hex token is generated per server start.
   - Access from Windows: `http://127.0.0.1:5173/?token=my-token` (WSL2 automatically forwards localhost). If forwarding fails, use the WSL IP (from `ip addr show eth0`).

5. **React to changes**: Kill and restart the dashboard after re-running `/understand` to pick up the new graph.

### Windows npm Registry & Prefix

The user's Windows npm is configured with:
```ini
# C:\Users\<user>\.npmrc
registry=https://registry.npmmirror.com
cache=D:\baseSoftware\nodejs\npm-cache
prefix=D:\baseSoftware\nodejs\npm-global
```

- The npm binary is at `D:\baseSoftware\nodejs\npm.cmd`
- Global installs go to `D:\baseSoftware\nodejs\npm-global\`
- Windows PATH may NOT include the npm-global dir — tools installed there won't be found from cmd/powershell
- **Fix:** Use full path (`D:\baseSoftware\nodejs\npm-global\<tool>.cmd`) in Cursor mcp.json, or add to PATH via:
  ```powershell
  [Environment]::SetEnvironmentVariable("Path", "$env:Path;D:\baseSoftware\nodejs\npm-global", "User")
  ```

### Cursor CodeGraph MCP — Auto-Rewrite

When `codegraph install` is run from WSL, it doesn't touch Windows configs. However, if the user also installed CodeGraph on Windows via npm, Cursor may auto-detect it and write a preliminary `mcp.json` entry. That entry often includes `"type": "stdio"` and extra args like:
```json
"codegraph": {
  "type": "stdio",
  "command": "codegraph",
  "args": ["serve", "--mcp", "--path", "${workspaceFolder}"]
}
```
**Fix:** Simplify to just the command (no type, minimal args):
```json
"codegraph": {
  "command": "D:\\baseSoftware\\nodejs\\npm-global\\codegraph.cmd",
  "args": []
}
```

---

## Absorbed from `wsl-agent-tooling` (archived)

The unique patterns from the now-archived `wsl-agent-tooling` skill — WSL
network proxy diagnostic flow, Windows cmd access patterns, and a consolidated
verification checklist — live in `references/wsl-proxy-and-verification.md`.
Load it when network connectivity is suspect, when a WSL-installed tool isn't
found from Windows cmd, or when verifying a fresh cross-environment tool install.

## Pitfalls

1. **Windows .exe not runnable from WSL** — WSL cannot exec PE binaries (`Exec format error`). Use `wsl.exe` from Windows side as bridge, not the reverse.

2. **npm.cmd not runnable from WSL** — `.cmd` files are batch scripts, not binaries. Install via WSL npm or run from Windows cmd.

3. **curl|bash installers blocked** — The user blocks `curl ... | sh` / `curl ... | bash`. Prefer npm install, git clone + manual symlink, or standalone installer script review.

4. **codegraph init on /mnt/ drives** — Live watching disabled. Must run `codegraph sync` manually after changes.

5. **Cursor MCP JSON validation** — Always validate JSON after manual edits. One wrong comma breaks all MCP servers.

6. **External MCP installers + YAML corruption** — `codegraph install` etc. can break `config.yaml` indentation (especially `platform_toolsets:` sections). Always run `hermes config check` after.

7. **Source path location** — Skills/MCP that reference local files need absolute paths. D:\baseSoftware source lives at `/mnt/d/baseSoftware/` in WSL. Use realpath or absolute paths, not relative.

8. **WSL ln -s on Windows drives creates broken symlinks** — When you `ln -s` from WSL targeting a Windows path (e.g. `/mnt/d/...`), the resulting symlink stores the Linux path as its target. Windows apps (Cursor, VS Code, Explorer) CANNOT resolve `/mnt/d/` — the link appears broken. This is NOT a display issue; the symlink is genuinely unusable from Windows. **Fix:** Delete the WSL symlink and create a Windows directory junction instead. Since WSL interop may be disabled, generate a PowerShell script the user runs on Windows (see "Skills — use Windows directory junctions" section above).

9. **WSL interop disabled / can't run Windows binaries** — WSL may have interop disabled (`/proc/sys/fs/binfmt_misc/WSLInterop` missing). This means you cannot run any Windows .exe/.cmd from WSL (`Exec format error`). Impact: cannot use `cmd.exe /c mklink` or run npm.cmd. **Workaround:** Generate .bat/.ps1 scripts on the Windows desktop for the user to double-click/run. Do NOT try to work around by changing WSL config — the user blocks modifications to dotfiles like ~/.bashrc.

9b. **When WSL interop IS available — use `cmd.exe /c` with care** — The `cmd.exe /c` bridge works but has sharp edges:

    | Problem | Fix |
    |---------|-----|
    | Chinese paths in batch scripts break `%cd%` / `%~dp0` | Use `subst X: D:\\...` virtual drive (NOT `mklink /D` — `%cd%` resolves real path) |
    | SVN URLs with Chinese chars get garbled | Use `chcp 936` (GBK) instead of `chcp 65001` (UTF-8) |
    | Bat file `set` commands truncated | Keep bat files GBK-encoded, NOT UTF-8-BOM |
    | Bash double-quotes corrupt nested quotes | Use single-quote wrapping in bash |
    | URL-encoding Chinese as `%E5%AE%89` in bat files | Don't — `%` is batch variable delimiter; use subst+GBK instead |

    Full patterns: `government-procurement-ops` skill → `references/publish-workflow.md`.

10. **pnpm not in PATH after npm install -g** — `npm install -g pnpm` installs pnpm to `/home/<user>/.local/n/bin/pnpm` but `~/.local/n/bin` may NOT be in PATH after install; `which pnpm` returns empty. **Fix:** Use full path `/home/<user>/.local/n/bin/pnpm`, or prefix commands with `PATH="/home/<user>/.local/n/bin:$PATH"`.

11. **pnpm blocks native addon builds (ERR_PNPM_IGNORED_BUILDS)** — When running `pnpm install` in Understand-Anything's plugin root, pnpm may refuse to run build scripts for native addons (tree-sitter parsers, esbuild) due to its `onlyBuiltDependencies` policy. **Fix:** Add an `.npmrc` in the project root with explicit allowlist entries:
    ```
    onlyBuiltDependencies[]="esbuild"
    onlyBuiltDependencies[]="tree-sitter-c"
    onlyBuiltDependencies[]="tree-sitter-cpp"
    onlyBuiltDependencies[]="tree-sitter-go"
    onlyBuiltDependencies[]="tree-sitter-java"
    onlyBuiltDependencies[]="tree-sitter-javascript"
    onlyBuiltDependencies[]="tree-sitter-php"
    onlyBuiltDependencies[]="tree-sitter-python"
    onlyBuiltDependencies[]="tree-sitter-ruby"
    onlyBuiltDependencies[]="tree-sitter-rust"
    onlyBuiltDependencies[]="tree-sitter-typescript"
    onlyBuiltDependencies[]="tree-sitter-c-sharp"
    onlyBuiltDependencies[]="@tree-sitter-grammars/tree-sitter-kotlin"
    ```
    Or run `pnpm approve-builds` interactively — but headless sessions cannot respond, so the `.npmrc` approach is preferred.

12. **Tree-sitter native parsers need build-essential** — The tree-sitter language parsers are C/C++ native addons that must compile during `pnpm install`. If `gcc`/`make` are missing from the WSL environment, the build silently fails or tree-sitter extraction produces no results. **Fix:** `sudo apt install build-essential`.

13. **WSL network proxy (CHECK FIRST)** — This WSL environment sits behind an HTTP proxy at `http://127.0.0.1:8888`. Without it, all outbound connections time out (`git clone`, `npm install`, `curl`, `pip install`, everything). Always test connectivity before diagnosing tool-specific failures: `curl -sI --connect-timeout 5 https://github.com -o /dev/null -w "%{http_code}"` → "000" means no connectivity → activate proxy. SSH is blocked entirely by the proxy — never use `git@github.com:` remotes. Full diagnostic flow in `references/wsl-proxy-and-verification.md`.

14. **Verification after install** — After installing any cross-environment tool, run the verification checklist in `references/wsl-proxy-and-verification.md` to confirm WSL binary, Hermes MCP, config YAML, Cursor mcp.json, and Cursor skills are all correct.

15. **npm/pnpm ECONNRESET through proxy → switch to npmmirror** — When the Sing-box proxy is up but npm registry requests (`registry.npmjs.org`) get ECONNRESET (TCP-level resets, not timeouts), the proxy chain is dropping npm connections. **Fix:** switch registry to the Chinese mirror:
   ```bash
   pnpm config set registry https://registry.npmmirror.com
   # Or for npm:
   npm config set registry https://registry.npmmirror.com
   ```
   This avoids the proxy entirely for npm traffic (npmmirror resolves via domestic DNS). After switching, a failed `pnpm install` can resume — the store cache holds partial downloads.

16. **Node.js install without sudo (n + N_PREFIX)** — The user blocks `curl|bash` (nvm) and sudo commands that require password. For installing a newer Node.js version:
   ```bash
   npm install -g n                          # n version manager, installable without sudo
   mkdir -p ~/.local/n                       # n needs N_PREFIX to avoid /usr/local (needs sudo)
   N_PREFIX=$HOME/.local/n n <version>       # e.g. n 24
   # Then use inline prefix: PATH=$HOME/.local/n/bin:$PATH node
   # Or the full path: $HOME/.local/n/bin/node
   ```
   Do NOT try `export PATH=...` — variable assignment with `export` is blocked in this environment. Always use inline `PATH=...` prefix or the full binary path.

17. **Docker Desktop + WSL Integration** — When Docker Desktop is installed on Windows and needs to be used from WSL:
   - Enable WSL Integration: Docker Desktop → Settings → Resources → WSL Integration → toggle Ubuntu ON → Apply & Restart
   - After enabling, `/usr/bin/docker` → `/mnt/wsl/docker-desktop/cli-tools/usr/bin/docker` (auto-created symlink)
   - Docker socket at `/var/run/docker.sock` owned by `root:docker` (mode `srw-rw----`)
   - User may be in `docker` group but membership hasn't refreshed. **Fix:** `sg docker -c "<cmd>"` or `newgrp docker`
   - `permission denied while trying to connect to the docker API` → use `sg docker -c`
   - `bash docker ps` → "cannot execute binary file": user ran docker as a shell script. Just run `docker ps` directly.

18. **WSL filesystem performance (9P overhead) — CRITICAL for Node.js projects** — Never put large Node.js project source code on `/mnt/d/` (Windows drives). The WSL 9P protocol translates every Linux filesystem syscall to Windows NTFS calls. Each `open()`/`read()`/`write()` crosses the protocol boundary. For build tools that write thousands of files (Gatsby page-data.json, webpack chunks, Vite HMR), this per-operation overhead compounds into catastrophic slowness. Symptoms: Gatsby stuck at `Writing page-data.json 1/19116` for hours. **Fix:** Always clone/develop on WSL native ext4 filesystem (`~/fcc`, not `/mnt/d/fcc`). Docker containers, databases, and services CAN remain on Windows side — `localhost` TCP networking is not affected by this filesystem layer. The user can still edit files from Windows via `\\wsl$\Ubuntu\home\...`.