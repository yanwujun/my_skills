---
name: wsl-batch-execution
description: Execute Windows .bat deployment scripts from Hermes in WSL — Chinese path encoding, SVN URL handling, Maven plugin config, parameter passing patterns.
trigger: |
  用户要求从 WSL 执行 Windows .bat 脚本，特别是包含中文路径的部署/发布脚本，
  或者调用 cmd.exe /c 执行任何 Windows 批处理文件时遇到编码或路径问题。
---

# WSL Batch Execution

从 Hermes (WSL) 执行 Windows .bat 部署脚本的完整模式。

## 核心问题

WSL→cmd 调用链中存在两层编码断层：
1. **bash→cmd 命令行参数**：bash 用 UTF-8，cmd 默认用 GBK/CP936
2. **cmd→SVN/文件系统**：脚本内部的中文变量展开

## 标准执行模板

### 第一步：创建英文符号链接（关键！）

中文路径是万恶之源。用 `mklink /D` 创建不含中文的目录链接：

```bash
cmd.exe /c 'chcp 65001 >nul && mklink /D D:\pub_deploy D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter'
```

之后所有操作通过 `D:\pub_deploy` 进行，脚本内部的 `%~dp0` 展开为英文路径，所有变量自然不含中文。

### 第二步：chcp 65001 + 单引号包裹

```bash
# ✅ 正确：单引号包裹，bash 不做任何转义
cmd.exe /c 'chcp 65001 >nul && cd /d D:\pub_deploy && call script\发布程序到指定环境.bat %temp%\params.txt'

# ❌ 错误：双引号包裹，内部引号会被 bash 转义
cmd.exe /c "chcp 65001 >nul && call ... \"arg1,arg2\""
```

规则：**永远用单引号包裹 cmd.exe /c 的整个命令字符串**。

### 第三步：参数文件模式

很多中文 .bat 脚本用 `for /f ... in (%1)` 读取参数文件（而非命令行参数）。传参方式：

```bash
# 先写参数到临时文件（纯 ASCII 参数无编码问题）
cmd.exe /c 'chcp 65001 >nul && echo current,test3,xcj,,trade > %temp%\pub_params.txt && ...'

# 然后传给脚本
cmd.exe /c '... && call script\发布程序到指定环境.bat %temp%\pub_params.txt'
```

脚本内的 `for /f "tokens=1-5 delims=," %%a in (%1)` 会读取文件内容并正确解析逗号分隔的参数。

## SVN URL 中文处理

SVN URL 中的中文在 WSL→cmd 下会被编码为 `%3F`（即 `?`），导致 `svn: E170000: URL doesn't exist`。

**解决**：把配置文件中的中文 SVN 路径替换为 URL 编码，同时确保文件是 UTF-8 BOM 编码。

### 处理 system-info.conf

```python
import urllib.parse

filepath = '/mnt/d/.../system-info.conf'
with open(filepath, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 替换中文为 URL 编码（保留斜杠）
for cn_path in ['安装与配置/部署配置', 'P20高效电子交易/P2040直采与框架协议/C2服务网关/直采商城']:
    encoded = urllib.parse.quote(cn_path, safe='/')
    content = content.replace(cn_path, encoded)

# UTF-8 BOM 保存
with open(filepath, 'w', encoding='utf-8-sig') as f:
    f.write(content)
```

### 处理 init.bat 中的中文路径

init.bat 通常是 GBK 编码。先转 UTF-8 BOM，再替换中文，注意 batch 中 `%` 需转义为 `%%`：

```python
import urllib.parse

with open(filepath, 'rb') as f:
    raw = f.read()
text = raw.decode('gbk')  # 先按 GBK 解码

cn_path = '脚本/编译与生成'
encoded = urllib.parse.quote(cn_path, safe='/')
batch_safe = encoded.replace('%', '%%')  # batch 中 %% = 字面 %

text = text.replace(cn_path, batch_safe)

with open(filepath, 'w', encoding='utf-8-sig') as f:
    f.write(text)
```

**重要**：操作后记得备份原始文件，执行完成后恢复。

## Maven 插件缺失处理

如果报 `No plugin found for prefix 'tomcat7'`，需要在 Maven settings.xml 添加 pluginGroup：

```xml
<pluginGroups>
    <pluginGroup>org.apache.tomcat.maven</pluginGroup>
</pluginGroups>
```

Maven 全局配置路径：`D:\baseSoftware\apache-maven\apache-maven-3.6.3\conf\settings.xml`

## 执行顺序

对于多步骤部署（如 lib→weblib→发布），需注意依赖关系：

1. **步骤1和2可并行**（如果无依赖）— 都用 `background=true + notify_on_complete=true`
2. **步骤2依赖步骤1时**：必须等步骤1完成再执行（如 weblib 依赖 lib 的 jar）
3. **步骤3的多个模块**：顺序执行（同环境部署避免冲突）

## 常见错误速查

| 错误 | 原因 | 解决 |
|------|------|------|
| `系统找不到文件 \"current,...\"` | 参数引号被 bash 转义 | 用单引号包裹 cmd 命令 |
| `svn: E170000: URL ... %3F%3F ... doesn't exist` | SVN URL 中文被破坏 | URL 编码配置文件中的中文 |
| `No plugin found for prefix 'tomcat7'` | Maven pluginGroup 缺失 | 添加 org.apache.tomcat.maven |
| `there is no POM in this directory (ZCtrlCenter)` | 脚本 cd 到 web 子目录失败 | 用 mklink /D 英文符号链接 |
| `'D:��Ŀ...' 不是内部或外部命令` | bash→cmd 中文路径乱码 | 加 chcp 65001 前缀 |
| `UNC 路径不受支持` | cmd 从 WSL 路径启动 | 加 `D: && cd ...` 切换盘符 |

## 清理

执行完成后：
1. 恢复被修改的配置文件（system-info.conf, init.bat）
2. 清理临时参数文件（%temp%\pub_*_params.txt）
3. 可选：移除符号链接（`rmdir D:\pub_deploy`）
