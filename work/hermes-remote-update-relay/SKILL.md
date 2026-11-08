---
name: hermes-remote-update-relay
version: 1.0.0
author: administrator
license: MIT
description: "Use when 群聊协作帮远程机器升级Hermes后端。增量bundle经Z盘中继，含角色分工与验证步骤。"
metadata:
  hermes:
    tags: [hermes, update, bundle, collaboration, remote, nas, relay]
    related_skills: [hermes-system-update]
---

# 远程 Hermes 接力更新（双 agent 群聊协作）

## When to Use

- 用户在群聊里要求帮另一台机器的 Hermes agent（如 @default-10-30-2-166-9119）更新后端，且对方 GitHub 不通。
- 远程 agent 报出老版本 `vgit.<hash>` 并请求 bundle / 传输协助。
- 仅适用于源端=本 WSL 机器、目标端=能自己执行命令的远程 agent 的协作模式；本机自更新用 hermes-system-update。

源端（本机 WSL，GitHub 可通）打增量 git bundle，经共享通道传给目标端 agent（GitHub 不通），目标端自己执行升级命令。2026-11-03 与 10.30.2.166 完整验证过一次（跨 7119 commits，v0.21.1+9305.g6059d35）。

## 角色与机器事实

- **源端 = 本机**：WSL `192.168.2.166`，完整 hermes-agent 仓库在 `~/.hermes/hermes-agent`，GitHub 走代理 `HTTPS_PROXY=http://127.0.0.1:8888`。
- **目标端 = 远程 agent**（已知：`10.30.2.166`，装在 `/usr/local/lib/hermes-agent`，Python 3.14.x）：自己跑命令；本机对它 **22 端口可达但无 SSH 密钥**，不能替它执行。
- **共享通道 = Z 盘（NAS）**：目标端把 Z: 挂为 `/workspace/`（NFS `10.30.2.2:/nas1/agentWorkspace/GM20220407`），即 `Z:\hermes-update\x` = `/workspace/hermes-update/x`。

## 流程

### 1. 让目标端报状态（一条消息问全）

```bash
git remote -v && git rev-parse HEAD
timeout 15 git ls-remote https://github.com/NousResearch/hermes-agent.git HEAD  # 直连测试
node --version && python3 --version && hermes --version
```

### 2. 源端评估差距

```bash
cd ~/.hermes/hermes-agent && HTTPS_PROXY=http://127.0.0.1:8888 git fetch origin --tags
git rev-list --count <their-hash>..origin/main        # 落后多少 commit
git show origin/main:package.json | grep -A3 engines  # 当前 Node 硬要求（2026-11 时 >=26，会移动）
```

### 3. 先试零成本路径

目标端 remote 若是 ghfast.top 之类镜像且 403，**不代表 GitHub 直连不通**——让它先测直连 ls-remote；通了就 `git remote set-url origin https://github.com/NousResearch/hermes-agent.git && git pull`，整个 bundle 流程免掉。

### 4. 打增量 bundle（知道目标 commit 时永远优先于全量）

```bash
git bundle create hermes-inc-<hash>.bundle <hash>..origin/main
git bundle verify hermes-inc-<hash>.bundle   # 应 "okay"；prerequisites 都是 <hash> 祖先
sha256sum hermes-inc-<hash>.bundle           # 发给目标端核对
```

体量参考：7119 commits → 36MB（全量 main+tags 约 670MB）。不带 tags → 目标端升级后版本显示 `vgit.<newhash>`，属正常。

### 5. 传输（按优先级）

1. **Z 盘/NAS**（已验证）：WSL 挂不上 /mnt/z，两跳走：`cp` 到 `/mnt/d/hermes/` → PowerShell 单行 `Copy-Item 'D:\hermes\<f>' 'Z:\hermes-update\' -Force` + `Get-FileHash -Algorithm SHA256` 核对 → 目标端从 `/workspace/hermes-update/` 拿。
2. **HTTP 兜底**（未验证入站可达）：bundle 目录里 `python3 -m http.server 18642 --bind 0.0.0.0`（background），目标端 `wget http://192.168.2.166:18642/<f>`。可能被 Windows/Hyper-V 防火墙拦。
3. **SSH 推送**：目标端 22 开着，但需要它先把源端公钥加进 authorized_keys 并报用户名，才能 scp。

### 6. 目标端应用（发给它的命令清单）

```bash
sha256sum <bundle>                     # 对源端给的 hash
cd /usr/local/lib/hermes-agent
git status -s                          # 必须干净；有本地补丁先确认是否已上游合并
git bundle verify <bundle>
git fetch <bundle> refs/remotes/origin/main
git reset --hard FETCH_HEAD
# 依赖装进 hermes 实际用的 python 环境（3.14.x），不是系统 python
hermes config migrate                  # ⚠️ 需 Node >=26 在 PATH（10.30.2.166 实测），先升 Node 再 migrate
systemctl restart hermes-gateway       # 别用 CLI restart，离线会挂在依赖安装；目标端若是 --user 单元则用 systemctl --user
```

### 7. 收尾

- 目标端确认升级成功后：杀 HTTP 服务、删 `/mnt/d/hermes/` 和 scratch 临时副本；`Z:\hermes-update\` 那份**留着**（其他机器卡同一 commit 可复用）。
- 提醒目标端把 **Node 升到 engines 要求**（>=26）：这不只是 Web UI/桌面/TUI 的事——目标端实测 **`hermes config migrate` 本身就需 Node 26 在 PATH**，所以 Node 升级应排在第 6 步应用流程之内（migrate 之前），不是事后补。
- 让目标端 agent 把"应用侧"经验沉淀进**它自己的**技能库（两边技能不共享）。10.30.2.166 侧对应技能名：`hermes-update-target`。

## Pitfalls

- **lifecycle_guard**：目标 agent 在自己 gateway 进程内跑 `pip install`/`hermes update`/`hermes gateway restart` 会被拦 → 让它用 systemd-run 脱离进程域，或请用户手动终端执行。
- **`hermes gateway restart` 离线挂死**：CLI restart 内部触发依赖安装 → 一律 `systemctl restart hermes-gateway`。
- **config migrate 报 `_configurable_keys` 导入错误**：升级本身已成功，旧进程内存态问题，新进程里重跑 `hermes config migrate` 即可。
- 大跨度升级后目标端若有 Web UI/MCP 异常，第一诊断点是它的 `~/.hermes/logs/mcp-stderr.log`（详见 hermes-system-update）。

## Related

- `hermes-system-update`：本机更新全流程 + 全量 bundle 法 + 升级后修复坑集。
- 目标侧对位技能（10.30.2.166 机器上）：`hermes-update-target` —— 含分批装依赖、Pillow 冲突、pm repair 超时、launcher 坑等应用侧细节。
