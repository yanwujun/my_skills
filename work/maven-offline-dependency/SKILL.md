---
name: maven-offline-dependency
description: >-
  Extract Maven dependencies for offline use — three methods: (A) from local Maven repo via precise dependency:resolve,
  (B) from Spring Boot fat jars, (C) from dependency:tree output. Reconstructs the full Maven local repository structure
  (groupId/artifactId/version) with parent POM recursion, BOM import resolution, SNAPSHOT timestamp handling,
  and compilation failure recovery workflow.
trigger:
  - "I need to get the dependencies from this jar"
  - "如何拿到jar包里面的相关依赖包"
  - "copy/extract dependencies from fat jar to Maven repo"
  - "没有网/离线环境下部署Maven项目"
  - "How do I get the maven dependencies without internet"
  - "把依赖打包成压缩包"
  - "帮我提取这个项目的依赖仓库"
  - "把这个项目依赖复制出来"
  - "导出编译所需仓库"
category: devops
---

# Maven Offline Dependency Extraction

将 Maven 项目或 fat jar 中的依赖提取出来，还原为 **Maven本地仓库结构** (`groupId/artifactId/version/artifactId-version.jar`)，方便拷贝到其他无网/离线环境的机器上直接编译使用。

## 三种方法速览

| 方法 | 输入 | 需要 | 精确度 | 推荐场景 |
|------|------|------|--------|---------|
| **A: 从本地仓库精确提取** | Maven项目 pom.xml | Maven + 本地仓库 | ⭐⭐⭐ 最高 | 有完整本地仓库的开发机，需要100%精确 | 
| **B: 从 fat jar 提取** | Spring Boot fat jar | Python 3 | ⭐⭐ 中 | 只有jar包、无Maven/git环境 |
| **C: 从 dependency:tree 提取** | Maven项目 pom.xml | Maven + 本地仓库 | ⭐⭐ 中 | 仅需快速收集jar依赖（不包含父POM链） |

**核心原则：使用精确方法（Precise），不要使用批量方法（Bulk）。**
- ✅ **Precise** — `mvn dependency:resolve` → 解析精确 GAV + 父POM链 + BOM import → ~1,000 artifacts, ~500MB
- ❌ **Bulk** — 把关联 groupId 下的所有 SNAPSHOT 目录全同步 → ~11,000 dirs, 1GB+，过度浪费

## 方法A（推荐）：从本地仓库精确提取（Precise Method）

从已完整 resolve 的本地 Maven 仓库出发，用 `mvn dependency:resolve` 获取精确的 artifact 列表，逐级补齐父POM链和BOM import。**能准确处理 SNAPSHOT 时间戳版本、传递依赖、父POM链和BOM import。**

### 可选参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `offline` | `true` | `true`=目标离线环境，需生成时间戳SNAPSHOT独立目录；`false`=目标能连Nexus，跳过时间戳目录 |
| `target_dir` | `/tmp/mallrepository/` | 提取后的仓库输出路径 |
| `project_path` | （用户提供） | Maven 项目根目录路径 |
| `src_repo` | `/mnt/d/apache-maven/localRepository3.6.3/` | 源 Maven 本地仓库路径 |

### 关键区别：Precise vs Bulk

**使用精确方法（Precise），不要使用批量方法（Bulk）。**

| 方法 | 手段 | 结果 |
|------|------|------|
| ✅ **Precise** | `mvn dependency:resolve` → 解析精确 GAV + 父POM链 + BOM import | ~1,000 artifacts, ~500MB，够用、精确 |
| ❌ **Bulk** | 把关联 groupId 下的所有 SNAPSHOT 目录全同步到目标 | ~11,000 dirs, 1GB+，过度、浪费 |

**Precise 方法的三层保障（缺一不可）：**
1. **基础层**：`dependency:resolve` 输出的确切 artifact 列表（含时间戳SNAPSHOT）
2. **链式补齐**：对每个 artifact 的 POM，递归解析 parent 链 + BOM import
3. **不扩大范围**：绝不复制不在上述两层中的任何额外 SNAPSHOT 目录

> ⚠️ **血的教训：** 不要因为某个 groupId 下有很多 SNAPSHOT 版本就把它们全部同步过来。Maven 只使用 `dependency:resolve` 解析出的精确版本。额外文件不会帮助编译，只会让仓库臃肿。

### 步骤

