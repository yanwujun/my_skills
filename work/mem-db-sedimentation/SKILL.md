---
name: mem-db-sedimentation
version: 1.0.0
author: yanwujun
license: MIT
description: Use when 执行mem-db沉淀升级Phase、读写mem.db、做检索/注入或改沉淀cron输出.
metadata:
  hermes:
    tags: [memory, sedimentation, sqlite, fts5, claude-mem]
    related_skills: [tripartite-sync, claude-conversation-curation, session-curation]
---

# mem-db 统一记忆沉淀库

借鉴 claude-mem 架构，把 Cursor / Claude Code / Hermes / OpenCode 的会话沉淀统一进一个 SQLite 库，替代「隔夜 cron → 平铺 markdown」的旧模式（实时捕获 + 分层索引注入 + 按需检索）。

## When to Use

- 用户说「继续 mem-db / 继续沉淀升级 / 执行 Phase N」，或要写迁移脚本、脱敏 gate、mem-search 检索、索引注入
- 任何向 `~/memory-db/mem.db` 写入或从中检索的会话
- 修改三个沉淀 cron（cur-conv-curation / claude-conv-curation / tripartite-sync）的输出落点或注入方式前
- 不适用：Hermes 自身 memory 管理（用 memory 技能）、三方同步的日常执行（用 tripartite-sync，本技能只管升级项目）

**事实源：`D:\项目\个人总结\claude-mem架构借鉴-记忆沉淀升级计划_2026-11-09.md`**（Phase 划分、验收标准、附录 A 完整源码架构笔记）。执行任何 Phase 前先读它，完成后回去勾进度——进度只记在计划文档，不在本 skill 重复维护。

## 固定位置

- 库与脚本：`~/memory-db/`（mem.db、schema.sql v1、scripts/ 下：fts5_probe.py 验收探针、redact.py 脱敏 gate + test_redact.py 单测、migrate_daily.py 日报迁移——幂等可重跑，`--reset` 全清重导）——WSL ext4，**禁止放 /mnt/d**（9P 跨系统 IO 性能灾难）。Phase 2 捕获端复用 gate 直接 import redact.py，不要重写规则
- claude-mem 参考源码：`~/ref/claude-mem`（浅克隆，只读参考；**不安装不运行本体**——hooks 侵入、默认遥测、安装器引导登录第三方云服务）
- 存量迁移源：`D:\平时处理文件\Cursor沉淀\` 与 `ClaudeCode沉淀\` 下的 `每日_*.md`（两种半结构化格式）

## 硬规则

1. **脱敏 gate 前置于入库**：内网 IP→192.168.x.x；uuid/password/secret/cert_sha256→REDACTED；`<private>` 包裹的内容永不存正文（private_flag=1 只留元数据）。宁丢勿漏。gate 单测夹具注意：真样密钥字面量（sk- 前缀等）写文件时会被运行时自动替换为 `«redacted:…»` 标记，断言用 `\S+` 通配才不受影响。
2. **检索路由**：查询 ≥3 字符走 FTS5 trigram MATCH，<3 字符走 LIKE title/body 兜底——trigram 对两字中文词是机制性 0 命中（已探针验证）。中文 FTS 不能照抄 claude-mem：它用默认 unicode61 不分中文词，语义检索全靠向量兜底。
3. **同步方向沿用 tripartite-sync 白名单**：Cursor→Hermes 单向、Hermes→外默认禁；mem-db 不得新开输出通道。
4. 改沉淀 cron（7:50/8:40/9:30 三个）只改产物落点，**调度时间不动**；日报 md 保留作人读产物。

## 架构要点（详见计划文档附录 A）

- 实体分层：sessions（平台会话 ID↔库 ID 双映射）/ observations（title + body 摘要 + narrative 全文，检索先索引后详情）/ session_summaries（固定分节 request/investigated/learned/completed/next_steps，不是自由文本）/ work_state（append-only 条目流，同名 key 最新值覆盖）
- FTS5 用 external-content + 同步触发器（索引不复制正文)；**已存在的 external-content 索引绝不重复回填**——会损坏 delete/update 记账；重建表后须重新挂触发器
- Python sqlite3 连接默认 `foreign_keys=OFF`：幂等迁移靠 DELETE session 级联清 observations，必须先 `PRAGMA foreign_keys=ON`，否则级联静默失效留孤儿行；`lastrowid` 在 cursor 上不在 connection 上
- 注入预算拟合：渲染→实测字符数→超预算按优先级逐条整项 drop（全文→summary→lastMessage→会话数减半→观察数减半，保底 1 条），只整条丢不腰斩；**统计报实际投递量而非查询量**；注入块之后还要拼接的横幅必须计入被测长度，事后追加会撑爆预算
- 检索四步：search（仅索引+ID）→ timeline（锚点前后时序）→ get_observations（批量 ≤100 ID）→ 原始工具输出兜底（仅当摘要回答不了）；另设**零参数自描述协议工具**（important_workflow 模式）让 agent 先读用法再检索，比塞 system prompt 可靠
- 迁移粒度：日报每个 `###` 小节 = 1 条 observation（title=小节头，body=首段摘要，narrative=小节全文）；「评估后不沉淀」节跳过。解析三坑：①必须跟踪 ``` 代码围栏——规则类小节正文常嵌 markdown 代码块，块内 `## ` 行会被误判为标题把 narrative 截断；②文件名有 `每日_YYYYMMDD.md` 与早期 `Cursor对话沉淀报告_YYYYMMDD.md` 两代，用 `(\d{8})\.md$` 宽匹配——窄 glob 会静默漏文件；③type 用标题+首段判（全文匹配过宽会误标），project 用全文判（提及即归属）

## Phase 2 捕获端预置知识

- **Cursor 已支持 hooks**（postToolUse / postToolUseFailure / stop），transcript 在 `~/.cursor/projects/<slug>/agent-transcripts/<UUID>/<UUID>.jsonl`，slug = cwd 去前导 `/`、`/` 和 `.` 全换 `-`；拼路径前先用 `^[A-Za-z0-9_-]+$` 校验会话 ID，防路径穿越
- **Claude Code hook stdout 有 10k 字符硬限**：超 1 个字符整块被替换成存盘 stub 且 hook 仍报成功（静默失败，上下文全丢）——注入内容必须主动拟合到限内并给尾部横幅留余量
- 失败的工具调用（error_message）入库须标 is_error——失败尝试不能被记成完成的工作
