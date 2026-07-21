# Windows 系统架构检测

## PowerShell 检测命令

```powershell
# 方案1: WMI Win32_Processor (最可靠)
$cpu = Get-WmiObject Win32_Processor
Write-Host ("Name: $($cpu.Name)")
Write-Host ("Architecture: $($cpu.Architecture)")
switch ($cpu.Architecture) {
    0  { Write-Host "Result: x86 (32-bit)" }
    5  { Write-Host "Result: ARM (32-bit)" }
    6  { Write-Host "Result: Intel Itanium" }
    9  { Write-Host "Result: x64 (AMD/Intel)" }
    12 { Write-Host "Result: ARM64" }
}

# 方案2: 环境变量
Write-Host ("PROCESSOR_ARCHITECTURE: $env:PROCESSOR_ARCHITECTURE")

# 方案3: .NET Runtime
Write-Host ("Runtime: $([System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture)")
```

## 从 WSL 中执行

```bash
# 通过 WSL 运行上述 PowerShell
powershell.exe -Command '
$cpu = Get-WmiObject Win32_Processor
$arch = switch ($cpu.Architecture) { 9 {"x64"} 12 {"ARM64"} 5 {"ARM"} default {"$($cpu.Architecture)"} }
Write-Host "Arch: $arch"
Write-Host "CPU: $($cpu.Name)"
'
```

## 常见 CPU 与对应的架构值

| CPU 类型 | Architecture 值 | 说明 |
|---------|----------------|------|
| Intel Core i3/i5/i7/i9 | 9 (x64) | 绝大多数台式机/笔记本 |
| AMD Ryzen 系列 | 9 (x64) | 包括 Ryzen 9 9900X 等 |
| Intel/AMD Xeon | 9 (x64) | 服务器 |
| Snapdragon X Elite | 12 (ARM64) | 新代 ARM Windows PC |
| Surface Pro X (SQ1/SQ2) | 12 (ARM64) | ARM Windows |
| Apple M1/M2/M3 (via Parallels) | 12 (ARM64) | 虚拟化 |
