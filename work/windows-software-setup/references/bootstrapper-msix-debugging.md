# MSIX 引导程序调试参考

## 背景

Claude Desktop 等现代 Windows 应用使用引导程序（bootstrapper）模式：
- 下载的小 `.exe`（6-7MB）是一个引导程序，不是真正的安装包
- 引导程序启动后从云端下载真正的 MSIX 包（~233MB）
- MSIX 安装到 `C:\Program Files\WindowsApps\` 下，无法通过 `/D=` 参数改变

## 引导程序日志位置

```
%TEMP%\ClaudeSetup.log
# 例如: C:\Users\Administrator\AppData\Local\Temp\ClaudeSetup.log
```

## 日志关键信息解读

| 日志内容 | 含义 |
|---------|------|
| `Native arch: x64` | 安装包架构，确认是否匹配系统 |
| `Standard user — attempting MSIX install with credential prompt` | 普通用户模式，会弹 UAC |
| `Downloading MSIX to C:\Users\...\Temp\Claude-xxxxxxxx.msix` | MSIX 包的临时存放位置 |
| `Download progress: 10% (23363440 / 233453352 bytes)` | 下载进度 + 总大小 |
| `Download complete: 233453352 bytes, SHA256: 0a4c0bb9...` | 下载完成及完整性校验 |
| `Self-elevating: ... --elevated --msix-path ...` | 引导程序自提权继续安装 |
| `Elevated process exited with code 0` | 安装成功 |
| `Proxy interception detected: 0 bytes, Content-Type=""` | 代理/VPN 拦截了 MSIX 下载 |
| `HTTP request failed: ... net/http: TLS handshake timeout` | 网络连接超时（GFW 或代理问题） |

## 常见的 MSIX 下载失败场景

### 场景 1: TLS handshake timeout
- **现象**：引导程序 3 次重试全部 TLS 超时
- **原因**：`api.anthropic.com` 被 GFW 阻断
- **解决**：开启代理/VPN 后再试

### 场景 2: Proxy interception detected (HTTP 403)
- **现象**：引导程序报告被代理拦截
- **原因**：代理/VPN 规则不完整或公司防火墙策略
- **解决**：关闭代理直连，或配置代理规则放行 `api.anthropic.com`

### 场景 3: ERROR_BAD_EXE_FORMAT (0x800700D8)
- **现象**：引导程序启动瞬间就报错
- **原因**：下载了 ARM64 版本但系统是 x64（或反之）
- **解决**：通过 `Get-WmiObject Win32_Processor` 检测 CPU Name 确认正确架构

## MSIX 安装位置检测

MSIX 安装后不在普通路径，需要用 AppxPackage 命令查找：

```powershell
# 查找 Claude 安装路径
$pkg = Get-AppxPackage -Name "Claude" | Sort-Object Version -Descending | Select-Object -First 1
$pkg.InstallLocation
# 返回: C:\Program Files\WindowsApps\Claude_1.6608.2.0_x64__pzs8sxrjxfjjc
```

## MSIX 手动安装

如果引导程序反复失败，可以让用户直接在浏览器打开 MSIX 下载 URL 下载 `.msix` 文件，然后双击运行。

Claude Desktop MSIX URL（x64）：
```
https://api.anthropic.com/api/desktop/win32/x64/msix/latest/redirect
```