#### 1. 确认仓库路径

```bash
grep -r "localRepository" ~/.m2/settings.xml /mnt/d/apache-maven/*/conf/settings.xml 2>/dev/null
```

#### 2. 用 `mvn dependency:resolve` 获取精确版本

```bash
cd /path/to/project
mvn dependency:resolve -DincludeScope=runtime -DoutputAbsoluteArtifactFilename=true -Dmdep.outputFile=/tmp/mvn_resolve_$(date +%s).txt -q
```

**为什么用 `dependency:resolve`？**
- 输出 Maven 解析后的**确切版本**（包括时间戳 SNAPSHOT）
- 格式固定、机器可读：`groupId:artifactId:type:version:scope:absolute-path`

**作用域参数说明：**
- `-DincludeScope=runtime` → compile + runtime（不含 provided、test）
- `-DincludeScope=compile` → compile + provided + system（不含 runtime、test）
- 如果项目用 Lombok（`provided` scope），需用 `-DincludeScope=compile`

**WSL 中运行 Windows 端 Maven：**
```bash
ln -sf "/mnt/d/baseSoftware/Eclipse Adoptium/jdk-11.0.29.7-hotspot" /tmp/jdk11
MAVEN_HOME_WIN=$(wslpath -w /mnt/d/baseSoftware/apache-maven/apache-maven-3.6.3)
PROJECT_DIR_WIN=$(wslpath -w "/mnt/d/项目/xxx")
LAUNCHER_JAR="${MAVEN_HOME_WIN}\\boot\\plexus-classworlds-2.6.0.jar"
/tmp/jdk11/bin/java -classpath "$LAUNCHER_JAR" \
  -Dclassworlds.conf="${MAVEN_HOME_WIN}\\bin\\m2.conf" \
  -Dmaven.home="$MAVEN_HOME_WIN" \
  -Dmaven.multiModuleProjectDirectory="$PROJECT_DIR_WIN" \
  org.codehaus.plexus.classworlds.launcher.Launcher \
  dependency:resolve -DincludeScope=runtime -Dmdep.outputFile=C:\\tmp\\resolve.txt -f pom.xml
```

#### 3. 解析 dependency:resolve 输出 → 批量复制 artifact

```python
import re, os, shutil, hashlib

def parse_resolve_line(line):
    m = re.match(r'\s*(.+?):(.+?):(.+?):(.+?):(.+?):(.+)', line)
    return m and (m.group(1), m.group(2), m.group(4))

def copy_artifact(gid, aid, ver, src_root, dst_root):
    src = os.path.join(src_root, gid.replace('.', '/'), aid, ver)
    dst = os.path.join(dst_root, gid.replace('.', '/'), aid, ver)
    if not os.path.isdir(src):
        return False, f"源仓库不存在: {gid}:{aid}:{ver}"
    if os.path.isdir(dst):
        return True, "已存在"
    shutil.copytree(src, dst)
    return True, "已复制"
```

#### 4. 递归解析父 POM 链

```python
def find_pom(gid, aid, ver, src_root):
    pdir = os.path.join(src_root, gid.replace('.', '/'), aid, ver)
    if not os.path.isdir(pdir):
        return None
    pom = os.path.join(pdir, f"{aid}-{ver}.pom")
    if os.path.isfile(pom):
        return pom
    if '-SNAPSHOT' in ver:
        for f in os.listdir(pdir):
            if f.endswith('.pom') and f.startswith(aid):
                return os.path.join(pdir, f)
    return None

def resolve_parents(gid, aid, ver, src_root, visited=None):
    if visited is None: visited = set()
    needed = set()
    pom_path = find_pom(gid, aid, ver, src_root)
    if not pom_path: return needed
    with open(pom_path, 'r') as fh: content = fh.read()
    props = dict(re.findall(r'<(\w[\w.]*)>(.*?)</\1>', content))
    def resolve_var(val):
        for k, pv in props.items():
            val = val.replace('${' + k + '}', pv)
        return val
    pm = re.search(r'<parent>\s*<groupId>(.+?)</groupId>\s*<artifactId>(.+?)</artifactId>\s*<version>(.+?)</version>', content, re.DOTALL)
    if pm:
        pg, pa, pv = pm.group(1).strip(), pm.group(2).strip(), resolve_var(pm.group(3).strip())
        if '${' not in pv and os.path.isdir(os.path.join(src_root, pg.replace('.','/'), pa, pv)):
            key = (pg, pa, pv)
            if key not in visited:
                visited.add(key); needed.add(key)
                needed |= resolve_parents(pg, pa, pv, src_root, visited)
    return needed
```

