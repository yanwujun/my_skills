# Tabby Terminal 安装与配置实录（2026-07, v1.0.235）

Tabby (eugeny/tabby) — 开源 SSH/终端工具，Xshell 替代品，MIT 协议，跨平台。

## winget 包 ID 陷阱

```
Eugeny.Tabby     ← 终端工具（要装的）
TabbyML.Tabby    ← TabbyML（AI 编程助手），同名不同物，别装错
```

## 安装

- electron-builder NSIS 格式，per-user 安装，**无需管理员/UAC**
- 静默安装：`setup.exe /S`
- 自定义目录：`setup.exe /S /D=D:\baseSoftware\Tabby`（`/D=` 必须放最后）
- 默认位置：`%LOCALAPPDATA%\Programs\Tabby\`
- 静默卸载：`"<安装目录>\Uninstall Tabby.exe" /S`
- release URL 模式：`https://github.com/Eugeny/tabby/releases/download/v<版本>/tabby-<版本>-setup-x64.exe`（v1.0.235 约 148MB）

## 卸载后清理

`%LOCALAPPDATA%\Programs\Tabby` 残留**空目录**（0 字节），`rmdir` 删除。

## 界面语言设置

配置文件：`%APPDATA%\tabby\config.yaml`（首次 UI 改动前可能不存在，可直接创建）：

```yaml
locale: zh-CN
```

改后需重启 Tabby 生效。UI 路径：Settings（Ctrl+,）→ Appearance → Language → 中文（zh-CN）。

## 实测流程（踩坑记录）

1. `winget install --id Eugeny.Tabby` 直连失败：`0x80072efd`（GitHub 被墙 + 代理未运行）
2. msstore 源无此包（`--source msstore` 返回 No package found）
3. 用户开代理后 `curl -s -x http://127.0.0.1:8888` 探测 github.com → 200
4. `winget --proxy` 被禁（需管理员启用 ProxyCommandLineOptions）→ 放弃
5. `curl -sL -x http://127.0.0.1:8888 -o /mnt/c/Users/Administrator/Downloads/tabby-1.0.235-setup-x64.exe <url>` → 148MB 约 11s
6. `powershell Start-Process setup.exe -ArgumentList '/S' -Wait` → 装到 C 盘
7. 用户要求 D 盘 → 卸载器 `/S` → 重装 `/S /D=D:\baseSoftware\Tabby` → rmdir C 盘空目录
8. 写 config.yaml `locale: zh-CN` 设中文（重启生效）
