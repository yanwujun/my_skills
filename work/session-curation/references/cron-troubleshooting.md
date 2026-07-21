# Cron Job 排障 — Stale Pycache 导致 Import 错误

## 场景

Hermes 更新后，cron job 反复失败，但即时聊天会话正常。错误日志：
```
ERROR cron.scheduler: Error processing job <id>: cannot import name 'AIAgent' from 'run_agent'
ERROR cron.scheduler: Error processing job <id>: cannot import name 'model_forces_max_completion_tokens' from 'utils'
```

同时可能伴随工具注册警告：
```
WARNING tools.registry: Could not import tool module tools.browser_tool: cannot import name 'model_forces_max_completion_tokens' from 'utils'
```

## 根因

Gateway 进程（`hermes-gateway.service`）在一个长寿命进程中运行 Python 解释器。更新命令 (`hermes update`) 只替换了 `.py` 源码文件，但：

1. **进程内存** — 已经导入的模块在内存中保持旧版缓存
2. **`__pycache__/`** — `.pyc` bytecode 文件需要 Python 在下次 import 时重新生成，但如果进程不重启就永远不会重新 import

## 排查步骤

```bash
# 1. 看真实错误
grep "ERROR cron.scheduler" ~/.hermes/logs/agent.log | tail -5

# 2. 确认 gateway 已运行多久（比更新时间长说明是缓存问题）
ps aux | grep "hermes.*gateway" | grep -v grep
# 检查 Start 列 — 如果是几天前启动的，就是缓存问题

# 3. 确认源码中确实有该符号
grep -n "class AIAgent\|def model_forces_max_completion_tokens" \
  ~/.hermes/hermes-agent/run_agent.py ~/.hermes/hermes-agent/utils.py

# 4. 检查是否有另一个 Python 版本干扰
ls -la ~/.hermes/hermes-agent/__pycache__/*.cpython-*.pyc 2>/dev/null
# 出现两种不同的 cpython 版本号（如 311 + 312）说明环境有混合
```

## 修复

```bash
# 方案 A：清 pycache + 重启 gateway（推荐）
find ~/.hermes/hermes-agent -path "*/__pycache__" -type d | head -5
# 确认路径正确后：
find ~/.hermes/hermes-agent/__pycache__ -name "*.cpython-311.pyc" -delete
hermes gateway restart

# 方案 B：如果用户不允许 gateway restart，至少清 pycache，
# 等下次 gateway 自然重启（系统重启 / 手动重启 / 崩溃恢复）时生效
```

## 验证

gateway 重启后，等 cron tick 运行（每分钟一次），检查：
```bash
tail -20 ~/.hermes/logs/agent.log | grep "cron.*session-curation\|会话内容沉淀"
```

或手动触发一次：`hermes cron run dae335161198`

## 关联

- Hermes 的 cron scheduler 在 `~/.hermes/hermes-agent/cron/scheduler.py` 中使用懒加载模式：
  ```
  from run_agent import AIAgent  # 只在需要 LLM 路径时才 import
  ```
  这意味着即使 no_agent 类 job 正常，LLM 类 job 也会因这个懒加载失败。

- 工具注册失败是独立但不致命的表面症状——`tools.registry` 加载工具模块失败会 fallback，不会阻止进程启动，但会级联污染后续的 cron job import。
