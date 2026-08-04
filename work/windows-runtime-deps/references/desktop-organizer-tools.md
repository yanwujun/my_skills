# GitHub 开源 Windows 桌面管理/整理工具清单（2026-07 调研）

用户场景：替代 360 桌面助手（嫌 360 太拉）。按用途分类，star/状态以 2026-07-31 为准。

## 桌面分区整理（类 Fences / 360 格子收纳）

| 项目 | star | 协议 | 状态 |
|---|---|---|---|
| **DesktopFramesPlus** (limbo666/DesktopFramesPlus) | 568 | MIT | ✅ 最活跃（2026-07 仍在提交）；最新 2.7.7.294 (2026-06-08)；绿色版 zip 免安装 |
| NoFences (Twometer/NoFences) | 668 | MIT | 🚧 维护放缓，老牌可用 |
| DeskFrame (PinchToDebug/DeskFrame) | 498 | — | 2026-03 更新，C#，可用 |
| Palisades (Xstoudi/Palisades) | 74 | — | ❌ 2026-03 已归档，别装 |
| DawnLauncher (nilaoda) | — | — | ❌ 仓库已 404 删库 |

## 免费闭源（GitHub 仅发布，非开源）

- **酷呆桌面 Coodesker** (coodesker/coodesker-desktop) — 808⭐，仓库只有 7 commits（纯发布页），原生中文，功能最成熟、最接近 360 助手

## 快速启动 + 全局搜索

- **GeekDesk** (BookerLiu/GeekDesk) — 2.8k⭐，Apache-2.0，集成 Everything 搜索，品类最火；最后更新 2025-03（功能已定型）
- **DesktopGo** (Aixbox/DesktopGo) — 40⭐，MIT，Tauri+Rust，启动台模式（图标整理+启动+Everything 搜索合一），新项目

## 完整桌面环境重构

- **Seelen UI** (eythaann/Seelen-UI) — **17.4k⭐**，Rust+WebView：Dock 栏、平铺窗口管理、视频壁纸、主题、任务栏重写、Win+S 快速启动器。⚠️ PolyForm Strict 许可（个人免费自用 OK，商用受限）；微软商店可装
- 综合推荐：整体换血 → Seelen UI；只要格子分区 → DesktopFramesPlus；只要搜索启动 → GeekDesk

## 本机安装记录（Windows 11 24H2）

- DesktopFramesPlus → `D:\baseSoftware\DesktopFramesPlus\Desktop Frames.exe`（绿色版），桌面快捷方式 `DesktopFramesPlus.lnk`
- 依赖 **.NET 8 Desktop Runtime**，已静默安装 8.0.29（`C:\Program Files\dotnet\shared\Microsoft.WindowsDesktop.App\8.0.29`）— 本机后续 .NET 8 应用可直接跑
- 下载/安装全程走代理 `-x http://127.0.0.1:8888`（sing-box）
