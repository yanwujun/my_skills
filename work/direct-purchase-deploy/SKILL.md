---
name: direct-purchase-deploy
description: 直采商城（zcsc/zc-mall）部署到测试/生产环境：Maven发布 + 模块部署三步流程。含WSL执行Windows脚本的编码与参数传递解决方案。
---

# 直采商城部署

三步流程部署直采商城应用到指定环境（test3/dev等）。

## 触发条件

- 用户说"发布"、"部署"直采商城/智采商城
- 用户提到执行 `release.bat`、`发布程序到指定环境.bat`
- 从 WSL 调用 Windows 的 `.bat` 部署脚本

## 前置条件

- SVN 和 Nexus (192.168.2.10:8081) 可访问
- JDK8 安装在 `C:\Program Files\Java\jdk8`
- Maven 已配置（本地仓库路径见 settings.xml）

## 部署流程

### 步骤1：发布 lib（Maven deploy）

```
路径: D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\pub\branches\current\lib\release.bat
```

执行 `mvn clean -DskipTests source:jar deploy`，将 `pub-lib` 发布到 Nexus snapshots。

```bash
cmd.exe /c "D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\pub\branches\current\lib && call release.bat"
```

### 步骤2：发布 weblib（依赖步骤1）

```
路径: ...\pub\branches\current\weblib\release.bat
```

**必须在步骤1成功后执行** — weblib 依赖 pub-lib，否则报 `Could not find artifact com.zcsc.pub:pub-lib`。

```bash
cmd.exe /c "D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\pub\branches\current\weblib && call release.bat"
```

### 步骤3：发布业务模块

```
路径: D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter\发布程序到指定环境.bat
```

该脚本是 wrapper，实际逻辑在 `script\发布程序到指定环境.bat`（由 init.bat 从 SVN export）。

该脚本的 `for /f` 从 `%1` 读取参数：**逗号分隔的单参数字符串**或**参数文件路径**。

参数格式：`版本,环境,发布点,发布方式,模块`

| 字段 | 说明 | 示例 |
|------|------|------|
| 版本 | 分支或版本号 | `current`, `trunk`, `3.32.22` |
| 环境 | 目标环境 | `test3`, `dev` |
| 发布点 | 系统发布点 | `xcj`（行采家）, `zcj`（智采） |
| 发布方式 | 空=直接部署, `cr`=仅生成发布包 | `` |
| 模块 | 子系统名 | `goods`, `trade`, `website` |

**批量发布有问题，必须逐个模块执行**（不要一次传多个模块名）。

**WSL→cmd 调用模板**（参数文件方式，避免引号转义问题）：

```bash
# goods
cmd.exe /c 'chcp 65001 >nul && echo current,test3,xcj,,goods > %temp%\pub_params.txt && D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter && call script\发布程序到指定环境.bat %temp%\pub_params.txt'

# trade
cmd.exe /c 'chcp 65001 >nul && echo current,test3,xcj,,trade > %temp%\pub_params.txt && D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter && call script\发布程序到指定环境.bat %temp%\pub_params.txt'

# website
cmd.exe /c 'chcp 65001 >nul && echo current,test3,xcj,,website > %temp%\pub_params.txt && D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter && call script\发布程序到指定环境.bat %temp%\pub_params.txt'
```

## WSL 执行 Windows 脚本的编码方案

从 WSL terminal 调用 `cmd.exe /c` 时存在两个编码问题：

1. **路径乱码**：bash 传 UTF-8 中文路径给 cmd，cmd 默认用 GBK 解析。解决：命令开头加 `chcp 65001 >nul`
2. **参数引号**：bash 双引号内不能再嵌套双引号传给 cmd。解决：bash 单引号包裹整条命令（单引号内所有字符原样传递，包括 `"`）
3. **UTF-8 .bat 文件**：WSL 写入的 .bat 文件是 UTF-8，cmd 默认用 GBK 读取导致中文路径乱码。解决：不用临时 .bat 文件，直接在 cmd 命令中完成所有操作

## 常见问题

### weblib 报 `Could not find artifact pub-lib`
步骤1未完成或失败。等步骤1的 `BUILD SUCCESS` 后再执行步骤2。

### `No plugin found for prefix 'tomcat7'`
Maven 找不到 tomcat7-maven-plugin。检查 Nexus 仓库是否包含该插件，或在 settings.xml 中添加 pluginGroup。这是直接部署模式（非cr）的必经路径。

### `系统找不到文件 xxx.conf`
版本号不正确。检查 `ZCtrlCenter\versions\` 目录下有哪些 `.conf` 文件，使用存在的版本名。
