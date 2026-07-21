# 直采商城发布工作流

## 概述

从 WSL 环境通过 `cmd.exe /c` 调用 Windows `.bat` 脚本完成 Maven deploy 和模块发布的完整流程。

## 前置条件

- SVN 已认证（脚本内 `svn update` / `svn export` 需要）
- Maven 已安装（`D:\baseSoftware\apache-maven\apache-maven-3.6.3`）
- Maven settings.xml 已配置 Nexus 私服（`192.168.2.10:8081`）

## 步骤1 & 2：发布 lib 和 weblib 到 Maven 仓库

**⚠️ 顺序依赖：weblib 依赖 lib，必须先发布 lib。**

```bash
# 步骤1：发布 lib（约30秒）
cmd.exe /c 'chcp 65001 >nul && D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\pub\branches\current\lib && call release.bat'

# 步骤2：发布 weblib（约20秒，必须先等步骤1完成）
cmd.exe /c 'chcp 65001 >nul && D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\pub\branches\current\weblib && call release.bat'
```

两个脚本内容相同：
```batch
svn update
mvn clean -DskipTests source:jar deploy
```

## 步骤3：发布业务模块（goods / trade / website）

### 脚本路径

- 外层入口：`D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter\发布程序到指定环境.bat`
- 实际脚本：`ZCtrlCenter\script\发布程序到指定环境.bat`（由 `init.bat` 从 SVN export）

### 参数格式

脚本通过 `for /f "tokens=1-5 delims=," %%a in (%1)` 解析参数，**不是空格分隔，是逗号分隔的单个参数字符串**：

```
版本,环境,发布点,发布方式,模块
```

| 字段 | 说明 | 示例值 |
|------|------|--------|
| 版本 | SVN 分支名 | `current`, `trunk`, `long`, 或 `3.32.22` |
| 环境 | 目标环境 | `test3`, `show1`, `dev` |
| 发布点 | 平台标识 | `xcj`(行采家), `zcj`(智采商城), `glxt`(管理系统) |
| 发布方式 | cr=仅生成发布包, 空=直接部署 | `cr` 或留空 |
| 模块 | 子系统名 | `goods`, `trade`, `website` |

### cr 模式 vs 直接部署

- **cr 模式**（推荐）：仅 `mvn clean package` → 生成 war 包到 `d:\发布目录\{env}\{dpypoint}\`，**不需要 tomcat7 插件**
- **直接部署**（非cr）：`mvn tomcat7:redeploy` 直接部署到远程 Tomcat，需要 `tomcat7-maven-plugin`

### WSL→cmd 编码问题与解决方案

从 WSL 终端调用 Windows cmd 执行中文路径脚本时的核心问题：
1. **bash UTF-8 vs cmd GBK**：cmd.exe 默认用系统代码页（GBK/CP936）解析命令行参数，WSL 传的是 UTF-8，导致中文乱码
2. **嵌套引号**：bash 的双引号/单引号处理与 cmd 的 `^"` 转义冲突

**解决方案：参数文件法**

不直接在命令行传参，而是把参数写入临时文件，让脚本的 `for /f` 从文件读取：

```bash
# 先写参数到 %temp% 下的临时文件，再执行脚本
cmd.exe /c 'chcp 65001 >nul && echo current,test3,xcj,cr,trade > %temp%\pub_trade_params.txt && D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter && call script\发布程序到指定环境.bat %temp%\pub_trade_params.txt'
```

**三个关键点：**
1. `chcp 65001` — 切换 cmd 控制台到 UTF-8（仅 cr 模式；热发布见下方 subst 方案）
2. **单引号包围整个命令** — bash 单引号内字符原样传递，避免 bash 转义
3. **参数文件法** — 用 `echo ... > %temp%\\params.txt` 写入参数文件，避免命令行引号嵌套问题

#### ⚠️ chcp 65001 的局限：不能用于直接部署（热发布）