#### 5. 递归解析 BOM import（最关键步骤！）

```python
BOM_PATTERNS = [
    r'<dependency>\s*<groupId>(.+?)</groupId>\s*<artifactId>(.+?)</artifactId>\s*<version>(.+?)</version>\s*<type>pom</type>\s*<scope>import</scope>',
    r'<dependency>\s*<groupId>(.+?)</groupId>\s*<artifactId>(.+?)</artifactId>\s*<version>(.+?)</version>\s*<scope>import</scope>\s*<type>pom</type>',
]
# 每个已复制 POM 扫描 BOM，新发现的递归处理，直到没有新 BOM（通常3-5轮）
# 注意：版本号含 ${...} 属性占位符时跳过（编译时由父POM链继承解析）
```

#### 6. SNAPSHOT 时间戳独立目录（offline=true 时需要）

当依赖坐标是时间戳版本（如 `com.djc:djc-flowable-bom:1.9.2-20230518.080737-5`）时：

- 源仓库中，时间戳文件存在 `1.9.2-SNAPSHOT/` 目录内
- **但 Maven 查找 `1.9.2-20230518.080737-5` 时会去 `1.9.2-20230518.080737-5/` 独立目录！**
- **所以两个目录都必须存在！**

```python
import re, os, shutil

def create_timestamp_dirs(dst_root):
    """Scan all SNAPSHOT dirs, read maven-metadata.xml, create missing timestamp dirs"""
    TIMESTAMP = re.compile(r'^([\w.]+)-(\d{8}\.\d{6}-\d+)$')
    created = 0
    for root, dirs, files in os.walk(dst_root):
        if not root.endswith('-SNAPSHOT'): continue
        meta = [f for f in files if f.startswith('maven-metadata') and f.endswith('.xml')]
        if not meta: continue
        aid_base = os.path.basename(root.replace('-SNAPSHOT', ''))
        parent = os.path.dirname(root)
        for mf in meta:
            with open(os.path.join(root, mf)) as fh: content = fh.read()
            ts = re.search(r'<timestamp>(\d{8}\.\d{6})</timestamp>', content)
            bn = re.search(r'<buildNumber>(\d+)</buildNumber>', content)
            if not ts or not bn: continue
            full_ver = f"{os.path.basename(root).replace('-SNAPSHOT', '')}-{ts.group(1)}-{bn.group(1)}"
            ts_dir = os.path.join(parent, full_ver)
            if os.path.isdir(ts_dir): continue
            os.makedirs(ts_dir, exist_ok=True)
            for fn in os.listdir(root):
                if full_ver in fn:
                    shutil.copy2(os.path.join(root, fn), os.path.join(ts_dir, fn))
                elif fn.startswith(aid_base) and '-SNAPSHOT' in fn:
                    ts_fn = fn.replace('-SNAPSHOT', f'-{ts.group(1)}-{bn.group(1)}')
                    shutil.copy2(os.path.join(root, fn), os.path.join(ts_dir, ts_fn))
            created += 1
    return created
```

**真实案例：** 同一 artifact 的多个 SNAPSHOT 时间戳可能不同
```
djc-flowable/1.9.2-SNAPSHOT/           → 1.9.2-20230518.080634-5/
djc-flowable-bom/1.9.2-SNAPSHOT/       → 1.9.2-20230518.080737-5/  ← 注意版本不同！
djc-flowable-core/1.9.2-SNAPSHOT/      → 1.9.2-20230519.061438-6/
```

### 编译失败恢复：步骤123 工作流

当用户反馈编译报错时，使用**严格的三步流程**：

#### 步骤1：提取完整依赖链

从错误信息提取所有 artifact 坐标：
```
Failed to collect dependencies at 
  A → B:jar:x.y.z → C:jar:a.b.c → D:pom:e.f.g-timestamp-N
```

```python
chain = [
    ("com.djc", "djc-basedata-client", "jar", "1.14.0-SNAPSHOT"),
    ("com.gec.stddata", "gec-stddata-rpcapi", "jar", "1.3.0"),
    ("com.gmsoft", "platform-bom", "pom", "1.0.1-20200413.070047-1"),
]
```

