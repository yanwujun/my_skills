---
name: session-curation
description: "每日自动分析前一天会话内容，判断是否需要沉淀为记忆(memory)、技能(skill)或脚本(script)。跟踪已处理会话的 last_active 时间戳，避免重复扫描和浪费token。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [curation, session-analysis, memory, skill-management, automation]
    related_skills: []
---

# Session Curation — 会话沉淀自动化

每日自动扫描前一天（或上次运行以来）的新/变更会话，分析内容价值，自动沉淀到记忆/技能/脚本。

## 核心逻辑

```
Phase 1: 发现会话
    session_search() 浏览模式 → 获取最近 3 个会话（不一定全量）
    +
    session_search(query="user OR assistant", limit=10, sort="newest") → discover 模式补全历史会话
    │
    ├─► 用 grep -oP 提取所有 session_id（cron 下 execute_code blocked，用 terminal grep 代替）
    │    对比 state 文件：session_id 不在 state 中 → 新会话
    │                    last_active > state 中的记录 → 有更新的会话
    │    跳过 source=cron 的会话
    │
Phase 2: 逐条 scroll 分析
    ├─► session_search(session_id=..., window=5-10)
    │    读取 bookend_start → 了解会话目标
    │    读取 bookend_end   → 了解会话结果
    │    读取 messages      → 了解交互过程
    │
    ├─► 分析内容，判断沉淀类型：
    │    ├ A. 用户偏好/环境事实/重复纠正 → memory
    │    ├ B. 可复用的工作流/命令序列 → skill
    │    └ C. 复用的脚本/工具函数 → skill 内建 scripts/
    │
Phase 3: 更新状态
    └─► write_file 写回 state 文件：标记已处理，记录 last_active、actions_taken
```

> **Cron 模式特别提醒**：`execute_code` blocked，`terminal -c` 需审批。用 `grep -oP` + `sort -u` 提取字段，用 `tail -c N` 读大文件尾部。详见踩坑记录。

## 沉淀判断标准

### A. 沉淀到记忆 (memory)

**两种存储后端可选：**

1. **Hermes 内置 memory**（默认）— 容量有限（~2,200字符 user + ~1,375字符 profile），适合高价值偏好和关键环境事实
2. **mem0 MCP Server**（可选，需提前配置）— 基于 Qdrant + fastembed 的向量存储，容量几乎无限，支持语义搜索。工具名 `mcp_mem0_add_memory` / `mcp_mem0_search_memories` 等。适合大量知识点、文本材料等需要语义检索的内容

**选择策略**：用户偏好/环境事实 → Hermes 内置 memory；大量结构化知识（如教材内容、技术参考） → mem0 MCP Server

**当会话揭示了以下内容时：**
- 用户明确说"记住了"、"以后就这样"、"不要XXX"
- 用户纠正了你的行为方式（沟通风格、命名习惯、技术偏好）
- 发现了环境事实（已安装的工具、项目路径、配置细节）
- 用户偏好（输出格式、语言习惯、工作流程）

**保存方式：** 使用 `memory` 工具，选择合适的 target（user/profile/memory）

**示例：** "用户要求所有安全提示用中文提问" → memory target=user
          "项目A的测试数据库地址是192.168.x.x:3306" → memory target=memory

### B. 沉淀到技能 (skill)
**当会话建立了以下内容时：**
- 一个可复用的多步骤工作流（3+步），适合下次复用
- 某个特定领域的问题排查套路
- 一个非显而易见的安装/配置过程
- 错误修复方案，将来可能再次遇到

**保存方式：** 使用 `skill_manage` 工具创建或更新 skill

**示例：** "如何排查 WSL 下 maven 构建失败" → 创建 wsl-maven-build skill
          "直采商城环境启动顺序" → 创建 direct-purchase-env-test skill

### C. 沉淀到脚本 (script)
**当会话产生了以下内容时：**
- 一个 Python/bash 脚本，日后会重复使用
- 一个复杂的命令行管道或数据处理逻辑
- 数据库查询模板或数据修复脚本

**保存方式：** 创建 skill 并将脚本放在 scripts/ 子目录

**不沉淀的情况：**
- 闲聊、问候、简单问答
- 一次性的文件读取或查看操作
- 只涉及当前会话上下文的临时操作
- 用户只是在测试功能或学习使用

### 质量门槛
- 会话必须有至少 5 条以上的消息交互
- 必须有实质性的用户反馈或操作结果
- 沉淀内容必须能独立于会话上下文被理解
- 如果有50%的把握不确定 → 不沉淀（宁缺毋滥）

### 批量首次扫描 vs 每日增量扫描

