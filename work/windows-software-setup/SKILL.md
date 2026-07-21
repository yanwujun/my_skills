---
name: windows-software-setup
description: 从 WSL 安装 Windows 桌面软件 — 处理 Cloudflare 防护下载、架构检测、静默安装、语言包部署
trigger: 用户要求安装任意 Windows 桌面应用（.exe/.msi），或需要从 WSL 中操作 Windows 软件部署
---

# Windows Software Setup

安装 Windows 桌面应用程序时，由于 WSL 运行在 Linux 环境，需要特别注意架构检测、下载方式、安装执行等环节。

## 工作流

### 1. 确认系统架构（关键第一步）

切勿假设 x64！先通过 WMI 检测：

```powershell
$cpu = Get-WmiObject Win32_Processor
switch ($cpu.Architecture) {
    9  { Write-Host "x64 (AMD/Intel)" }
    12 { Write-Host "ARM64" }
    5  { Write-Host "ARM (32-bit)" }
}
```

同时检查 `PROCESSOR_ARCHITECTURE` 环境变量确认。

### 2. 下载安装包

#### Cloudflare 防护的处理
- **claude.ai**, **docs.google.com** 等很多站点使用 Cloudflare 挑战
- 自动化工具（curl、PowerShell Invoke-WebRequest）会被拦截，收到 403 + "Just a moment..." 页面
- **解决方案**：让用户自己在 Windows 浏览器上打开下载页，点击下载，保存到本地
- 也可尝试用 browser 工具导航到页面后触发下载，但不保证成功
- **不要** 反复尝试自动化绕过 Cloudflare — 这行不通

#### 文件检查
下载后先确认文件大小合理、架构匹配。

### 3. 安装执行

直接在 WSL 中用 `powershell.exe Start-Process` 运行安装包可能失败（尤其 ARM64 安装包）。

**推荐方法：** 通过 Windows 计划任务运行

```powershell
$action = New-ScheduledTaskAction -Execute "D:\path\to\setup.exe" -Argument "/S /D=D:\target\dir"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "Administrator" -RunLevel Highest -LogonType Interactive
Register-ScheduledTask -TaskName "InstallApp" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
```

**备用方法：** 在用户桌面创建 .bat 文件，让用户双击执行

```powershell
$batContent = @"
@echo off
echo Installing...
start /wait D:\path\to\setup.exe /S /D=D:\target\dir
echo Done!
pause
"@
Set-Content -Path "C:\Users\Administrator\Desktop\install.bat" -Value $batContent
```

### 4. 安装后清理
- 删除计划任务: `Unregister-ScheduledTask -TaskName "InstallApp" -Confirm:$false`
- 可保留安装包在 D:\baseSoftware 下以便重装

## 常见问题

### Cloudflare 防护
- 症状：curl 返回 403, Invoke-WebRequest 返回 HTML 挑战页
- 处理：用户手动下载
- 工具链限制：`browser_click` 在 headless 模式下可能触发不了真实下载

### 架构不匹配
- ARM64 安装包在 x64 系统上: `0x800700D8` (ERROR_BAD_EXE_FORMAT)
- x64 安装包在 ARM64 系统上: 同样会报错
- 始终安装前检测架构（查 CPU Name 而非仅 Architecture 值，因为两者都可能返回 64-bit）

### MSIX 引导程序（Bootstrapper）模式
- 很多现代 Windows 应用（Claude Desktop, Teams 等）的安装器是一个小引导程序（~6-7MB），启动后再下载真正的 MSIX 包（~200MB+）
- `/D=` 安装目录参数对 MSIX 无效 — MSIX 总是安装到 `C:\Program Files\WindowsApps\`
- 引导程序日志位于 `%TEMP%\ClaudeSetup.log`，是调试的第一信息来源
- 日志中可见下载进度、SHA256、代理拦截检测等信息

### GFW / 代理问题（中国网络环境）
- 引导程序下载 MSIX 时常见错误：
  - **TLS handshake timeout** — 直连被墙，需开代理
  - **Proxy interception detected (HTTP 403)** — 代理/VPN 反而拦截了下载，需关闭代理
- 正确做法：关代理试 → 不行就开代理试 → 都不行就用户在浏览器手动下载 MSIX
- MSIX 下载 URL 示例：`https://api.anthropic.com/api/desktop/win32/x64/msix/latest/redirect`

### 权限不足
- 普通用户无法安装到 Program Files / D:\\baseSoftware
- 使用计划任务 + RunLevel Highest + LogonType Interactive 来提权
- MSIX 安装时引导程序会自提权（self-elevating），但需要用户确认 UAC 弹窗

## Pitfalls

- 不要从 WSL 直接 `Start-Process` 非 x64 的 exe — WSL interop 层不模拟 ARM64 执行
- 不要假设系统是 x64 — 现在是 ARM Windows 时代（Surface Pro X, Snapdragon X Elite 等）
- 下载链接提取后不要再从 WSL curl — Cloudflare cookie 不会跨进程继承
- 语言包安装脚本可能需要管理员权限 — 通过 .bat 双击触发 UAC 提权最稳妥
- MSIX 引导程序的 `/D=` 参数**不生效** — 如果用户指定了安装目录但最终装到 WindowsApps，需要解释这是 MSIX 机制决定的
- 如果引导程序反复失败，直接取 MSIX URL 让用户在浏览器下载 `.msix` 文件后手动双击安装

## 参考文件

- `references/schtasks-install-method.md` — 通过计划任务安装的完整模板和常见错误码
- `references/architecture-detection.md` — 架构检测命令和架构值对照表
- `references/bootstrapper-msix-debugging.md` — MSIX 引导程序调试、日志解读、常见失败场景