#### 步骤2：逐级检查（每级都要 ls 确认）

```bash
# 1. 确认源仓库是否存在
ls -d /mnt/d/apache-maven/localRepository3.6.3/<group-path>/<artifact>/<version>/
# 2. 确认目标仓库是否存在
ls -d /tmp/mallrepository/<group-path>/<artifact>/<version>/
# 3. 文件内容确认（不是只检查目录）
ls <path>/
# 4. 注意区分相似 artifactId！djc-flowable ≠ djc-flowable-bom ≠ djc-flowable-core
# 5. 注意多版本共存！有 1.10.1-SNAPSHOT ≠ 有 1.9.2-SNAPSHOT
```

#### 步骤3：补齐 + 验证

```bash
# 补齐后用离线验证
mvn dependency:resolve -o -Dmaven.repo.local=/tmp/mallrepository
```

#### ⚠️ 验证铁则

| ✅ 正确的验证 | ❌ 错误的做法 |
|--------------|-------------|
| `ls <dir>/ && echo "确认存在"` | 脚本输出 "copied X files" 就结束 |
| 列出目录内容，检查 jar/pom 文件 | 只说 "已补齐" 或 "done" |
| 在目标仓库验证（不是源仓库） | 在源仓库查完就汇报 |

### 🧹 污染文件清理（offline=true 时必须）

离线模式下，Maven 之前连接 Nexus 失败会留下失败的缓存标记，即使 jar 文件已存在也无法编译：

| 文件 | 来源 | 危害 |
|------|------|------|
| `*.lastUpdated` | 下载失败标记 | Maven 跳过该 artifact 不再重试 |
| `resolver-status.properties` | 解析器状态 | 记录"资源不存在"，阻止后续检查 |
| `_remote.repositories` | 仓库元数据 | 记录远程来源，离线触发 check 失败 |

```bash
find /tmp/mallrepository/ -name "*.lastUpdated" -delete
find /tmp/mallrepository/ -name "resolver-status.properties" -delete
find /tmp/mallrepository/ -name "_remote.repositories" -delete
```

执行时机：所有 artifact 复制完成后、使用之前，必须清理。

### 完整流程总结（方法A）

```
1. mvn dependency:resolve -DincludeScope=runtime -Dmdep.outputFile=resolve.txt
2. 解析 resolve.txt，从源仓库复制所有 artifact
3. 递归解析父 POM 链（多轮直到无新 parent）
4. 递归解析 BOM import（多轮直到无新 BOM）
5. SNAPSHOT 时间戳独立目录生成（offline=true 时）
6. 污染文件清理
7. 验证目标仓库文件数，打包带走
```

## 方法B：从 fat jar 提取（离线方式，无需Maven）

### 原理

Spring Boot fat jar 里的依赖都放在 `BOOT-INF/lib/` 下，文件名是扁平的（如 `spring-core-5.3.20.jar`）。每个 jar 内部自带 `META-INF/maven/{groupId}/{artifactId}/pom.properties`，记录着完整的 GAV 坐标。

脚本策略：
1. **优先**从 jar 内部的 `pom.properties` 读取准确的 GAV
2. **备选**从文件名反推 artifactId + version，再用 KNOWN_GROUP_IDS 映射补全 groupId
3. **兜底**完全无法识别的（如 `xpp3_min-1.1.4c.jar`）放入 `_unknown/` 目录

### 前置条件

- Python 3（任何环境都有）
- Spring Boot fat jar 一枚（213MB那种）
- 不需要 Maven、不需要网络、不需要 Java

### 方法

提取打包好的 Spring Boot fat jar（`BOOT-INF/lib/`）中的所有依赖，还原 Maven 本地仓库结构。

```bash
python3 scripts/extract_maven_repo_from_fatjar.py path/to/xxx-provider.jar /输出目录
```

**优点**：无需 Maven、无需网络、无需 Java，适合无网/新机器环境。

**缺点**：fat jar 中的版本可能与 pom.xml 实际声明的不一致（尤其 SNAPSHOT 依赖），因为构建时可能 bundle 了不同的版本。

## 方法C：通过 mvn dependency:tree 提取（快速收集jar依赖）

