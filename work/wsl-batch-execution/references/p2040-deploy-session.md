# Session Reference: P2040 直采商城发布

## 环境信息

- **项目**：P2040 直采与框架协议 / 直采商城
- **部署目标**：test3 环境、xcj（行采家）发布点
- **模块**：goods, trade, website（类型均为 web/opertype=3）
- **部署方式**：热发布（tomcat7:redeploy）

## 关键路径

```
ZCtrlCenter: D:\项目\svn\P2040直采与框架协议\C2服务网关\直采商城\ZCtrlCenter
Maven 安装: D:\baseSoftware\apache-maven\apache-maven-3.6.3
Maven 全局配置: D:\baseSoftware\apache-maven\apache-maven-3.6.3\conf\settings.xml
用户级 Maven 配置: D:\apache-maven\localRepository3.6.3\..\conf\settings.xml (或 .m2/settings.xml)
本地仓库: D:\apache-maven\localRepository3.6.3
Nexus: http://192.168.2.10:8081/repository/maven-public/
SVN: https://192.168.2.10:8080/svn/GovProEleTrade/
```

## 配置文件实际内容

### system-info.conf（UTF-8 BOM）
```
system.name=电子直采
system.code=zcsc
system.path=https://192.168.2.10:8080/svn/GovProEleTrade/P20高效电子交易/P2040直采与框架协议/C2服务网关/直采商城
system.dbpath=D:\Repositories\GovProEleTrade
system.dbrootpath=\P20高效电子交易\P2040直采与框架协议\C2服务网关\直采商城
system.jdk=jdk8
system.pubconfigsvn=https://192.168.2.10:8080/svn/GovProEleTrade/安装与配置/部署配置
system.scriptver=v-webapp
system.deployname=
```

### init.bat（GBK 编码）
```
svn export %pubconfigsvn%/脚本/编译与生成/%scriptver% %scriptpath%
```

### 发布脚本参数格式（逗号分隔文件）
```
版本,环境,发布点,发布方式,模块
current,test3,xcj,,trade    → 热发布 trade
current,test3,xcj,,website  → 热发布 website
current,test3,xcj,cr,trade  → cr模式 trade
```

## 错误演进记录

1. 参数格式错误：传空格分隔参数 → `系统找不到文件 test3`
2. 参数引号被 bash 转义：`\"current,...\"` → 脚本把转义引号当文件名
3. SVN URL 中文变 %3F：`svn: E170000: URL ... %3F%3F%3F ... doesn't exist`
4. Maven tomcat7 插件缺失：`No plugin found for prefix 'tomcat7'`
5. cd 到 web 目录失败：`no POM in this directory (ZCtrlCenter)` — 因 temppath 含中文
6. 最终解决：`mklink /D D:\pub_deploy` + URL编码配置 + pluginGroup → 编译打包成功
7. Tomcat 连接失败：`Connection refused: connect` — test3 tomcat 未启动（环境问题，非脚本问题）

## script\发布程序到指定环境.bat 关键行

- 第10行：`for /f "tokens=1-5 delims=," %%a in (%1)` — 从参数文件读取
- 第30-33行：`set rootpath=%cd%` → `set temppath=%rootpath%\temppath`
- 第55行：`if exist %temppath% rmdir /S /Q %temppath%` — 清空临时目录
- 第289行：`svn export !mainpath!/web %temppath%\!subname!\web` — 导出web源码
- 第310行：`cd %temppath%\!subname!\web` — 切换到web目录（中文路径关键点）
- 第397行：`call mvn tomcat7:redeploy -U -Dmaven.test.skip=true` — 热部署
- 第332-411行：遍历 `*-deployto.conf`，从 getmachine.bat 获取目标机器配置