`chcp 65001`（UTF-8）方案在 cr 模式下可行，但直接部署时会失败，原因：
- 脚本内部 `cd %temppath%\\!subname!\\web` 失败（中文变量展开问题）
- SVN 客户端在 chcp 65001 下仍用 GBK 编码 URL，中文路径变成 `?`
- URL 编码中文（如 `%E5%AE%89`）中的 `%` 被 batch 误解释为变量展开

### 直接部署/热发布：subst 虚拟驱动器方案

用 `subst` 创建虚拟驱动器避开所有中文路径：

```bash
# 一次性设置（跨 cmd 会话持久，重启后需重建）
cmd.exe /c 'chcp 936 >nul && subst X: D:\\项目\\svn\\P2040直采与框架协议\\C2服务网关\\直采商城\\ZCtrlCenter'

# 热发布 trade（参数留空=直接部署）
cmd.exe /c 'chcp 936 >nul && echo current,test3,xcj,,trade > %temp%\\pub_trade_params.txt && X: && cd \\ && call script\\发布程序到指定环境.bat %temp%\\pub_trade_params.txt'

# 清理
cmd.exe /c 'subst X: /d'
```

**为什么有效：**
- `subst X:` 后 `%cd%` 返回 `X:\\`（纯英文），路径变量全部避开中文
- `chcp 936`（GBK）让 SVN 客户端正确编码中文 URL
- bat 文件保持 GBK 编码（不能用 UTF-8，否则 `set` 被截断）
- `mklink /D` 不可用：`%cd%` 会解析为实际路径（含中文），subst 无此问题

#### ⚠️ 发布脚本内部 cd 失效的兜底方案

即使使用 subst+chcp 936，发布脚本内部的热部署 mvn 仍可能在错误目录执行。原因：脚本第332行的 `for` 循环处理 `deployto.conf` 时，`getmachine.bat` 等子调用会改变当前工作目录（CWD），导致第397行的 `mvn tomcat7:redeploy` 在 `X:\\` 而非 `X:\\temppath\\{module}\\web` 执行。

**兜底：手动 mvn tomcat7:redeploy**

当发布脚本的 mvn 在错误目录执行时，temppath 中的源码和 war 包可能已就绪（svn export + mvn package 在 cd 失效前已完成），直接手动执行最后一步：

```bash
# trade 热部署 — 手动补刀（3分钟，228MB）
cmd.exe /c 'chcp 936 >nul && cd /d X:\temppath\trade\web && mvn tomcat7:redeploy -U -Dmaven.test.skip=true -Dtomcat.dev.url=http://192.168.2.2:32071/manager/text -Dtomcat.dev.server=test3-server-tomcat -Dtomcat.dev.path=/zcsctrade'

# website 热部署（注意：trade 失败后 website 的源码可能未 svn export，需先处理）
cmd.exe /c 'chcp 936 >nul && cd /d X:\temppath\website\web && mvn tomcat7:redeploy -U -Dmaven.test.skip=true -Dtomcat.dev.url=http://192.168.2.2:32071/manager/text -Dtomcat.dev.server=test3-server-tomcat -Dtomcat.dev.path=/zcscwebsite'
```

**关键：`-D` 参数名必须匹配 pom.xml 中的 `<properties>`**

pom.xml 中定义的是项目特定属性名（如 `tomcat.dev.url`），不是 tomcat7 插件的标准名（`tomcat.url`）。查看 pom.xml 确认：

```xml
<properties>
    <tomcat.dev.server>dev-server-tomcat</tomcat.dev.server>
    <tomcat.dev.url>http://192.168.2.11:8081/manager/text</tomcat.dev.url>
    <tomcat.dev.path>/xygh</tomcat.dev.path>
</properties>
```

所以用 `-Dtomcat.dev.url=...` 而非 `-Dtomcat.url=...`。