在**有 Maven + 本地仓库**的开发机上执行，能得到 pom.xml 实际解析出的**完整依赖树**（含传递依赖的每个版本）。推荐使用 `dependency:tree` 而不是 `dependency:list`，因为 tree 输出格式更结构化、更易解析（每行一个坐标）。

```bash
# 1. 在项目根目录执行 dependency:tree
mvn dependency:tree -DoutputFile=dependency-tree.txt -DoutputType=text -DincludeScope=runtime -Dverbose=false

# 如果也需要 test scope 的依赖，去掉 -DincludeScope 参数
mvn dependency:tree -DoutputFile=dependency-tree-all.txt -DoutputType=text
```

### 💡 从 WSL 运行 Windows Maven（当 Windows JDK 只有 .exe 时）

WSL 环境下若没有 Maven/Java，需借助 Windows 的 Maven 和 JDK。但 Windows JDK（如 Eclipse Adoptium）只有 `java.exe` 而没有 `java` 二进制文件，WSL 的 bash 脚本检测 `/bin/java` 时会失败。

**解法：创建 .bat 批处理文件，通过 cmd.exe 运行。**

```bash
# 1. 创建 .bat 文件到 Windows 目录
cat > /mnt/c/Users/Administrator/temp/run_mvn.bat << 'BATEOF'
@echo off
set JAVA_HOME=D:\baseSoftware\Eclipse Adoptium\jdk-11.0.29.7-hotspot
set MAVEN_HOME=D:\baseSoftware\apache-maven\apache-maven-3.6.3
set MAVEN_OPTS=-Dmaven.repo.local=D:\apache-maven\localRepository3.6.3
cd /d D:\项目\svn\xxx-project-root
call "%MAVEN_HOME%\bin\mvn.cmd" dependency:tree -DoutputFile=C:\Users\Administrator\temp\deps.txt -DoutputType=text
echo EXIT_CODE=%ERRORLEVEL%
BATEOF

# 2. 从 WSL 运行
/mnt/c/Windows/System32/cmd.exe /c "C:\Users\Administrator\temp\run_mvn.bat"

# 3. 读结果（从 Windows 路径映射到 WSL 路径）
cat /mnt/c/Users/Administrator/temp/deps.txt
```

> ⚠️ **关键 Pitfall**：Windows JDK 路径如果包含空格（如 `Eclipse Adoptium`），在 `.bat` 文件中的 `set JAVA_HOME=...` 必须用 `set JAVA_HOME=D:\path\with\spaces`（不加引号），而不能用 `set "JAVA_HOME=..."`，否则 cmd.exe 的 `call` 命令会把引号当作路径的一部分。

### 从 dependency:tree 输出解析并复制依赖到目标仓库

`dependency:tree` 的输出格式为：
```
|  +- com.gmsoft:starter-job:jar:2.2.5:compile
|  |  \- org.quartz-scheduler:quartz:jar:2.3.2:compile
```

完整的复制脚本（包含传递依赖的 jar/pom/checksum 全部文件）：

```python
import re, os, shutil

DEPS_FILE = "/mnt/c/Users/Administrator/temp/deps.txt"
SOURCE_REPO = "/mnt/d/apache-maven/localRepository3.6.3"
TARGET_REPO = "/tmp/mallrepository"

pattern = re.compile(r'[+\-|\\ ]+\s+([\w.]+):([\w.-]+):[\w.-]+:([\w.]+(?:-SNAPSHOT)?):')

with open(DEPS_FILE) as f:
    for line in f:
        m = pattern.search(line)
        if m:
            g, a, v = m.group(1), m.group(2), m.group(3)
            src = os.path.join(SOURCE_REPO, g.replace('.', '/'), a, v)
            dst = os.path.join(TARGET_REPO, g.replace('.', '/'), a, v)
            if os.path.isdir(src):
                os.makedirs(dst, exist_ok=True)
                for fname in os.listdir(src):
                    shutil.copy2(os.path.join(src, fname), os.path.join(dst, fname))
            else:
                print(f"  ❌ MISSING: {g}:{a}:{v}")
```

> ⚠️ **deps.txt 在 Windows 路径下时，用 WSL 路径 `/mnt/c/Users/...` 访问**，不要用 Windows 反斜杠路径。

### ⚠️ 关键 Pitfall：必须先创建依赖文件输出目录

Maven 的 `-DoutputFile` 不会自动创建父目录。如果指定 `C:\Users\Administrator\temp\deps.txt`，**确保 `temp` 目录已存在**：

