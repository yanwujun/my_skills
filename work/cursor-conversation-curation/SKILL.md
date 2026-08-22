---
name: cursor-conversation-curation
description: 分析 Cursor 会话沉淀规则。Use when 分析 Cursor 对话、沉淀 Cursor skill/规则时。
version: 1.0.0
metadata:
  hermes:
    tags: [cursor, curation, skill-management, automation]
---

# Cursor 会话沉淀 — 每日自动分析

分析用户 Cursor 里的对话，提炼可复用的业务规则/技能/偏好，沉淀到 Cursor 规则体系。由 cron 每日触发（monitor 模式，无新会话零 token 静默）。

## 数据源（关键认知）

- **用 `conversation-search.db`，不要碰 `state.vscdb`**
  - `state.vscdb` = 14GB，Cursor 运行中锁定，复制极慢
  - `conversation-search.db` = 61MB，含全部会话全文（FTS 索引），可安全复制
  - 路径：`/mnt/c/Users/Administrator/AppData/Roaming/Cursor/User/globalStorage/conversation-search.db`
- 表结构：
  - `conversations`：会话元数据（fts_rowid, id, title, updated_at 毫秒, ...）
  - `conversation_fts_content`：全文（id = conversations.fts_rowid, c0=title, c1=body）
  - body 含用户消息 + 助手回复 + 思考过程，无结构化分隔，靠内容分析
- 其他库价值有限：`ai-code-tracking.db`（ai_code_hashes 15 万行，无对话内容，跳过）

## 提取脚本

`~/.hermes/scripts/cursor_conv_daily.py`（cron monitor 模式）：

- 复制 db → 增量提取 `updated_at > 水位` 的会话（限 40 个，正文预览 600 字符）→ 写 `/tmp/cursor_conv_daily/latest_summary.md` + `latest.json`
- **水位**：`~/.hermes/state/cursor_conv_last_ts`（毫秒）。脚本提取后立即推进（agent 失败也不重复提取）
- 输出：有会话 `NEW_SESSIONS:N DATE:yyyy-mm-dd`；无会话固定 `NO_NEW`（monitor hash 不变 → 跳过 agent，零 token）
- 首次运行回退 72h；空标题但正文 > 300 字符的会话也纳入

## 分析流程（agent 执行）

1. 读 `/tmp/cursor_conv_daily/latest_summary.md`（每条 600 字符预览）
2. 有价值会话可读 `latest.json` 或直接从 conversation-search.db 取完整 body
3. 提炼维度（按价值排序）：
   - **用户纠正过的地方**（最有价值，明确预期）→ 规则候选
   - 反复出现的业务规范/技术约束 → 规则候选
   - 新任务类型及其标准流程 → 流程候选
   - 用户显式表达偏好（语言/格式/粒度）→ 偏好候选
4. 判断是否已覆盖：读现有规则文件，避免重复沉淀（宁缺毋滥）

## 沉淀目标（按规则类型分流）

| 规则类型 | 写入目标 | 方式 |
|---|---|---|
| SQL/表结构/平台编码/数据操作 | `~/.cursor/skills/platform-sql-kit/SKILL.md` | patch 追加小节 |
| 全局约定/被纠正偏好/纪律 | `~/.cursor/rules/conventions.mdc` | patch 追加小节 |
| 独立方法论（审核分析/接口核对等） | `~/.cursor/skills/<name>/SKILL.md` | 新建 |
| 会话统计/日报 | `D:\平时处理文件\Cursor沉淀\每日_YYYYMMDD.md` | write_file |

**注意**：目标文件在 Windows 侧（`/mnt/c/Users/Administrator/.cursor/...`），write_file/patch 用 WSL 路径即可。

## 沉淀判断标准（宁缺毋滥）

- 会话必须 ≥5 条消息交互且有实质内容
- 用户明确纠正/表达过预期 → 沉淀
- 规则必须能独立于会话上下文被理解
- 50% 把握不确定 → 不沉淀
- 与既有规则重复 → 不沉淀

## 已知坑

- **cron 模式**：`execute_code` 完全 blocked；`terminal` 的 python `-c` 需审批 → 数据分析一律用脚本文件（.py），不用内联命令
- **monitor 死循环陷阱**：脚本输出含日期 → 每天 hash 变化 → 每天触发 agent。这是**特性**：确保每天至少跑一次分析。但必须让水位推进逻辑在脚本内完成，否则 agent 失败会无限重复
- **WAL 文件**：复制 db 时 .db-wal 不复制没问题，SQLite 读快照时自动合并已提交数据；Cursor 运行中复制是安全快照
- **标题为空**：1228/2170 会话标题为空，过滤时用正文长度兜底
- **DeepSeek 余额**：子代理曾 402 中断 → 主会话直接补分析，不要重派子代理

## 手动运行

```bash
# 手动触发脚本（不经过 agent）
python3 ~/.hermes/scripts/cursor_conv_daily.py

# 手动触发 cron 任务立即跑一次
cronjob(action='run', job_id='<id>')
```

## 首次全量分析（一次性）

若需全量（2170 会话）分析：删除水位文件后跑脚本 → 取最近 40 个；或用 execute_code 直接查库（参考本 skill 数据源章节），派并行子代理分片深挖（每片 30 会话），主会话补齐失败片。