**机器配置来源**：发布脚本从 SVN 下载 `${pubconfigsvn}/${envname}/${dpypoint}/machine{N}.conf` 到 `%temppath%\conf\`。test3/xcj 的 tomcat 位于 `machine01.conf` 中的 `tomcat.zcsc.port` 和 `login.ip`。

### 批量发布示例

```bash
# goods（cr模式）
cmd.exe /c 'chcp 65001 >nul && echo current,test3,xcj,cr,goods > %temp%\pub_goods_params.txt && D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter && call script\发布程序到指定环境.bat %temp%\pub_goods_params.txt'

# trade（cr模式）
cmd.exe /c 'chcp 65001 >nul && echo current,test3,xcj,cr,trade > %temp%\pub_trade_params.txt && D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter && call script\发布程序到指定环境.bat %temp%\pub_trade_params.txt'

# website（cr模式）
cmd.exe /c 'chcp 65001 >nul && echo current,test3,xcj,cr,website > %temp%\pub_website_params.txt && D: && cd D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter && call script\发布程序到指定环境.bat %temp%\pub_website_params.txt'
```

## 部署类型映射

脚本中 `systemlist.conf` 定义 `g4` 列 → `opertype` 映射：

| g4 | opertype | 部署方式 |
|----|----------|---------|
| 1 | 1 | Java lib 类型（scp + 启停 server.sh） |
| 2 | 1 | Java lib 类型（同上，带 server.sh stop/start） |
| 3 | 2 | **Web 类型**（tomcat7:redeploy 或 cr 打包） |
| 4 | 3 | 静态资源（7z + scp + unzip） |

trade、goods、website 的 g4=3 → opertype=2 → Web 类型。

## 常见问题

### tomcat7 插件找不到

```
[ERROR] No plugin found for prefix 'tomcat7' in the current project and in the plugin groups [org.apache.maven.plugins, org.codehaus.mojo]
```

**原因**：`tomcat7-maven-plugin` 的 groupId 是 `org.apache.tomcat.maven`，不在 Maven 默认 pluginGroups 中。

**解决方案**：
1. 用 cr 模式（推荐，不依赖 tomcat7 插件）
2. 或在 `D:\\baseSoftware\\apache-maven\\apache-maven-3.6.3\\conf\\settings.xml` 的 `<pluginGroups>` 中添加：
```xml
<pluginGroups>
    <pluginGroup>org.apache.tomcat.maven</pluginGroup>
</pluginGroups>
```
注意：全局 settings.xml 优先；用户级（`~/.m2/settings.xml`）也可用，但两个文件都没有此配置时需要手动添加。

### weblib 依赖 lib 导致失败

错误：`Could not find artifact com.zcsc.pub:pub-lib:jar:1.48.14-SNAPSHOT`

**原因**：weblib 的 pom.xml 依赖 pub-lib，但 lib 还没发布到 Nexus。

**解决**：必须等步骤1（lib deploy）完成后再执行步骤2。不要并行执行。

### 版本配置文件

版本配置位于 `ZCtrlCenter\\versions\\{ver}.conf`。可用的版本：
- `current.conf` — 当前开发分支
- `trunk.conf` — 主干
- `3.32.x.conf` — 历史发布版本

系统配置 `system-info.conf` 中 `system.scriptver=v-webapp` 控制实际使用的发布脚本版本。

### 批量发布中单模块失败后的恢复

发布脚本按 `{ver}.conf` 中定义的系统列表顺序处理（trade → goods → website）。如果前面的模块失败（mvn 报错 → `goto errCode`），后续模块不会被处理，且 `%temppath%` 目录已被 `rmdir` 清空。

恢复步骤：
1. 跳过已成功的模块，为失败模块单独创建参数文件
2. 重新执行发布脚本（会重建 temppath、重新 svn export、重新 mvn package）
3. 如仍失败，用上面"手动 mvn tomcat7:redeploy"兜底

如果只是最后一步 tomcat deploy 失败（war 包已生成），直接补刀即可，无需重跑整个脚本。