```bash
# 在 .bat 文件中先创建目录
if not exist C:\Users\Administrator\temp mkdir C:\Users\Administrator\temp
```

### 将 dependency:list 中的坐标复制到目标目录

从本地 Maven 仓库逐一复制 dependency:list 声明的所有 jar：

```python
# 解析 dependency:list 的输出格式:
#   com.gec:gec-org-core:jar:1.18.0:compile
import re

with open('dependency-list.txt') as f:
    for line in f:
        m = re.match(r'\s+([\w._-]+(?:\.[\w._-]+)*):([\w._-]+):jar:([\w._-]+[\w._-]*):(compile|runtime|test)', line)
        if m:
            gid, aid, ver = m.group(1), m.group(2), m.group(3)
            # 构造本地仓库路径
            src = f"D:\\apache-maven\\localRepository3.6.3\\{gid.replace('.', '\\')}\\{aid}\\{ver}\\{aid}-{ver}.jar"
            dst = f"/tmp/mallrepository/{gid.replace('.', '/')}/{aid}/{ver}/{aid}-{ver}.jar"
            # ⚠️ 必须 mkdir -p 目标目录，否则 cp 失败
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
```

### ⚠️ 关键 Pitfall：cp 前必须先 mkdir -p

**不要直接 `cp src dst/` 当目录不存在时**。这会导致 `cp: cannot create regular file '...': No such file or directory`。

**总是先创建目标目录**：
```bash
mkdir -p /tmp/mallrepository/com/gec/gec-org-core/1.18.0/
cp source.jar /tmp/mallrepository/com/gec/gec-org-core/1.18.0/gec-org-core-1.18.0.jar
```
或者用 Python 的 `shutil.copy2(src, dst)` 配合 `os.makedirs(os.path.dirname(dst), exist_ok=True)`。

## 方法三：两种方式结合（最完整）

1. 先用 fat jar 提取大头（绝大部分依赖已覆盖）
2. 再用 `mvn dependency:list` 找出 fat jar 中未包含或版本不同的依赖，补全到同一目录
3. 最后运行验证脚本确保 100% 齐全

### ⚠️ 关键补充：父POM递归解析（Parent POM Resolution）

**这是最容易被忽视的关键步骤。** `dependency:tree` 和 `dependency:list` 的输出**只包含 jar 依赖**，但 Maven 编译时还需要所有 `<parent>` 链（父POM → 祖父POM → 曾祖父POM...），这些**永远不会出现在依赖树输出中**。

如果只复制依赖树里的 jar 就以为完事了，在目标机器上编译时会报类似 `Non-resolvable parent POM` 的错误。

**解法**：复制完所有 jar 依赖后，再递归扫描所有已复制的 POM 的 `<parent>` 标签，从源仓库补齐：

```python
# 递归补齐所有缺失的 parent POM（包含 jar 和 pom 等全部文件）
# 用法：先复制完 dependency:tree/list 中的所有依赖，再执行此脚本

import os, re, shutil

TARGET_REPO = "/tmp/mallrepository"       # 目标仓库
SOURCE_REPO = "/mnt/d/apache-maven/localRepository3.6.3"  # 源仓库

def get_copied_artifacts(repo_path):
    """返回目标中已存在的所有 (group, artifact, version)"""
    copied = set()
    for root, dirs, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".pom"):
                rel = os.path.relpath(root, repo_path)
                parts = rel.split(os.sep)
                if len(parts) >= 3:
                    group = ".".join(parts[:-2])
                    artifact = parts[-2]
                    version = parts[-1]
                    copied.add((group, artifact, version))
    return copied

copied_set = get_copied_artifacts(TARGET_REPO)
missing_stack = set(copied_set)  # 已处理过的
to_process = list(copied_set)    # 待检查 parent 的列表

round_num = 0
while to_process:
    round_num += 1
    new_parents = set()
    
    for group, artifact, version in to_process:
        # 找这个 artifact 的 POM 文件（SNAPSHOT 的文件名可能不同）
        dir_path = os.path.join(TARGET_REPO, group.replace('.', '/'), artifact, version)
        if not os.path.isdir(dir_path):
            continue
        pom_files = [f for f in os.listdir(dir_path) if f.endswith(".pom")]
        if not pom_files:
            continue
        
        pom_path = os.path.join(dir_path, pom_files[0])
        try:
            with open(pom_path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except:
            continue
        
        for m in re.finditer(
            r'<parent>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>\s*<version>([^<]+)</version>',
            content, re.DOTALL
        ):
            pg, pa, pv = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            key = (pg, pa, pv)
            if key not in missing_stack:
                missing_stack.add(key)
                new_parents.add(key)
    
    if not new_parents:
        print(f"  第 {round_num} 轮: 无新增 parent POM，解析完成 ✓")
        break
    
    # 从源仓库复制这些 parent POM
    copied_count = 0
    for pg, pa, pv in sorted(new_parents):
        src_dir = os.path.join(SOURCE_REPO, pg.replace('.', '/'), pa, pv)
        dst_dir = os.path.join(TARGET_REPO, pg.replace('.', '/'), pa, pv)
        if os.path.isdir(src_dir):
            os.makedirs(dst_dir, exist_ok=True)
            for f in os.listdir(src_dir):
                sf = os.path.join(src_dir, f)
                df = os.path.join(dst_dir, f)
                if os.path.isfile(sf) and not os.path.exists(df):
                    shutil.copy2(sf, df)
                    copied_count += 1
    
    print(f"  第 {round_num} 轮: 发现 {len(new_parents)} 个 parent POM，已复制 {copied_count} 文件")
    to_process = list(new_parents)

print(f"\n✅ parent POM 递归解析完成，最终 {len(get_copied_artifacts(TARGET_REPO))} 个 artifact")
```

