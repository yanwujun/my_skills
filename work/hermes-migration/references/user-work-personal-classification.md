# 用户技能/记忆 工作 vs 个人分类基线（2026-08 实测）

> 用户身份：政府直采商城/框架协议 QA/dev。分类用于迁移打包，随时可迭代——拿不准的技能列给用户确认。

## 技能分类（~/.hermes/skills/）

### 🏢 工作（迁移目标机器必带）
- `dogfood/`（核心）：ai-audit-regression、direct-purchase-deploy、direct-purchase-sql（含 generate_month_file.py）、framework-audit-sql、framework-contract-sql、supply-chain-push
- `productivity/government-procurement-ops`、`productivity/gitee-notes-repo`（公司 Gitee shenbufan）
- `sdd-architect/`、`sdd-converge/`（SDD 方法论全套）
- `dws/`（钉钉）、`understand-anything/`（CodeGraph 代码分析）、`devops/maven-offline-dependency`
- `software-development/` 子集：business-rule-graph/semantic-conflict/summarize、code-change-automation、entity-to-sql、java-entity-sql、requirement-change-analysis、upgrade-doc-generator、java-coding-standards、springboot-patterns、jpa-patterns、springboot-security、clean-arch-rules、ddd-rules、legacy-code-rules、database-migrations、api-design、ai-sdd-workflow

### 🏠 个人（留原机/按需）
- chongqing-home-buying、creative/（Remotion/AI周报视频/散文诗/小说/comfyui/manim 等）、remotion、media/、mlops/、gaming/、social-media/、research/（worldmonitor*/polymarket/arxiv）、red-teaming/godmode、note-taking/obsidian、smart-home/openhue、yuanbao
- productivity 学习类：ruankao-*、english-*、econ/iching/philo/physics-tutor、pdf-study-pipeline、bilibili-comment-analyzer、grill-me、i-have-adhd、petdex
- devops/freecodecamp-dev

### 🔧 通用（两边都带）
- autonomous-ai-agents/（hermes-agent、coding-agents）、devops 其余（hermes-*、wsl-*、windows-*、proxy-*、kanban、skill-curation、webhook-subscriptions、web-search-fallback、python-ci-fix）、mcp/、github/、email/、data-science/
- markdown-viewer、hyperframes、apikey-image-gen、grok-image-to-video、hermes-desktop-plugins
- productivity 办公类：docx、pdf、powerpoint、xlsx、ocr-and-documents、nano-pdf、notion、linear、airtable、google-workspace、maps、teams-meeting-pipeline、writing-great-skills
- software-development 通用流程：tdd-workflow、systematic-debugging、debugging-tools、diagnosing-bugs、code-quality、simplify-code、development-planning、project-kickoff、code-generation、karpathy-guidelines、llm-app-backend、llm-json-output-validation、react-h5-frontend、react-vite-webapp、opencode-setup、git-server-ssh-setup、cursor-analytics

## 工作版记忆筛选

MEMORY.md / USER.md 是 § 分隔整体文件。工作版保留工作+通用条目：

- **MEMORY.md 剔除**：软考/英语推送、创作路径（D:\项目\个人总结）、F:\音乐、视频:Remotion、smart-learn-app、novel-learn、worldmonitor 股市、购房
- **USER.md 剔除**：B站关注、股票持仓、写作偏好
- **保留核心**：编码约定（SQL路径/saleAgent/coding agent/occurPlatCode/Redis禁JVM锁/MyBatis foreach）、供应链 OAuth2、框架协议AI审核参数、b-r-g、Cursor Rules、Win机器/网络盘、WSL interop+QQ推送约定、代理配置、WSL铁律、npm/CLI踩坑、用户命令禁区、代码分析流程、SDD方法论偏好、新项目调研偏好

## cron 决策（用户确认过）

| 任务 | 归类 | 备注 |
|---|---|---|
| 月度SQL工作文件生成 (6b1895) | 工作 ✅ | 必带；脚本路径 productivity→dogfood 已修正 |
| 会话内容沉淀-每日分析 (dae335161198) | **必要** ✅ | 用户明确纠正过"还是必要的"（Hermes 自我学习机制） |
| skill同步检查-每周 (672de1fcd444) | 个人 ❌ | GitHub 个人仓库备份；曾 TimeoutError 失败 |
| 软考/英语推送等 | 个人 ❌ | 已禁用，不带 |

## 打包产物结构（D:\hermes-migration\）

- hermes-work.tar.gz（2.1M/531条）+ hermes-common.tar.gz（637K/429条）
- hermes-迁移清单.md + work-memories/（工作版记忆源文件）+ work-cron/（工作版任务源文件）
