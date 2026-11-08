# 三方会话数据源手册(Hermes / Claude Code / Cursor)

## Hermes — `~/.hermes/state.db`(sqlite,权威源)

- 表:`sessions`、`messages`、`system_prompts`(还有 messages_fts 全文索引)
- `messages` 关键列:`session_id, role(user/assistant/tool), content, tool_calls(JSON数组), tool_name, timestamp(unix float), token_count`
  - tool_calls 结构:`[{"function": {"name": "skill_view", "arguments": "{\"name\": \"xxx\"}"}}]`(arguments 是嵌套 JSON 字符串)
- `system_prompts`:`hash + prompt`(完整系统提示词文本),`<available_skills>` 块 = 技能目录注入
- `~/.hermes/sessions/*.jsonl` 为遗留旧数据(仅早期少量),不要作为统计源

skill_view 使用统计骨架:
```python
import sqlite3, json, collections
con = sqlite3.connect("/home/administrator/.hermes/state.db")
sv = collections.Counter()
for (tc,) in con.execute("select tool_calls from messages where tool_calls like '%skill_view%'"):
    for c in json.loads(tc or "[]"):
        fn = c.get("function", {})
        if fn.get("name") == "skill_view":
            args = json.loads(fn.get("arguments", "{}"))
            if not args.get("file_path"):   # 带 file_path 的是加载 reference,不算技能首载
                sv[args.get("name", "?")] += 1
```

目录块测量 + 瘦身后验证(直接从源码重建):
```python
import sqlite3, re
con = sqlite3.connect("/home/administrator/.hermes/state.db")
prompt = con.execute("select prompt from system_prompts order by rowid desc limit 1").fetchone()[0]
block = re.search(r"<available_skills>(.*?)</available_skills>", prompt, re.S).group(1)
print(len(block))
# 重建验证(归档/禁用后):
import sys; sys.path.insert(0, "/home/administrator/.hermes/hermes-agent")
from agent.prompt_builder import build_skills_system_prompt
print(len(build_skills_system_prompt()))
```

- 插件开关:`hermes plugins disable/enable <name>`(写 config.yaml plugins.enabled/disabled,gateway 热重载;平台 hooks 需 `hermes gateway restart` 才彻底清除)
- 技能归档目录:`~/.hermes/skills/.archive/`(被 catalog 扫描排除);技能可见性机制:`skills.disabled`、`skills.platform_disabled`、SKILL.md frontmatter conditions(requires_tools/requires_toolsets/fallback_for_*/session_platforms)、focus 编码姿态自动把非编码分类折叠为仅名称

## Claude Code — `/mnt/c/Users/Administrator/.claude/`

- 会话:`projects/<项目目录变形名>/<uuid>.jsonl`,每行一个 JSON;type=user/assistant/attachment/queue-operation;子代理在 `<uuid>/subagents/`(统计主会话时跳过)
- 目录名是 Windows 路径的不可逆变形;真实 cwd 对照 `sessions/<pid>.json`
- assistant 行关键字段:`message.model`、`message.usage{input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens}`、content[] 里 `type=="thinking"` 块
- 斜杠命令调用:user 行文本中 `<command-name>/xxx</command-name>`
- **timestamp 是 ISO UTC(Z 后缀)**,切窗口前先 `.astimezone()`
- 单会话文件可跨月复用(resume/continue),用「gap>10min 切 burst」求活跃时长,burst 带日期再归属到某天
- 延迟配方:逐行时间差,「前一行→assistant 行」= 模型响应(含排队/思考),「assistant(tool_use)→user(tool_result)」= 工具执行;过滤 0<d<300s
- `settings.json`:env.ANTHROPIC_BASE_URL / ANTHROPIC_MODEL / CLAUDE_CODE_SUBAGENT_MODEL;**modelSettings.<model>.effortLevel 会覆盖全局 effortLevel**(高 effort → thinking 轮比例与延迟大增);permissions.defaultMode;`commands/` 与 `commands-archive/`(归档目录不被加载)
- CLAUDE.md 每会话全文注入;受 cron 模式保护不可直写,交互会话可改

## Cursor — `/mnt/c/Users/Administrator/` 与 AppData

- `.cursor/rules/*.mdc` frontmatter 三态:`alwaysApply:true`=每请求注入;`globs`=匹配文件在上下文时附加(**`**/*` 即全匹配=变相 always**);仅 `description`=agent-requested 按需
- `.cursor/skills/<name>/SKILL.md`:按需加载,目录只注入 name+description;`.cursor/commands/`:斜杠命令
- 会话库(WSL 访问注意 9P):
  - `AppData/Roaming/Cursor/User/workspaceStorage/<hash>/state.vscdb`(每个 ~1MB):表 ItemTable / cursorDiskKV(常空) / composerHeaders(常空);**直接 sqlite open 报 disk I/O error → 先 cp 到 /tmp 再查**
  - `AppData/Roaming/Cursor/User/globalStorage/state.vscdb`(~18GB):`composerHeaders`(composerId, workspaceId, createdAt/lastUpdatedAt 为 epoch ms, isSubagent, isArchived)+ `cursorDiskKV`(键 `bubbleId:<cid>:<bid>`,值为 bubble JSON)
  - 大库连接方式:`sqlite3.connect(f"file:{path}?immutable=1", uri=True)` — immutable 跳过锁,9P 上可查小表
  - **不要**在 cursorDiskKV 上做 `key LIKE 'bubbleId:<cid>:%'` 扫描(9P 上 >400s 超时);composer 级统计用 composerHeaders 就够
- 规则引用挖掘:工作区库 ItemTable value 里正则 `([a-z0-9\-\.]+)\.mdc`;实测会话中引用的几乎全是**项目级** `.cursor/rules`,全局规则趋零——全局规则的价值要单独论证
- 改规则前整目录备份(如 `~/.hermes/backups/cursor-rules-<日期>/`);模板类规则转 skill 时剥 .mdc frontmatter、补 `name/description` YAML(中文触发式描述)
