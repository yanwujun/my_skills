---
name: cli-browser-automation
version: 1.0.0
author: yanwujun
license: MIT
description: Use when 用 agent-browser CLI 做浏览器自动化：UI回归、抓取、内网站点测试。
metadata:
  hermes:
    tags: [browser, automation, agent-browser, qa, wsl]
    related_skills: [hermes-system-update, xcj-mallbase-show1-test]
---

# CLI 浏览器自动化（agent-browser）

## When to Use

- 用户要求写/跑 UI 回归脚本或浏览器自动化（终端侧，非 Hermes 内置 browser 工具）
- 需要在 shell 里打开页面、操作表单、截图、比对页面差异
- 测试政采内网站点（.gm 域名）的页面流程
- 给 Cursor/OpenCode 等编码 agent 配置浏览器操作能力
- 不适用：Hermes 会话内临时查网页（用内置 browser 工具）、纯 HTTP API 调用（用 curl）

从 shell 或编码 agent 驱动真实浏览器：`open → snapshot -i → 按 @ref 操作 → get 验证 → close`。

## 本机布局

- 用户侧 CLI：`agent-browser` → `~/.local/bin/agent-browser`（软链到 `~/.local/n/bin`，npm 全局 0.4x，PATH 首位）
- Hermes 自带旧版在 `~/.hermes/node/bin/agent-browser`（内置 browser 工具用）——**不动它、不向 Hermes 树同步**，两版并存，状态目录共享 `~/.agent-browser`
- 健康检查 `agent-browser doctor`（CLI/Chrome/daemon/网络/headless 启动一遍过）；Chrome 落后 stable 报 CVE 时跑 `agent-browser install` 升级内核

## 核心循环

```bash
agent-browser open <url> --session <name>     # 每 session 独立 daemon+浏览器，隔离调试不踩默认会话
agent-browser snapshot -i --session <name>    # 交互元素 a11y 文本快照，每个带 [ref=eN]
agent-browser click @e1 --session <name>      # 按 ref 操作
agent-browser get url --session <name>        # 验证结果
agent-browser close --session <name>
```

- **ref 只在快照时刻有效**：导航或 DOM 变化后必须重新 snapshot 再操作——旧 ref 指向的节点可能已不存在
- **点击语义是宁可失败不假成功**：目标隐藏/禁用/视口外/被遮挡（如 consent 弹层）会直接报错而非返回 success。报错时先关掉遮挡物、重拍快照再重试，不要以为点过了
- 版本配套文档：`agent-browser skills get core`（输出与当前安装版本匹配的用法）；MCP 形态 `agent-browser mcp`；给编码 agent 装技能桩 `npx skills add vercel-labs/agent-browser`

## 政采内网站点（.gm 域名）

直采商城/行采家等用内部 CA 证书，直接 open 报 `ERR_CERT_AUTHORITY_INVALID`：
- 快速通行：`agent-browser open https://<站点> --ignore-https-errors`（已验证 zc-mall.xcjshow1.gm 首页快照正常，登录/搜索/分类 ref 齐全）
- 更安全：`--ca-cert <内部CA路径>` 只信任指定 CA，拿到证书文件后优先切这个

## 常用命令组

- 捕获：`screenshot` / `pdf` / `record` / `diff`（页面差异比对，适合回归）
- 调试：`console` / `errors` / `network` / `a11y` / `react`
- 状态与登录：`cookies` / `storage` / `eval`；`--cdp` 或 `--auto-connect` 附加已登录的现有 Chrome 复用会话；`session`/`auth` 命令管理登录态库（auth vault）、域名白名单、`confirm/deny` 动作策略

## 安装/升级备忘

- `npm install -g agent-browser` 后 bin 在 `~/.local/n/bin`（不在 PATH）：需 `ln -sf ~/.local/n/bin/agent-browser ~/.local/bin/agent-browser` 才能直呼
- npm 12 拦 postinstall（allow-scripts 警告）不影响使用：包内 `bin/` 自带各平台二进制，Chrome 内核单独由 `agent-browser install` 下载
