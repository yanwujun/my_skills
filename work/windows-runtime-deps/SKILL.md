---
name: windows-runtime-deps
description: 从 WSL 给 Windows 应用补装缺失运行时（.NET Desktop Runtime / VC++ Redist）并验证启动 — 诊断"exe 启动无进程"、aka.ms 最新版下载、静默安装、桌面快捷方式
trigger: Windows 桌面程序启动后无反应/进程不存在，疑似缺运行时；或需要从 WSL 验证 Windows 程序启动、创建快捷方式
---

# Windows Runtime Dependencies

配套 `windows-software-setup`（完整软件安装）。本 skill 专注：**装好了程序却起不来** → 缺运行时依赖的排查与补装。

## 诊断：程序启动无进程

1. 启动并检查:
   `powershell.exe -NoProfile -Command "Start-Process 'D:\path\app.exe'; Start-Sleep 4; Get-Process -Name '<AppName>' -ErrorAction SilentlyContinue"`
   - 查得到 PID = 成功（托盘常驻程序 MainWindowTitle 为空是正常的，别误判失败）
   - 查不到 = 程序启动即退出，继续排查
2. **.NET 应用必带 `*.runtimeconfig.json`**（与 exe 同目录）。读它拿所需框架：
   - `"tfm": "net8.0"` + frameworks 含 `Microsoft.WindowsDesktop.App` → 需要 .NET Desktop Runtime 8.x
   - 没有 runtimeconfig.json 的程序一般不用 .NET（改查 VC++ Redist / MSVCP140.dll 缺失）

## 检查已装版本

`dotnet --list-runtimes` 依赖 PATH，用户机器可能根本没装 dotnet CLI — 直接查目录更稳:
```powershell
Test-Path 'C:\Program Files\dotnet\shared\Microsoft.WindowsDesktop.App\8.0.29'
```

## 下载最新运行时（aka.ms 免查版本号）

微软 aka.ms 短链会 302 到最新 patch：
```
curl -sIL -x http://127.0.0.1:8888 "https://aka.ms/dotnet/8.0/windowsdesktop-runtime-win-x64.exe" -o /dev/null -w "final_url=%{url_effective}"
```
（换 .NET 9/10 同理改 `dotnet/9.0/...`；x86/arm64 改 URL 中平台段）

## 静默安装 + 验证

```powershell
Start-Process 'D:\...\windowsdesktop-runtime-8.0.29-win-x64.exe' -ArgumentList '/install','/quiet','/norestart' -Wait
Test-Path 'C:\Program Files\dotnet\shared\Microsoft.WindowsDesktop.App\8.0.29'   # 输出 INSTALL OK
```
管理员用户下直接 `Start-Process -Wait` 即可（实测未触发 UAC）；失败再改用计划任务提权（见 windows-software-setup）。

## 桌面快捷方式（单行 powershell，不写 .ps1 — 用户偏好）

```powershell
$s = (New-Object -ComObject WScript.Shell).CreateShortcut('C:\Users\Administrator\Desktop\App.lnk'); $s.TargetPath = 'D:\baseSoftware\App\app.exe'; $s.WorkingDirectory = 'D:\baseSoftware\App'; $s.Save()
```

## 下载资源走代理（中国网络）

- GitHub / builds.dotnet.microsoft.com 直连超时（curl exit=28）→ 加 `-x http://127.0.0.1:8888`（sing-box 代理）
- GitHub release 直链获取：抓 `https://github.com/<owner>/<repo>/releases/latest`（web_extract 可读），注意资产文件名可能含 `+` 号（如 `DesktopFrames+.zip`）

## Pitfalls

- **删除 shell 当前所在目录会废掉会话 cwd**（`pwd` 报 getcwd 错误，连 `cd ~` 都失败）— 清理临时目录前先 `cd` 走，或后续命令显式带 workdir 参数
- 绿色版 zip 程序依赖运行时很常见 — 启动无进程先查 runtimeconfig.json，别急着怪程序
- 下载后 `file` 验证真实格式（zip/exe），别只看扩展名

## 参考文件

- `references/desktop-organizer-tools.md` — GitHub 开源 Windows 桌面管理/整理工具清单（star、维护状态、已归档/删库避坑，2026-07 调研）
