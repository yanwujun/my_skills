# 案例：钉钉下载会话文件闪退（2026-07-31）

## 现象
Windows 11 (24H2, build 26100) 下钉钉 8.3.45 下载会话文件 → 点"下载" → 弹出 Win7 风格保存对话框 → 应用闪退。无错误弹窗。

## 排查链（按序排除）
1. 记事本 Ctrl+S → Win11 新样式对话框 → 系统文件对话框正常，钉钉用了老式 API 或自绘
2. GROOVEEX.DLL（OneDrive 168 例官方案例）→ `Test-Path` = False → 排除（未装 Office 组件）
3. 事件日志 Application Error 1000：无 DingTalk 记录，但发现 `BCShellEx64.dll` 6月三次崩 Explorer
4. `reg query "HKCR\CLSID" /f "BCShellEx64" /s /d` → `D:\baseSoftware\Beyond Compare 5\BCShellEx64.dll`（Beyond Compare 5.2.2）
5. 用户关闭 BC "Include Beyond Compare in Explorer context menu" → `Test-Path InProcServer32` = 已注销 → 仍闪退 → 排除
6. 全量枚举 HKCR\CLSID 三方 InProcServer32 → 无（全系统组件）→ 排除三方 Shell 扩展
7. `net use` → 有 Z: 网络驱动器 `\\10.30.2.2\gm20220407`（OK 状态，28TB NAS）——嫌疑但非实锤
8. 钉钉日志 `%APPDATA%\DingTalk\log\cef_debug.log.2026-07-31`：
   `RENDER_FRAME_DISCONNECT, MAIN_FRAME, error_result=9` + `connection retry scheduled (1/5)`
   → CEF 渲染进程崩溃，崩溃处理器静默接管（解释系统无日志）
9. 崩溃转储 `%LOCALAPPDATA%\DingTalk\dumps\`：18:23-19:03 共 9 个转储，时间与测试吻合
   `dingtalk.RPT`（UTF-16LE，iconv 提取）实锤：
   ```
   Exception code: C0000005 ACCESS_VIOLATION
   Fault address: A59BD8C8  C:\Windows\System32\COMDLG32.dll
   Call stack: libcef.dll → dt_web_view.dll → MainFrame.dll → COMDLG32.dll(崩) → USER32 → ntdll
   ```
   → 钉钉 CEF 网页对话框调系统老式 API（COMDLG32 GetSaveFileName，故 Win7 风格），**COMDLG32.dll 在进程内访问违规**
10. 环境扫描：奇安信天擎（QAXClientSvc 运行中）+ 360 全家桶：
    `360FileService`（C:\Windows\SysWOW64）、`360QuickPreview`、`360FileBrowser`（%APPDATA%）、`360DesktopLite`
    → 360 文件浏览器/快速预览专门 hook 替换系统文件对话框 → 头号嫌疑（验证中：退出 360 文件组件 → 复测；再退天擎；最后 sfc /scannow）

## 关键结论
- 钉钉"Win7 风格对话框"= CEF 渲染的网页对话框内调系统 COMDLG32 老 API，两级结构
- 崩溃在系统 COMDLG32.dll（C0000005），非钉钉本体、非三方 Shell 扩展
- 国产安全软件（天擎/360 文件浏览器）hook COMDLG32/USER32 是此类崩溃的最常见成因
- 钉钉安装位置：D:\baseSoftware\DingDing\main\current\（用户软件统一装 D:\baseSoftware）

## 复用要点
- 静默崩溃（无 WER）优先查 `%LOCALAPPDATA%\<App>\dumps\` 转储 + `%APPDATA%\<App>\log\cef_debug.log`
- RPT 转储文件是 UTF-16LE：`iconv -f UTF-16LE -t UTF-8 dingtalk.RPT`
- 验证顺序建议：先退用户自装软件（360 文件浏览器）→ 再退公司安全软件（天擎）→ 最后 sfc /scannow + DISM
