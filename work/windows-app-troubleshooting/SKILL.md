---
name: windows-app-troubleshooting
description: Windows 桌面应用故障排查（闪退/崩溃/对话框异常）— 从 WSL 用 PowerShell 查事件日志 faulting module、CLSID 反查 Shell 扩展归属、定位元凶。当用户报"XX软件在 Windows 上闪退/崩溃/下载时崩/弹窗后崩"时使用。
---

# Windows 桌面应用故障排查（从 WSL）

## 触发场景
- 用户报 Windows 上软件闪退/崩溃：钉钉、微信、Explorer、任意桌面应用
- 症状：点按钮→弹窗→闪退；下载文件时崩；右键崩；对话框异常

## 核心方法论

### 第一步：区分"应用问题" vs "系统/Shell 问题"
- **对话框样式对照测试**：打开记事本 → Ctrl+S。
  - 记事本弹 Win11 新样式、故障应用弹 Win7 旧样式 → 该应用用了**老式 API**（`SHBrowseFolder`/`GetSaveFileName`），问题在"应用 + Shell 枚举环境"
  - 记事本也是旧样式 → 系统被全局降级（注册表策略/三方 hook），方向完全不同
- **闪退无崩溃日志 = 崩溃源是"被加载的外部模块"**（Shell 扩展 DLL）而非应用本体——应用本体崩必产生 Application Error 记录。这是最关键的判据

### 第二步：事件日志实锤 faulting module
```bash
powershell.exe -NoProfile -Command '[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-WinEvent -FilterHashtable @{LogName="Application"; Id=1000,1026} -MaxEvents 15 -ErrorAction SilentlyContinue | ForEach-Object { $PSItem.TimeCreated.ToString("yyyy-MM-dd HH:mm") + " | " + $PSItem.ProviderName + " | app=" + $PSItem.Properties[0].Value + " | faulting=" + $PSItem.Properties[3].Value }'
```
- Event 1000 = Application Error：`Properties[0]`=应用名，`Properties[3]`=faulting module
- Event 1026 = .NET Runtime；1001 = WER 报告（Properties 结构不同，勿混用索引）
- 关注**反复出现**的第三方 faulting module（如 BCShellEx64.dll 多次崩 Explorer = 不稳定扩展）

### 第三步：CLSID 反查 DLL 归属（比全盘搜索快得多）
```bash
powershell.exe -NoProfile -Command 'reg query "HKCR\CLSID" /f "BCShellEx" /s /d'
```
→ 输出里 InProcServer32 的 Default 值即 DLL 完整路径 → 反查归属（例：BCShellEx64.dll → Beyond Compare 5，装在 D:\baseSoftware\，不在 Program Files）

### 第四步：确认安装状态/版本 + 验证已知嫌疑
```bash
# 卸载表查应用版本
powershell.exe -NoProfile -Command 'Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*","HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" -ErrorAction SilentlyContinue | Where-Object { $PSItem.DisplayName -match "关键词" } | ForEach-Object { $PSItem.DisplayName + " | " + $PSItem.DisplayVersion }'
# 已知嫌疑 DLL 必须先 Test-Path 确认存在再下结论（托盘没图标 ≠ 组件不存在）
powershell.exe -NoProfile -Command 'Test-Path "C:\Program Files\Microsoft Office\root\vfs\ProgramFilesX86\Microsoft Office\Office16\GROOVEEX.DLL"'
# DLL 版本归属
powershell.exe -NoProfile -Command '(Get-Item "D:\path\to\X.dll").VersionInfo | Select ProductName,ProductVersion | Format-List'
```

### 第五步：验证修复（三选一，均可恢复，写操作先经用户确认）
1. 应用自身设置关掉"资源管理器/Shell 集成"（最干净，推荐）
2. 临时改名嫌疑 DLL 为 `.bak` → 复测 → 改回（影响面：仅右键菜单类功能）
3. 注册表 Blocked 列表屏蔽 CLSID（`HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Shell Extensions\Blocked`）

## WSL→PowerShell 执行陷阱（必须遵守）
- **bash 会展开 `$_`** → `-Command` 外层必须用**单引号** `'...'`，PowerShell 内用 `$PSItem` 替代 `$_`（否则 ForEach-Object 语法错误）
- 中文输出乱码 → 命令开头加 `[Console]::OutputEncoding=[Text.Encoding]::UTF8;`
- **不要往 Windows 侧写 .ps1 文件再 `-File` 执行**（用户明确拒绝过：cp 脚本到 C:\...\Temp + -File）。只读诊断一律单行 `-Command`；复杂逻辑先征求用户同意
- `-File` 传 `\\wsl.localhost\...` UNC 路径解析会失败
- 只读查询（Get-WinEvent / Test-Path / reg query / Get-ItemProperty）可直接执行；改注册表、改名文件等写操作必须用户确认

## 已知 Shell 扩展冲突案例库
- **OneDrive GROOVEEX.DLL**：钉钉下载文件闪退（钉钉官方技术支持确认 168 例，Win11 高频）。先 Test-Path 确认存在再假设；修复=注册表 Blocked 脚本或改下载路径到非 OneDrive 目录
- **Beyond Compare BCShellEx64.dll**：Win11 上枚举时崩，连坐宿主进程（Explorer、钉钉老式对话框）
- 通用怀疑对象：网盘客户端、虚拟光驱（DAEMON Tools/UltraISO）、压缩软件、杀毒的 Shell 扩展
- 详细案例见 references/dingtalk-download-crash.md

## 用户偏好
- 结论先行：嫌疑排名 + 证据表（事实/证据两列），验证方案列为选项让用户挑
- 用户说"先不验证，直接告诉我后续要注意什么"时 → 给"后续注意清单"（验证方案 + 日常规避 + 方法论沉淀）即收尾，不要继续动手
- 排查完成后主动提议把流程存成 skill 复用

## 支持文件
- `references/dingtalk-download-crash.md` — 钉钉下载闪退完整案例（2026-07）：完整证据链、命令输出、环境数据
