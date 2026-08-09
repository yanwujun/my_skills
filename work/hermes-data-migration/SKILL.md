---
name: hermes-data-migration
description: "Use when migrating/backing up Hermes to another machine."
version: 1.0.0
category: devops
metadata:
  hermes:
    tags: [hermes, migration, backup, restore, wsl]
    related_skills: [hermes-deployment, hermes-cron-ops]
---

# Hermes 数据迁移 / 备份（换电脑）

Trigger: user 要换电脑 / 迁移 Hermes / 备份技能与记忆 / 恢复另一台机器的配置。目标机器先装好 Hermes 本体（install.sh），再拷数据。

## 核心原则

- **只拷用户数据，不拷源码与缓存**。`~/.hermes/hermes-agent/`（重装）、`cache/`、`logs/`、`checkpoints/`、`audio_cache/`、`sandboxes/`、`node/`、`state-snapshots/`、`state.db`（500MB+，自动重建）——全部不迁。
- **先问清这台机器要哪部分**：本用户把「工作」和「个人」严格分开（见下），迁移前必须确认目标机器归属，再打对应包。

## 必拷清单（~/.hermes/ 下）

| 路径 | 说明 |
|---|---|
| `skills/` | 按领域分包（见下方分栏） |
| `memories/MEMORY.md` + `USER.md` | 明文 UTF-8，`§` 分隔条目；**read_file 会误报 "Binary file"（中文文本误判）**，用 `python3 -c "open(p,'rb').read(50)"` 验证。每个文件都是工作+个人条目混装——目标机只要单领域就重写文件，别整拷 |
| `config.yaml` | 模型/approvals/mcp_servers/平台配置 |
| `.env` | API keys + 业务凭据（可能含机器路径 /mnt/d/...，需审计） |
| `auth.json` | OAuth tokens / credential pools |
| `cron/jobs.json` | 任务定义（executions.db、output/ 历史可选） |
| `profiles/<name>/` | 每个 profile 是迷你实例：独立 config.yaml + skills/ + memories/ |
| `scripts/`、`mcp-servers/` | 自定义辅助脚本 |

## 技能三栏分包（本用户 2026-08 确认）

- **工作（目标工作机必带）**：`skills/dogfood/`（ai-audit-regression、direct-purchase-sql 含 generate_month_file.py、framework-*-sql、direct-purchase-deploy、supply-chain-push）、`productivity/government-procurement-ops`、`sdd-architect/`+`sdd-converge/`、`dws/`（钉钉）、`understand-anything/`、`devops/maven-offline-dependency`、`productivity/gitee-notes-repo`、software-development 工作子集（business-rule-*、code-change-automation、entity-to-sql、java-entity-sql、requirement-change-analysis、upgrade-doc-generator、java/springboot 规范、clean-arch/ddd/legacy/database-migrations、api-design、ai-sdd-workflow）
- **个人（留原机/按需）**：chongqing-home-buying、creative/（Remotion、AI周报视频、散文诗、小说）、remotion、media/、mlops/、gaming/、social-media/、research/（worldmonitor 股市、polymarket）、red-teaming、note-taking/obsidian、smart-home、yuanbao、productivity 的 ruankao-*、english-*、tutor 系列、pdf-study-pipeline、bilibili-comment-analyzer、grill-me、i-have-adhd、petdex、devops/freecodecamp-dev
- **通用（两边都建议带）**：autonomous-ai-agents/（hermes-agent、coding-agents）、devops/hermes-*、wsl-*、windows-*、proxy-*、kanban、webhook-subscriptions、skill-curation、web-search-fallback、mcp/、github/github-operations、email/himalaya、data-science/jupyter、productivity 办公类（docx/pdf/powerpoint/xlsx/ocr/nano-pdf/notion/linear/airtable/google-workspace/maps/teams-meeting-pipeline/writing-great-skills）、markdown-viewer、hyperframes、apikey-image-gen、grok-image-to-video、hermes-desktop-plugins、software-development 通用开发（tdd/systematic-debugging/debugging-tools/diagnosing-bugs/code-quality/simplify-code/development-planning/project-kickoff/code-generation/karpathy-guidelines/llm-app-backend/llm-json-output-validation/react-h5-frontend/react-vite-webapp/opencode-setup/git-server-ssh-setup/cursor-analytics）、SOUL.md、hooks/

## 打包（旧机器）

```bash
cd ~/.hermes && tar czf ~/hermes-migration/hermes-work.tar.gz <工作清单路径...> \
  memories config.yaml .env auth.json cron/jobs.json profiles/sdd-architect ...
```

按分栏列出路径即可；个人包、通用包同理分三个 tar.gz。**凭据包（.env/config.yaml/auth.json）传输建议加密**。

## 恢复（新机器）与验证

```bash
tar xzf hermes-work.tar.gz -C ~/.hermes/
hermes config check && hermes doctor
hermes mcp test mysql        # 验证工作库 MCP
hermes cron list             # 检查任务
hermes skills list           # 确认技能分类齐全
```

## 已知坑（2026-08 实测）

1. **MCP server 脚本可能在 ~/.hermes 之外**：config.yaml 的 mcp_servers 引用 `D:\mcp-server\mcp-mysql-python\server.py`（WSL 侧 /mnt/d/...）——Windows 侧目录需单独拷，新机器改路径。
2. **cron 任务里嵌的脚本路径会漂移**：job prompt 写死 `~/.hermes/skills/productivity/direct-purchase-sql/scripts/...`，技能重组后实际在 `dogfood/direct-purchase-sql/scripts/`。审计：`grep -o '~/.hermes/skills/[^ ]*' cron/jobs.json | sort -u`，逐条 `find ~/.hermes/skills -name <script>` 验证，用 cron edit 修正。详见 hermes-cron-ops。
3. **记忆文件误报 binary**：read_file 对中文 UTF-8 记忆文件报 "Binary file - cannot display"，实际是明文；直接 python3 读字节确认即可。
4. **skills/.archive/**：隐藏的归档目录，含旧版技能（如 direct-purchase-sql 旧版），一般不必迁。
