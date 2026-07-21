# 通过计划任务从 WSL 安装 Windows 软件

## 完整模板

```powershell
$installerPath = "D:\baseSoftware\Setup.exe"
$targetDir    = "D:\baseSoftware\AppName"
$taskName     = "InstallAppTemp"

# 确保目标目录存在
if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force }

# 创建计划任务
$action    = New-ScheduledTaskAction -Execute $installerPath -Argument "/S /D=$targetDir"
$trigger   = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
$settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "Administrator" -RunLevel Highest -LogonType Interactive

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force

Write-Host "Task '$taskName' created. Waiting 90 seconds for installation..."
Start-Sleep -Seconds 90

# 检查结果
$info = Get-ScheduledTaskInfo -TaskName $taskName
Write-Host ("LastRunTime: $($info.LastRunTime)")
Write-Host ("LastTaskResult: 0x{0:X8}" -f $info.LastTaskResult)
if ($info.LastTaskResult -eq 0) {
    Write-Host "SUCCESS: Installation completed!" -ForegroundColor Green
} else {
    Write-Host "FAILED: Error code 0x{0:X8}" -f $info.LastTaskResult -ForegroundColor Red
}

# 清理
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
```

## 常见错误码

| 值 | 含义 | 解决方法 |
|---|------|---------|
| 0x0 | 成功 | - |
| 0x800700D8 | ERROR_BAD_EXE_FORMAT | 安装包架构不匹配系统架构 |
| 0x80070118 | CRYPT_E_NO_MATCH | 权限不足，或任务用户无效 |
| 0x800704EC | 未正确关闭 | 确保任务运行前没有同名进程 |
| 0x8007139F | 组策略阻止 | 检查 Windows 安装策略 |
| 267009 (0x41281) | WAIT_TIMEOUT | 安装器等待用户交互（如 UAC 弹窗）超时 |
| 1 (0x1) | 安装器内部失败 | 检查引导程序日志 `%TEMP%\ClaudeSetup.log` |

## 从 WSL 执行

```bash
# 在 WSL 中调用 PowerShell 执行上述脚本
powershell.exe -File /mnt/d/baseSoftware/install_template.ps1
```

## 注意事项
- `-RunLevel Highest` 需要 UAC 提权，可能会弹出窗口要求用户点「是」
- `-LogonType Interactive` 确保任务在用户会话中运行（能看到 UAC 弹窗）
- 如果用户不在登录状态，任务可能无法启动