**首次运行**（state 文件为空的场景）：
- 可能一次性处理 10+ 个历史会话
- 此时内存快速填满，必须严格执行以下内存容量管理
- 优先沉淀影响深远的（用户偏好 > 环境事实 > 工作流）
- 可以分多次运行完成（state 记录已处理的 session_id 保证不重复）

**每日增量运行**（state 已有记录的场景）：
- 通常 0-3 个新会话需要处理
- 内存不会快速填满，正常判断即可

## 重要：内存容量管理（必读）

memory 工具有容量限制（~2,200 字符）。如果达到上限，`memory action=add` 会直接失败并返回 current_entries 列表。

### 写入前检查流程

在调用 `memory` 工具 **之前**，先读取当前记忆状态（从已知的记忆数据中获取 usage 百分比）：

1. **usage < 90%** → 直接 add，安全
2. **usage >= 90%** → 拒绝 add，改为 replace：
   a. 判断新内容是否可以合并到已有条目中（找语义最接近的）
   b. 如果可以合并：用 `memory action=replace` + `old_text=目标条目的唯一子串` + 更新的完整内容
   c. 如果无法合并（全新类型的信息）→ **跳过本次沉淀**，在报告中说"记忆已满，跳过 N 条"
3. **usage >= 98%** → 标记"记忆严重不足"，跳过所有 memory 沉淀，只做 skill/script 沉淀

### 合并策略（用 replace 代替 add）

当需要合并时：
- 先找已有的相关条目（如 note 仓库条目已有 GitHub/Gitee 信息，加入新仓库信息就合并进去）
- 旧内容变短的同时新内容加入，总长度不增或微增
- 示例：一条"note仓库 ~/note(gitee:shenbufan/note)" 合并 "skills仓库 D:\skills" → 合并为 "note ~/note(gitee) + skills D:\skills独立仓库"

### user 目标同样受限

`target=user` 的画像存储也有字符限制（~1,375 字符）。同样需要检查后再写入。

## 参考文件

- `references/analysis-tips.md` — 长会话处理、快捷判断、记忆合并示例等实操技巧
- `references/cron-troubleshooting.md` — 定时任务失败的排障套路（pycache 过期导致 import 错误等）

## 踩坑速查

- **Cron 模式工具受限**：`execute_code` blocked，`terminal -c` 需审批。用 `grep -oP` + `tail -c` 代替 Python 解析。
- **session_search() 浏览只返回 3 条**：需追加 `session_search(query="...", limit=10, sort="newest")` discover 调用补全。
- **cronjob 工具不可用**：用 state 文件的 `last_run_at` 代替。
- **Gateway pycache 过期**：更新后 cron 报 import 错误 → 清 `__pycache__` + `hermes gateway restart`。

完整排障流程见 `references/cron-troubleshooting.md`。

## 定时任务配置

```bash
cronjob action=create \
  name="会话内容沉淀-每日分析" \
  schedule="0 8 * * *" \
  skills='["session-curation"]' \
  prompt="今天是【当前日期】。加载 session-curation skill。\
\
任务：分析昨天及自上次运行以来所有新/变更的会话内容，自动沉淀有价值内容。\
\
步骤：\
1. 先用 cronjob action=list 列出所有 cron jobs，找到本 job（'会话内容沉淀-每日分析'）的 job_id 和 last_run_at\
2. 读取 state 文件：scripts/curation_state.json（skill 内建脚本）\
3. 用 session_search() 浏览模式获取所有会话\
4. 对比 state 文件，筛选出：\
   a. session_id 不在 state 中的（全新会话）\
   b. last_active > state 中记录的时间戳（有更新的会话）\
5. 对每个符合条件的会话：\
   a. 用 session_search(session_id=..., window=5) 查看内容\
   b. 阅读 bookend_start 了解会话目标，bookend_end 了解结果\
   c. 阅读 messages 了解交互过程\
   d. 按 skill 中的'沉淀判断标准'分析是否值得沉淀\
   e. 如果需要沉淀到 memory：先查记忆容量，按 skill 中"内存容量管理"章节处理（usage<90%才add，>=90%改为replace合并，>=98%跳过）\
   f. 如果需要沉淀到 skill：直接调用 skill_manage 工具\
   g. 记录到 state 文件\
6. 更新 state 文件的 last_run_at\
7. 状态文件写回用 write_file 工具\
8. 最终输出摘要：处理了 N 个会话，沉淀了 M 项内容\
\
约束：\
- 不要分析 cron job 自身的会话（source=cron 的跳过）\
- 每个会话只沉淀最有价值的 1-2 项内容，不要过度沉淀\
- 宁缺毋滥，不确定就不沉淀\
- 必须记录每个会话的 last_active 到 state，即使无沉淀，确保下次不重复扫描\
- state 文件写回前先 read_file 确认最新状态（可能有并发写入）"
```

