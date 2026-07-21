# 部署错误速查

## weblib 依赖 lib（步骤2在步骤1前执行）

```
[ERROR] Failed to execute goal on project pub-weblib: Could not resolve dependencies for project com.zcsc.pub:pub-weblib:jar:1.48.14-SNAPSHOT: Could not find artifact com.zcsc.pub:pub-lib:jar:1.48.14-SNAPSHOT in nexus
```

→ 等步骤1 `BUILD SUCCESS` 后重试。

## 参数格式错误（空格分隔而非逗号分隔）

```
系统找不到文件 test3。
"选择错误"
exit /B 11
```

→ 参数必须是逗号分隔的单一字符串或参数文件路径：`current,test3,xcj,,goods`

## 引号转义错误（WSL→cmd）

```
The system cannot find the file \"current,test3,xcj,,goods\".
```

→ 用参数文件方案：`echo current,test3,xcj,,goods > %temp%\pub_params.txt` 然后传文件路径给脚本。

## 中文路径乱码（cmd编码问题）

```
'D:��ĿsvnP2040ֱ������Э��C2��������ֱ���̳�ZCtrlCenter_tmp_pub_goods.bat' �����ڲ����ⲿ����
```

→ cmd 命令开头加 `chcp 65001 >nul`，且不使用 WSL 创建的 UTF-8 .bat 文件。

## tomcat7 插件缺失

```
[ERROR] No plugin found for prefix 'tomcat7' in the current project and in the plugin groups [org.apache.maven.plugins, org.codehaus.mojo]
```

→ 直接部署模式依赖 tomcat7-maven-plugin。检查 settings.xml pluginGroup 或改用 cr 模式。