**典型结果**：一个包含 478 个 jar 依赖的项目，递归解析 parent 链后还会新增约 200 个 parent POM（通常要 4-6 轮递归）。

### 检查 BOM import 是否完整

复制完 parent POM 后，还需要检查 `<dependencyManagement>` 中通过 `<type>pom</type><scope>import</scope>` 引用的 BOM，确保它们也存在于目标仓库：

```python
import os, re

# 扫描目标仓库所有 POM 中的 BOM imports
target_repo = "/tmp/mallrepository"
source_repo = "/mnt/d/apache-maven/localRepository3.6.3"

for root, dirs, files in os.walk(target_repo):
    for f in files:
        if not f.endswith(".pom"):
            continue
        pom_path = os.path.join(root, f)
        try:
            content = open(pom_path, encoding="utf-8").read()
        except:
            continue
        
        for m in re.finditer(
            r'<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>\s*<version>([^<]+)</version>\s*<type>pom</type>\s*<scope>import</scope>',
            content, re.DOTALL
        ):
            g, a, v = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            dst = os.path.join(target_repo, g.replace('.', '/'), a, v)
            if not os.path.isdir(dst) and os.path.isdir(os.path.join(source_repo, g.replace('.', '/'), a, v)):
                print(f"⚠️ 缺失 BOM: {g}:{a}:{v}")
```

**注意**：Spring Boot 等框架的 parent POM 中会引用大量 BOM，版本号通常是属性占位符（如 `${spring.version}`），这些在源仓库也不存在——因为它们是在编译时通过 Maven property 继承解析的，**不需要补齐**。只要该 BOM 在源仓库有解析后的具体版本目录，就把它复制过来。

### 完整流程总结（方法C）

```
1. mvn dependency:tree -DoutputFile=deps.txt -DoutputType=text
2. 解析 deps.txt，从源仓库复制所有 jar 依赖到目标仓库
3. 递归解析 parent POM 链（运行上面的 Python 脚本）
4. 检查 BOM import 完整性
5. 验证目标仓库文件数，打包带走
```

## 验证：dependency:list vs 实际文件

提取/复制完成后，**必须验证所有声明的依赖是否真的存在于目标目录**：

```bash
python3 scripts/verify_deps.py /tmp/mallrepository dependency-list.txt
```

输出结构示例：
```
/输出目录/
├── com/
│   ├── gec/gec-org-client/1.24.7-security-SNAPSHOT/gec-org-client-1.24.7-security-SNAPSHOT.jar
│   └── ...
├── org/
│   ├── springframework/boot/spring-boot-autoconfigure/2.3.9.RELEASE/spring-boot-autoconfigure-2.3.9.RELEASE.jar
│   └── ...
├── com/alibaba/fastjson/1.2.75/fastjson-1.2.75.jar
├── mysql/mysql-connector-java/5.1.48/mysql-connector-java-5.1.48.jar
└── _unknown/
    └── xpp3_min-1.1.4c.jar    # 极少数的格式异常jar
```

