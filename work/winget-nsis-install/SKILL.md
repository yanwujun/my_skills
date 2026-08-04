---
name: winget-nsis-install
description: 从 WSL 用 winget 或 NSIS 静默安装 Windows 桌面软件 — 包 ID 同名陷阱、0x80072efd 代理解法、/S /D= 静默安装与卸载、自定义安装目录
trigger: 用户要求安装/重装 Windows 桌面软件，且优先走 winget 或 NSIS 静默路径（与 windows-software-setup 互补：那个 skill 聚焦 Cloudflare 手动下载 + 计划任务，本 skill 聚焦 winget 与 NSIS 直装）
---

# Winget & NSIS Silent Install (from WSL)

从 WSL 安装 Windows 桌面软件的自动化路径。先试 winget，失败降级到 NSIS 静默安装。

## 用户环境约定

- **Windows 软件统一装到 `D:\baseSoftware\<AppName>`**（用户明确要求，C 盘不留应用）
- 拒绝需要管理员/sudo 的操作（winget settings 提权、UAC 提权安装都不可用）
- PowerShell `-NoProfile -Command` 每次执行都触发审批 → **把多个操作合并到一条命令里**，优先用 WSL 本地命令（curl、ls）探测，减少 powershell 调用

## 流程

### 1. winget 优先（最快路径）

```bash
winget.exe --version
winget.exe search <app> --accept-source-agreements   # 确认包 ID
winget.exe install --id <Id> --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
```

**同名陷阱**：search 结果可能有多个同名包，仔细核对 ID。实例：`Eugeny.Tabby`（终端）vs `TabbyML.Tabby`（AI 编程助手）。

### 2. 下载失败 0x80072efd → 代理问题

`InternetOpenUrl() failed / 0x80072efd` = WinINet 直连被墙或代理没跑。处理：
1. 探测代理：`curl -s -x http://127.0.0.1:8888 -o /dev/null -w "%{http_code}" https://github.com`（200=通，000=没跑）— 详见 proxy-network-debug skill
2. **不要用 `winget --proxy`**：该参数默认被禁用，需管理员运行 `winget settings --enable ProxyCommandLineOptions`，用户环境不可用
3. 代理恢复后：WSL curl 走代理下载到 Downloads，再 NSIS 静默安装（见下）

### 3. NSIS 静默安装 / 卸载 / 重装

electron-builder 打包的应用（Tabby、Cursor 等）是 NSIS 安装器：

```bash
# 静默安装（per-user 默认无需 UAC）
powershell.exe -NoProfile -Command "Start-Process -FilePath 'C:\...\setup.exe' -ArgumentList '/S' -Wait"

# 自定义目录：/D= 必须放最后、路径无空格时不加引号
powershell.exe -NoProfile -Command "Start-Process setup.exe -ArgumentList '/S','/D=D:\baseSoftware\Tabby' -Wait"

# 静默卸载（NSIS 卸载器同样支持 /S）
powershell.exe -NoProfile -Command "Start-Process -FilePath '<安装目录>\Uninstall <App>.exe' -ArgumentList '/S' -Wait"
```

### 4. 重装到自定义目录（常见需求）

```bash
# 一条命令完成 卸载→等待→重装，减少审批次数
powershell.exe -NoProfile -Command "Start-Process '...\Uninstall X.exe' -ArgumentList '/S' -Wait; Start-Sleep -Seconds 3; Start-Process setup.exe -ArgumentList '/S','/D=D:\baseSoftware\X' -Wait"
```

重装后：
- 开始菜单快捷方式会自动重建并指向新路径
- 旧路径 `%LOCALAPPDATA%\Programs\<App>` 常残留**空目录**（0 字节）→ `rmdir` 清理

## 验证

- 安装后确认 `search_files(pattern='<App>.exe', path='/mnt/d/baseSoftware/<App>')` 命中
- 确认旧位置无残留
- 启动应用验证：`powershell Start-Process 'D:\baseSoftware\<App>\<App>.exe'`

## Pitfalls

- **托盘进程存在 ≠ 代理可用**：GUI.for.SingBox / clash-verge-service 进程在跑但内核可能没监听任何端口。直接 curl 测端口，别查 netstat
- **msstore 源**可作为 GitHub 被墙时的备选（`--source msstore`），但很多工具不在商店
- winget 直连失败后别反复重试同一条命令 — 先修代理再继续
- 卸载器路径含空格（"Uninstall Tabby.exe"）→ PowerShell Start-Process 的 FilePath 必须加引号

## 参考文件

- `references/tabby-terminal.md` — Tabby 完整安装/卸载/中文配置实录（winget ID 陷阱、config.yaml locale）
