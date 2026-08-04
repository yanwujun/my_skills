# 案例：钉钉下载会话文件闪退（2026-07-31）

## 现象
Win11 下钉钉（8.3.45-Release.260720005）下载会话文件 → 点下载按钮 → 弹出 Win7 旧式"选择保存位置"对话框 → 闪退。下载任何文件都崩。

## 证据链（排查顺序即结论收敛顺序）

| 步骤 | 操作 | 结果 | 结论 |
|---|---|---|---|
| 1 | 记事本 Ctrl+S 对照 | Win11 新样式对话框 | 系统对话框正常 → **钉钉用老式 API**（SHBrowseFolder 树形目录框） |
| 2 | Test-Path GROOVEEX.DLL | False | **OneDrive/Groove 假设排除**（托盘没图标+文件不存在；注意：托盘没图标≠组件不存在，必须实测文件） |
| 3 | Get-WinEvent Id=1000,1026 近 60 条 | 无任何 DingTalk 记录 | 钉钉**静默崩溃** → 崩溃源在被加载的外部模块而非钉钉本体 |
| 4 | 事件日志扫描 | `BCShellEx64.dll` 三次崩 Explorer（6/24、6/26、6/29） | 系统里唯一反复崩溃的三方 Shell 扩展 |
| 5 | `reg query "HKCR\CLSID" /f "BCShellEx" /s /d` | InProcServer32 → `D:\baseSoftware\Beyond Compare 5\BCShellEx64.dll` | 归属 = **Beyond Compare 5.2.2**（CLSID {812BC6B5-83CF-4AD9-97C1-6C60C8D025C5}） |

## 根因推断
钉钉老式目录对话框枚举"此电脑/磁盘"时，系统加载 Beyond Compare 的 Shell 扩展（注册于 `HKCR\CLSID\{812BC6B5-...}`），该扩展在 Win11 上枚举时崩溃 → 宿主进程（钉钉）闪退。钉钉自身无崩溃日志佐证了这一点（崩的是加载进来的扩展）。

## 验证/修复方案（三选一，均可恢复）
1. Beyond Compare → 工具(Tools) → 选项(Options) → 集成(Integration) → 取消"资源管理器集成/右键菜单"（最干净）
2. 临时改名 `D:\baseSoftware\Beyond Compare 5\BCShellEx64.dll` → `.bak` → 复测 → 改回
3. 注册表 `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Shell Extensions\Blocked` 加 CLSID {812BC6B5-83CF-4AD9-97C1-6C60C8D025C5}

## 环境数据
- 钉钉 8.3.45-Release.260720005（2026-07-20 版，很新，无需升级）
- Beyond Compare 5.2.2.32186（D:\baseSoftware\，非标准安装目录 → 全盘搜不到，CLSID 反查才能定位）
- 无关噪音：同日 Windows-hermes-setup (1).exe 崩 4 次（faulting=shcore.dll），与本案无关

## 附带发现
事件日志里还出现过 `PinToStartMenu64.dll_unloaded` 崩 Explorer —— 又一个三方 Shell 扩展，属同类风险源。
