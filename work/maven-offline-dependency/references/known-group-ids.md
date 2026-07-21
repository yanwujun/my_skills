# KNOWN_GROUP_IDS 映射表

此表用于从文件名反推 groupId（当 jar 内部没有 pom.properties 时备用）。
添加到脚本的 KNOWN_GROUP_IDS dict 中即可生效。

## 格式

```python
"artifactId": "groupId",
```

## 快速添加

如果运行后发现 `_unknown_group/` 目录下有新 jar，补充映射：

```python
# 新发现的 artifact
"new-lib": "com.example",
# 然后在脚本的 KNOWN_GROUP_IDS 中插入后重新运行
# 或者用 fixup 脚本搬运: scripts/fix_unknown_group.py
```

## 关于 _unknown/ 的 jar

极少数的 jar 连文件名都无法解析（如 `xpp3_min-1.1.4c.jar`），
需要在 parse_filename 函数中增加特殊正则处理，
或直接手动改名放到 ~/.m2/repository/ 对应路径下。

## 实测覆盖率

首次运行 407 个依赖: 298 个通过 pom.properties 直接定位,
109 个需要文件名解析, 其中 108 个被 KNOWN_GROUP_IDS 覆盖,
1 个彻底无法识别 (xpp3_min-1.1.4c.jar, 24KB 古老 XML 解析器)。

## 各公司自定义库常见 groupId

| 前缀 | groupId |
|------|---------|
| gec-* | com.gec |
| gmsoft-* | com.gmsoft |
| gsp-* | com.gsp |