### 拷贝到目标机器的 Maven 仓库

```bash
# 全部拷贝
cp -r /输出目录/* ~/.m2/repository/

# 或压缩带走
cd /输出目录 && tar czf deps.tar.gz ./*
```

## Pitfalls / 注意事项

1. **cp 前必须先 mkdir -p** — 这是最容易踩的坑。`cp src.jar path/to/gid/aid/ver/` 如果中间目录不存在会失败，必须 `mkdir -p` 先创建完整路径。用 Python 脚本时用 `os.makedirs(dirname, exist_ok=True)` + `shutil.copy2()`。

2. **pom.properties 的 groupId 可能不对** — 少数历史遗留 jar（如 `antlr-2.7.7.jar`）内部 pom.properties 写的 groupId 是 `org.antlr`，但实际 Maven 坐标是 `antlr:antlr:2.7.7`。脚本内置 `FORCED_CORRECTIONS` 表处理已知情况。如果发现新的此类问题，往表中加条目即可。

3. **SNAPSHOT 版本差异** — fat jar 里打包的 SNAPSHOT 版本可能与 pom.xml 声明的不同（例如 pom 写 `gec-stockapply-core:1.42.48-SNAPSHOT` 但 fat jar 里是 `1.42.25-SNAPSHOT`）。两种都保留，用哪个取决于你需要在哪个环境下编译。

4. **花式版本号** — 部分 jar 版本号包含 `-SNAPSHOT`、`.RELEASE`、`-fwzq_zbj-SNAPSHOT`、`-plc-SNAPSHOT` 等后缀，脚本已兼容处理。不要在路径中手动拆分这些版本号（例如不要把 `1.4.4-7` 拆分到子目录里）。

5. **pom.xml 也会一并提取** — fat jar 提取时，如果 jar 内部包含 `pom.xml`，会同步拷贝到同级目录（文件名改为 `{a}-{v}.pom`），方便 Maven 解析依赖树。

6. **xpp3_min 这类边缘情况** — 极少数老 jar 的文件名格式不标准（如 `xpp3_min-1.1.4c.jar`），无法解析版本号，只能放入 `_unknown/`。不影响主项目运行。

7. **验证不能只靠脚本 exit code** — 之前发生过脚本报"已补全"但实际文件没拷贝成功的 bug。**必须用 `ls` 或文件系统确认**目标目录真的有 `.jar` 文件，再用 `verify_deps.py` 做全量交叉验证。

8. **存在多个版本时全部保留** — 不同模块可能依赖同一个包的不同版本（如 `spring-core:5.2.20.RELEASE` 和 `spring-core:5.3.20`），全部拷贝到各自版本目录，不要合并或删减。

## 参见

### 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/extract_maven_repo_from_fatjar.py` | 方法B：从 fat jar 提取依赖（skill目录内） |
| `scripts/verify_deps.py` | 验证目标仓库的依赖完整性 |
| `scripts/check_bom_imports.py` | 检查 BOM import 是否完整 |
| `scripts/resolve_parent_poms.py` | 递归解析父 POM 链 |

也可从 `~/.hermes/skills/devops/maven-offline-dependency/scripts/` 直接访问。

### 参考文件

| 文件 | 内容 |
|------|------|
| `references/known-group-ids.md` | KNOWN_GROUP_IDS 映射表（约200条），发现缺失时直接补充该文件即可生效 |
| `references/dependency-chain-cases.md` | **实际编译失败案例**：依赖链追溯、SNAPSHOT时间戳处理、artifactId混淆陷阱 |
| `references/parent-pom-recursion-case-study.md` | 478 artifact → 676 artifact 的递归解析实战记录 |
| `references/wsl-maven-execution.md` | WSL中运行Windows Maven的.bat文件方案 |

### 方法选择速查

| 场景 | 推荐方法 | 原因 |
|------|---------|------|
| 有完整本地Maven仓库 | **方法A** | 最精确，含父POM链+BOM import |
| 只有胖jar包 | **方法B** | 无需Maven/Java/网络 |
| 有Maven但需要快速上手 | **方法C** | 简单，但需手动补齐父POM链 |
| 编译失败缺依赖 | 方法A → 步骤123工作流 | 从错误信息定位并补齐 |
