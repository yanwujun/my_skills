# WSL + SVN + Java Editing Reference

## File Access Pitfalls

### SVN Checkout = Read-Only
SVN-checked-out files on NTFS mounts (`/mnt/d/`) have `-r-xr-xr-x` permissions. The `patch` tool and `write_file` fail with `Permission denied` on temp files.

**Fix before editing:**
```bash
chmod -R u+w xcj-ezc-provider/src/main/java/...
```

### Paths with Chinese Characters
NTFS mounts use `/mnt/d/...` paths that contain Chinese characters. The `patch` tool works with these paths as long as file permissions are correct.

## Spring Service Editing Pattern

### Interface + Impl Dual Update
Always update the **interface first**, then the implementation. The pattern is:

1. Add method signature to `*Service.java` (interface)
2. Add `@Override` implementation to `*ServiceImpl.java`
3. The impl class extends `BaseServiceImpl<Repo, Entity>` — use `list(queryWrapper)` for batch query methods

### Import Checklist After Patching
When adding batch/collection methods, verify these imports:

| Code Added | Import Needed |
|-----------|---------------|
| `new ArrayList<>()` | `java.util.ArrayList` |
| `Set<Long>` variable | `java.util.Set` |
| `Map<Long, ...>` variable | `java.util.Map` (usually already present) |
| `Collectors.toSet()` | `java.util.stream.Collectors` (usually via wildcard) |
| `Collectors.groupingBy` | `java.util.stream.Collectors` |
| `LambdaQueryWrapper` | `com.baomidou.mybatisplus...` |

Wildcard imports like `com.xcj.ezc.enums.*` cover enum references automatically.

### `patch` Tool Quote Pitfall
When the `old_string` or `new_string` in a `patch` call contains Java string literals with embedded `\"` characters, the serialization can produce escape-drift errors like:

```
Escape-drift detected: old_string and new_string contain the literal sequence '\"' 
```

**Fix:** Re-read the exact lines with `read_file` and copy the raw content — do NOT manually escape quotes. The file on disk uses raw `"` inside the Java source, and `patch` needs the exact byte content matched against it.

### Error Message Placeholder Format
`ExceptionChecker.throwException` uses `{}` (single SLF4J-style placeholder). The Java source shows `"{{}}"` which means:
- `{` = literal left brace
- `{}` = placeholder (replaced by the argument)
- `}` = literal right brace

Result: `您提交的对编号为：{<protocolNo>}的协议...`

## WSL Maven Compilation (Windows JDK)

When the JDK is on the Windows side (e.g. `D:\baseSoftware\Eclipse Adoptium\jdk-11...`) and Maven is also a Windows install, the stock `mvn` shell script fails because it calls `cygpath` (not available in WSL) and passes Unix-style paths (`/mnt/d/...`) to Windows Java which can't read them.

**Fix — WSL-adapted `mvn` wrapper:**

Creates a `/tmp/mvn-wsl` script that uses `wslpath -w` to convert paths before calling Windows `java.exe` directly:

```bash
cat > /tmp/mvn-wsl << 'MVNEOF'
#!/bin/bash
JAVA_HOME="/mnt/d/baseSoftware/Eclipse Adoptium/jdk-11.0.29.7-hotspot"
MAVEN_HOME="/mnt/d/baseSoftware/apache-maven/apache-maven-3.6.3"
PROJECT_DIR="$(pwd)"

JAVA_HOME_WIN=$(wslpath -w "$JAVA_HOME")
MAVEN_HOME_WIN=$(wslpath -w "$MAVEN_HOME")
CLASSWORLDS_JAR=$(ls "$MAVEN_HOME"/boot/plexus-classworlds-*.jar | head -1)
CLASSWORLDS_JAR_WIN=$(wslpath -w "$CLASSWORLDS_JAR")
M2_CONF_WIN=$(wslpath -w "$MAVEN_HOME/bin/m2.conf")
JANSI_PATH_WIN=$(wslpath -w "$MAVEN_HOME/lib/jansi-native")
PROJECT_DIR_WIN=$(wslpath -w "$PROJECT_DIR")

exec "$JAVA_HOME/bin/java.exe" \
  -classpath "$CLASSWORLDS_JAR_WIN" \
  "-Dclassworlds.conf=$M2_CONF_WIN" \
  "-Dmaven.home=$MAVEN_HOME_WIN" \
  "-Dlibrary.jansi.path=$JANSI_PATH_WIN" \
  "-Dmaven.multiModuleProjectDirectory=$PROJECT_DIR_WIN" \
  org.codehaus.plexus.classworlds.launcher.Launcher \
  "$@"
MVNEOF
chmod +x /tmp/mvn-wsl
/tmp/mvn-wsl compile -pl xcj-ezc-provider -am -q
```

**Prerequisite:** Symlink `java -> java.exe` so the wrapper's `$JAVA_HOME/bin/java` resolves:
```bash
JAVA_HOME="/mnt/d/baseSoftware/Eclipse Adoptium/jdk-11.0.29.7-hotspot"
ln -sf "$JAVA_HOME/bin/java.exe" "$JAVA_HOME/bin/java"
```

The wrapper handles multi-module projects with `-pl` + `-am` correctly.

## Chinese Curly Quotes in Java Strings

When patching `.java` files that contain Chinese curly quotation marks (`\u201C`/`\u201D`, aka `"` and `"`) INSIDE Java string literals, the `patch` tool may silently convert them to ASCII `"` (0x22, U+0022). This **breaks compilation** because the ASCII `"` terminates the Java string, leaving placeholder text like `{{}}` outside any string literal.

**Symptoms in compiler output:**
```
error: 需要')'       (unclosed string, unexpected bare code)
error: 非法字符: '\uff0c'  (Chinese comma now outside string)
error: 未关闭的字符串字面量  (string closed early by corrupt quote)
```

**Verification with hex dump:**
```bash
sed -n '<line>' <file> | xxd | head -20
# Look for 0x22 where \u201C or \u201D should be
```

**Fix — use Java Unicode escapes `\u201C`/`\u201D`:**
```java
// BEFORE (broken): "您提交的对编号为："{{}}的协议的...
//                              ^^ ASCII 0x22, terminates string early
// AFTER (correct):
ExceptionChecker.throwException(
    "您提交的对编号为：\u201C{{}}\u201D的协议的变更请求校验异常，...",
    protocol.getProtocolNo());
```

The compiler resolves `\u201C` and `\u201D` at compile time, producing the correct Chinese curly quotes in the runtime string. The `patch` tool does not corrupt Unicode escapes (they are plain ASCII characters `\`, `u`, digits).

**Detection:** Before re-running Maven, grep for problematic patterns:
```bash
# Find lines where " inside a Java string looks like a corrupt Chinese quote
grep -n '""\|""' <file>    # will be empty if clean
grep -n '为："\|。"' <file>  # check for ASCII " near Chinese chars
```

## Multi-File Editing Strategy

When implementing a change that touches 3+ files:

1. **Interfaces first** (lowest risk, no implementation coupling)
2. **Utility/helper methods** (no callers yet)
3. **Implementation files** (referencing interfaces added in step 1)
4. **Callers** (last — they depend on everything above)

This order lets the compiler catch issues at each step rather than needing to reason about all cross-references at once.
