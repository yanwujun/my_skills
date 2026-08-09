---
name: hermes-migration
description: "Migrate Hermes skills/memories/cron to a new machine."
version: 1.0.0
category: devops
metadata:
  hermes:
    tags: [hermes, migration, backup, skills, memories, cron, packaging, devops]
    related_skills: [hermes-deployment, hermes-cron-ops, hermes-config-debug]
---

# Hermes Migration (to another machine)

Trigger when: user wants to move Hermes skills/memories/config to a new computer, wants a migration file list, or asks to split "工作 vs 个人" content for packaging.

## Workflow (5 steps)

### 1. Inventory `~/.hermes/`

| Path | Notes |
|---|---|
| `skills/<cat>/<name>/` | Use `du -sh skills/*/` for sizes |
| `memories/MEMORY.md` + `USER.md` | **Plaintext UTF-8** — but `read_file` misreports as binary; read via python/terminal |
| `config.yaml` | model/provider, approvals, mcp_servers (often holds work DB connections), platform_toolsets |
| `.env`, `auth.json` | Credentials — ⚠️ encrypt the archive when transferring |
| `cron/jobs.json` | dict `{'jobs': [...], 'updated_at': ...}` |
| `profiles/<name>/` | Per-profile config/.env/auth/memories/skills/sessions/state.db |
| `scripts/`, `mcp-servers/` | MCP server code may live outside WSL (e.g. `/mnt/d/mcp-server/...`) — must be copied separately |

### 2. Classify skills: 工作 / 个人 / 通用

Work = target machine must-have; personal = leave behind; common = take both. For this user's concrete split, see `references/user-work-personal-classification.md`. Rule: when a skill straddles the line, list it for the user to confirm rather than guessing.

### 3. Filter memories (work-only version)

MEMORY.md/USER.md are `§`-delimited single files mixing work + personal entries. Make a work-only copy: keep work + common entries, drop personal ones (study, hobbies, investing, house-buying, personal projects). List the dropped entries in the migration doc so the user can veto.

### 4. Filter cron + fix script paths

Keep only jobs for the target machine; **verify every script path referenced in kept prompts** — paths drift when skills move categories (real case: `productivity/direct-purchase-sql` → `dogfood/direct-purchase-sql`). Fix with a string replace inside the job dict before writing. User-confirmed classification (2026-08, 两次纠正): 工作任务 + **自我维护任务都算必要** —— 会话内容沉淀-每日分析（Hermes self-learning loop）和 每周一更新检查（env maintenance）都要进工作包；skill-sync-to-personal-GitHub job 不是工作（个人备份）。拿不准的任务列给用户确认，别自己拍板。Details in hermes-cron-ops.

### 5. Credential triage → work-config (凭据三审)

Generate `work-config/` versions of `.env`, `auth.json`, `config.yaml` — never ship originals to a work machine. Mask-audit each file (key names + lengths only), drop personal credentials, then **scan the whole config for residual references to removed keys** (real case: deleting FIRECRAWL_API_KEY left `web.backend: firecrawl` → set `web.backend: auto` or web search breaks). Git credentials (SSH keys ~/.ssh, gh ~/.config/gh, GITHUB_TOKEN) never migrate — they're outside package scope anyway.

**Never-migrate list (本用户最终口径, 2026-08 三次收紧)**: LLM API keys (DEEPSEEK_API_KEY + auth.json 同 key)、DingTalk、QQ 凭据全部不迁 —— 连带删 config 里的 `qq`/`dingtalk` 段和 `platform_toolsets.qqbot`。工作包只保留内网工作凭据 (mysql 工作库、内网 LLM 网关、api_server 本地 key)。包内没有 LLM key 时新机器必须 `hermes setup` 自配。Full audit script + this user's keep/drop map: `references/credential-triage.md`.

### 6. Package with tar --transform, restore, verify

```bash
# stage filtered files first, then remap into canonical paths inside the archive:
cd ~/.hermes && tar czf ~/hermes-migration/hermes-work.tar.gz \
  --transform='s|^work-memories/|memories/|' \
  --transform='s|^work-cron/|cron/|' \
  --transform='s|^work-config/||' \
  -C ~/hermes-migration work-memories work-cron work-config \
  -C ~/.hermes skills/dogfood profiles/sdd-architect/config.yaml ...
```

Work package must NOT include originals of `~/.hermes/memories`, `cron/jobs.json`, `config.yaml`, `.env`, `auth.json` — always the work-* staged versions.

Verify: `tar xzf pkg.tar.gz -O memories/MEMORY.md | head` (transform applied?), `tar tzf | wc -l` (size sanity).

Restore on new machine: extract both archives into `~/.hermes/`, then `hermes config check && hermes doctor`, `hermes mcp test mysql` (after copying Windows-side MCP dir), `hermes cron list`, `hermes skills list`, test profile with `hermes -p <name> chat -q "测试"`.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Whole-profile tar bloat** | `profiles/<name>/` wholesale includes lsp/, node_modules, state.db (551MB), logs/, cache/, sessions/ → 31MB/7726 entries | Select only config.yaml, .env, auth.json, memories/, skills/<needed subset> → 2.1MB/531 entries |
| **read_file "Binary file" on memories** | MEMORY.md/USER.md show as binary | They're plaintext UTF-8; read via python `open(path, encoding='utf-8')` |
| **Cron script-path drift** | Packaged job references moved skill path | `grep -o '~/.hermes/skills/[^ ]*' jobs.json \| sort -u`, verify each, string-replace in job dict |
| **MCP server lives on Windows side** | `hermes mcp test` fails on new machine | Copy `D:\mcp-server\...` separately; adapt path in config.yaml |
| **Credential leak** | .env/config.yaml hold DB passwords + API keys | gpg -c or encrypted channel for transfer; better: ship only work-config versions (see §5) |
| **Residual reference to removed key** | Deleted FIRECRAWL_API_KEY but `web.backend: firecrawl` still set → web tools break | `web.backend: auto`; verify whole file with `'firecrawl' not in json.dumps(cfg).lower()` |
| **Personal jobs slipped into work package** | User corrects you | Ask on borderline jobs; see classification reference |

## Windows-side delivery

`cp -r ~/hermes-migration /mnt/d/hermes-migration` → visible in Explorer as `D:\hermes-migration\`; or `\\wsl$\<distro>\home\<user>\hermes-migration\`. Deliver: work/common tar.gz + migration checklist md + filtered memory/cron source files.

## Reference files

- `references/user-work-personal-classification.md` — this user's concrete 工作/个人/通用 skill split + work memory entries kept/dropped + cron decisions (2026-08 baseline)
- `references/credential-triage.md` — mask-audit script for .env/auth.json/config.yaml, this user's keep/drop credential map, residual-reference trap
