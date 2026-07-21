# Running Windows Maven from WSL

## Problem

WSL 环境没有安装 Maven 和 JDK，但 Windows 端有。然而 Windows JDK（Eclipse Adoptium）只提供 `java.exe`，没有 `java` 二进制文件。WSL 的 bash 脚本（包括 `mvn`）检测 `$JAVA_HOME/bin/java` 时会失败。

## Solution: Batch file approach

创建 `.bat` 文件，通过 WSL 调用 Windows `cmd.exe` 执行：

### Step 1: Create the batch file

Write a `.bat` file to a Windows-accessible location:

```bat
@echo off
set JAVA_HOME=D:\baseSoftware\Eclipse Adoptium\jdk-11.0.29.7-hotspot
set MAVEN_HOME=D:\baseSoftware\apache-maven\apache-maven-3.6.3
set MAVEN_OPTS=-Dmaven.repo.local=D:\apache-maven\localRepository3.6.3
cd /d D:\项目\svn\ProjectRoot
if not exist C:\Users\Administrator\temp mkdir C:\Users\Administrator\temp
call "%MAVEN_HOME%\bin\mvn.cmd" dependency:tree -DoutputFile=C:\Users\Administrator\temp\deps.txt -DoutputType=text
echo EXIT_CODE=%ERRORLEVEL%
```

### Step 2: Copy to Windows path and run

```bash
# Copy the .bat file
cp /tmp/run_mvn.bat "/mnt/c/Users/Administrator/temp/run_mvn.bat"

# Run via cmd.exe
/mnt/c/Windows/System32/cmd.exe /c "C:\Users\Administrator\temp\run_mvn.bat"

# Read the output
cat /mnt/c/Users/Administrator/temp/deps.txt
```

### Step 3: Parse and copy dependencies

Use `python3 ~/.hermes/skills/devops/maven-offline-dependency/references/parse-deps-tree-and-copy.py` to copy from local repo to target.

## Key Pitfalls

| Pitfall | Explanation |
|---------|-------------|
| **JDK path with spaces** | `Eclipse Adoptium` 路径含空格。在 `.bat` 中用 `set JAVA_HOME=D:\path\with spaces`（不加引号），不要用 `set "JAVA_HOME=..."` |
| **Output dir must exist** | Maven 的 `-DoutputFile` 不会自动创建父目录。在 `.bat` 中先 `mkdir` |
| **Maven is `mvn.cmd`** | Windows Maven 需要 `mvn.cmd`，不是 `mvn` |
| **WSL path mapping** | Windows `C:\Users\...` → WSL `/mnt/c/Users/...` |

## Real-world example

From session where user had:
- Source repo: `D:\apache-maven\localRepository3.6.3`
- Target: `\\wsl.localhost\Ubuntu\tmp\mallrepository`
- Two projects merged into one target:
  1. 590 dependencies from a `malltrade-dependency-list.txt`
  2. 349 dependencies from `xcj-mallbase` project (via `mvn dependency:tree`)

Combined result: 1,182 directories, 4,117 files, 425 MB, 0 missing.
