# OpenCode 工作空间模式

## 多项目工作空间创建流程

### 1. 先分析结构，再委托分析

```yaml
步骤:
  1. 用 CodeGraph / search_files / terminal 分析各项目的目录结构
  2. 用 `opencode run` 创建工作空间（不要用 bare mkdir）
  3. 用 CodeGraph MCP 做深度调用链分析（比 OpenCode 快且准确）
  4. 用 `opencode run -f project1 -f project2` 做跨项目分析
```

### 2. 创建工作空间目录+readme

```bash
# 方式A：让 OpenCode 自己建目录+写文件
terminal(command="""
  opencode run 'Create readme.md recording project paths and purpose'
""", workdir="/target/workspace-dir", pty=true, timeout=120)

# 方式B：更新现有 readme（追加新项目）
terminal(command="""
  opencode run 'Append these 3 new projects to readme.md...' -f ./readme.md
""", workdir="/target/workspace-dir", pty=true, timeout=60)
```

readme.md 格式示例：
```markdown
# 工作空间名称
- **工作空间名称**: XXX
- **关联项目1**: path/to/project1
- **关联项目2**: path/to/project2
- **用途**: 分析XXX
- **创建日期**: 2026-06-15
```

### 3. 启动 Web UI

```bash
# 先在目录下启动，确保 cwd 正确
terminal(command="opencode web --port 4096",
  workdir="/mnt/d/workspace", background=true)

# 验证端口和进程工作目录
ss -tlnp | grep 4096
ls -la /proc/$(lsof -ti:4096)/cwd   # 确认指向 workspace 目录
```

### 4. 挂载关联项目进行分析

```bash
# 用 -f 挂载项目文件/目录上下文
terminal(command="""
  opencode run 'Analyze cross-project impact' \
    -f /path/to/proj1 -f /path/to/proj2 -f /path/to/proj3
""", workdir="/workspace", pty=true, timeout=180)
```

### 5. Web UI 访问

- URL: `http://127.0.0.1:4096/Lw/session`
- 左侧导航栏显示工作空间名称
- 页面底部的 "Ask anything" 文本框输入需求

## 端口冲突处理

```bash
# 1. 找出占用端口的旧进程
lsof -ti:4096
# 2. 确认其工作目录（可能不是你期望的）
ls -la /proc/$(lsof -ti:4096)/cwd
# 3. 杀死旧进程
kill $(lsof -ti:4096)
# 4. 重新启动（从正确的 workspace 目录）
cd /workspace && opencode web --port 4096
```

## 注意事项

- **OpenCode 的"工作空间"就是当前进程的工作目录**，Web UI 中没有独立的"创建工作空间"按钮
- **`opencode run` 带中文路径或提示词时会触发安全扫描**（Confusable Unicode），需要用户批准
- **`opencode run` 超时**：大分析任务建议用 `--agent plan` 或在 60-120 秒内分步完成
- **`opencode web` 是持久服务**，`opencode run` 是一次性命令 — 根据场景选对模式
- **项目关联通过 readme.md 记录**，OpenCode 本身没有显式的"添加项目到工作空间"命令
