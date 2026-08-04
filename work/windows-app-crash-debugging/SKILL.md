---
name: windows-app-crash-debugging
description: 排查 Windows 桌面应用闪退/崩溃（静默崩溃、弹窗即崩、CEF 应用崩溃、下载文件时崩）。从 WSL 调 Windows PowerShell 查事件日志、CLSID 反查 DLL 归属、解析应用崩溃转储，区分系统组件缺陷 vs 三方软件 hook。当用户报"XX软件闪退/一打开就没了/弹保存框时崩/下载文件时崩"时使用。
---

# Windows 应用闪退排查

## 触发条件
- 用户报 Windows 桌面软件闪退/崩溃/无响应退出（钉钉、微信、WPS、办公软件等）
- 常见场景：弹对话框时崩、下载文件时崩、打开特定功能时崩、启动即崩

## 核心原则
1. **静默崩溃（系统事件日志无该应用记录）≠ 应用本体问题**：崩溃源通常在"被加载的外部模块"（Shell 扩展、hook DLL、系统组件在进程内崩）或子进程（CEF 渲染进程），应用崩溃处理器静默接管并自动重启子进程 → WER 无记录
2. **记事本对照法**：让用户开记事本 Ctrl+S 看另存为对话框样式——系统对话框正常（Win11 新样式）⇒ 应用用老式 API（GetSaveFileName/SHBrowseFolder 的 Win7 风格）或自绘对话框；系统也被降级 ⇒ 全局策略/hook 问题
3. **先明确崩溃环节再深挖**：点按钮即崩 / 弹窗后崩 / 使用中崩、所有文件还是特定文件，决定排查方向
4. **应用自带日志优先于系统日志**：CEF 应用看 cef_debug.log（RENDER_FRAME_DISCONNECT = 渲染进程崩）；崩溃转储 dumps/*.RPT 直接给 Exception code + faulting module，是静默崩溃的实锤证据

## 六步排查流程

### ① 明确崩溃环节
问清：什么操作触发？点下载就崩还是弹窗后崩？所有文件还是特定文件？闪退后有报错弹窗吗？

### ② 记事本对照测对话框（30 秒）
记事本 → Ctrl+S 看对话框样式，判断系统文件对话框是否正常（见核心原则 2）。

### ③ 事件日志查 faulting module（实锤第一步）
```bash
powershell.exe -NoProfile -Command '[Console]::OutputEncoding=[Text.Encoding]::UTF8; $e = Get-WinEvent -FilterHashtable @{LogName="Application"; Id=1000,1026} -MaxEvents 15 -ErrorAction SilentlyContinue; if (-not $e) { "NO_CRASH_EVENTS" } else { $e | ForEach-Object { $PSItem.TimeCreated.ToString("yyyy-MM-dd HH:mm") + " | " + $PSItem.ProviderName + " | app=" + $PSItem.Properties[0].Value + " | faulting=" + $PSItem.Properties[3].Value } }'
```
- 有目标应用记录 ⇒ faulting module 是元凶（注意区分：Explorer 的崩溃记录可能暴露反复崩的第三方扩展）
- **无记录 ⇒ 静默崩溃**，跳到 ⑤ 查应用日志和转储

### ④ CLSID 反查 DLL 归属（比全盘搜索快得多）
```bash
powershell.exe -NoProfile -Command 'reg query "HKCR\CLSID" /f "BCShellEx64" /s /d'
```
`HKEY_CLASSES_ROOT\CLSID\{...}\InProcServer32` 的 (Default) = DLL 完整路径 ⇒ 反查是什么软件（DLL 名常带厂商缩写，BC=Beyond Compare 等）。
全量枚举第三方 Shell 扩展（排除系统路径）：
```bash
powershell.exe -NoProfile -Command '[Console]::OutputEncoding=[Text.Encoding]::UTF8; $out = Get-ChildItem "HKCR:\CLSID" -ErrorAction SilentlyContinue | ForEach-Object { $ip = Join-Path $_.PSPath "InProcServer32"; if (Test-Path $ip) { $dll = (Get-ItemProperty $ip)."(default)"; if ($dll -and $dll -notmatch "C:\\Windows|WindowsApps") { $dll } } }; if ($out) { $out | Sort-Object -Unique } else { "NO_THIRD_PARTY_SHELLEX" }'
```
（枚举 HKCR\CLSID 全量约 1-3 分钟，可接受）

### ⑤ 应用自带日志 + 崩溃转储（静默崩溃必做）
- 日志目录：`%APPDATA%\<App>\log\`（钉钉：cef_debug.log.日期、gaea.log.日期）
  - `RENDER_FRAME_DISCONNECT` + `connection retry scheduled` ⇒ CEF 渲染进程崩溃（静默重启，系统无日志）
- 崩溃转储：`%LOCALAPPDATA%\<App>\dumps\`（钉钉：`dingtalk_<版本>_<hash>/` 含 Process.dmp + dingtalk.RPT）
  - RPT 是 UTF-16 二进制：`iconv -f UTF-16LE -t UTF-8 xxx.RPT` 提取
  - 关键字段：`Exception code: C0000005 ACCESS_VIOLATION`、`Fault address` 后的模块、`Call stack` 顶部模块
  - 只列该目录（`ls -lt`），**禁止全盘 find *.dmp**（极慢，用户会打断）

### ⑥ 安全软件 hook 排查（COMDLG32 在进程内崩的头号原因）
```bash
powershell.exe -NoProfile -Command '[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | ForEach-Object { $PSItem.displayName }'
powershell.exe -NoProfile -Command '[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-Process -ErrorAction SilentlyContinue | Where-Object { $PSItem.Name -match "qax|360|tianqing|edr" } | ForEach-Object { $PSItem.Name + " | " + $PSItem.Path }'
```
- **国产安全软件 hook 文件对话框**（奇安信天擎、360 文件浏览器/快速预览 360FileBrowser/360QuickPreview/360FileService）→ 弹保存框时在 COMDLG32/USER32 路径上 ACCESS_VIOLATION，栈里可能看不到 hook 软件自己的模块
- **faulting module 不止 COMDLG32**：文件夹选择类对话框（SHBrowseFolder）崩在 `shcore.dll`（如 Hermes 安装包选"其他路径"即崩 = 与钉钉保存框同一根因）
- **360 桌面助手（360DesktopLite/360DesktopService64）也会 hook 文件对话框**，不只是 360 文件浏览器——退出文件浏览器后仍崩时查它
- **360 内核驱动不随进程退出卸载**：进程全退后仍崩 ⇒ 残留 hook，必须重启且不启动 360 才能干净验证
- 验证顺序（每步 1 分钟）：① 退 360 文件组件 → ② 退奇安信天擎 → ③ 重启后不启动 360/天擎直接测（最干净）→ ④ 还崩则 `sfc /scannow` + `DISM /Online /Cleanup-Image /RestoreHealth`
- 应急兜底：在应用设置里指定固定下载/保存目录，跳过弹对话框，绕过 hook 冲突点
- 也查 AppInit_DLLs：`Get-ItemProperty "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Windows" | Select AppInit_DLLs`

## WSL → Windows 命令模板（踩坑总结）
- **必须用单引号包裹 -Command**，内部 PowerShell 字符串用双引号；`$_` 在 bash 双引号里会被展开吞掉 → 用 `$PSItem` 或外层单引号保护
- 每条命令加 `[Console]::OutputEncoding=[Text.Encoding]::UTF8;` 防中文乱码
- **不要把 .ps1 复制到 /mnt/c/ 再执行**：\\wsl.localhost 路径 PowerShell -File 不认（要 C:\ 盘符路径），且用户可能拒绝写 Windows 侧——优先单行 -Command
- 二进制文本（RPT 等）用 `iconv -f UTF-16LE -t UTF-8` 或 `strings -el`
- 只读查询（事件日志、注册表、进程）用户接受；**写操作（注册表屏蔽、改名 DLL、退杀软）必须先经用户确认**

## 已知元凶清单（按概率）
| 元凶 | 特征 | 处理 |
|---|---|---|
| 奇安信天擎 / 360 文件浏览器 | COMDLG32.dll ACCESS_VIOLATION、弹保存框即崩 | 退出软件复测，钉钉等加白名单 |
| OneDrive GROOVEEX.DLL（Office 组件） | Win11 下载文件后点打开闪退（官方 168 例） | 注册表 Shell Extensions Blocked 屏蔽或改下载路径 |
| Beyond Compare 等三方 Shell 扩展 | 扩展 DLL 反复崩 Explorer（事件日志可见） | 关 Shell 集成 / ShellExView 禁用 |
| 断连网络驱动器 / 慢 NAS | 老式对话框枚举"此电脑"卡死/崩 | `net use` 断开异常连接 |
| 文件路径超 260 字符 | 特定长文件名才崩 | 下载到短路径 |
| CEF 渲染进程 GPU 问题 | RENDER_FRAME_DISCONNECT、随机崩 | 关硬件加速 |

## Pitfalls
- 应用设置里"关闭右键菜单集成"可能不注销 CLSID 注册 → 用 `Test-Path "HKCR:\CLSID\{...}\InProcServer32"` 确认是否真注销，别被"关了还崩"误导
- 事件日志 -MaxEvents 数量要够（崩溃间隔长时 15 条不够）
- 无崩溃日志时别急着下结论——静默崩溃场景优先查应用自带日志和 dumps
- 弹窗闪退 ≠ 系统对话框问题：钉钉等 CEF 应用的"Win7 风格对话框"是自己渲染的网页对话框，内部再调系统 COMDLG32——两级都要看

## 案例参考
- 钉钉下载文件闪退完整排查案例（COMDLG32 + 奇安信/360 hook 推断、命令输出、崩溃栈）：references/dingtalk-comdlg32-case.md
