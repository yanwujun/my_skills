# 依赖链追溯案例：直采商城（mallbase + malltrade）

> 记录实际遇到的编译失败依赖链、根因和修复方案。
> 用于快速匹配错误信息并定位缺失的文件。

## 案例1：platform-bom 缺失（BOM import 链）

### 错误信息
```
Failed to collect dependencies at 
  com.djc:djc-basedata-client:jar:1.14.0-SNAPSHOT 
  → com.gec.stddata:gec-stddata-rpcapi:jar:1.3.0 
  → Failed to read artifact descriptor for com.gec.stddata:gec-stddata-rpcapi:jar:1.3.0 
  → Could not find artifact com.gmsoft:platform-bom:pom:1.0.1-20200413.070047-1
```

### 根因分析
```
gec-stddata-rpcapi:1.3.0
  → 父POM: gec-stddata-root:1.3.0
    → 祖父POM: com.gmsoft:basic:1.0.0-SNAPSHOT
      → dependencyManagement中 import platform-bom:${gmsoft.version}
        → ${gmsoft.version} = 1.0.1-SNAPSHOT（来自 properties）
          → 具体时间戳: 1.0.1-20200413.070047-1
```

### 修复
- 源仓库路径: `com/gmsoft/platform-bom/1.0.1-SNAPSHOT/`
- Maven 搜索路径: `com/gmsoft/platform-bom/1.0.1-20200413.070047-1/`
- **两个目录都需复制**：SNAPSHOT 目录（含时间戳文件） + 独立时间戳目录

---

## 案例2：djc-flowable 三连击（artifactId 极易混淆）

### 错误2a: djc-flowable-bom:1.9.2-20230518.080737-5
```
Failed to collect dependencies at 
  com.gec:gec-stockapply-client:jar:1.42.25-SNAPSHOT 
  → com.zcj:zcj-contract-core:jar:1.48.8-SNAPSHOT 
  → Could not find artifact com.djc:djc-flowable-bom:pom:1.9.2-20230518.080737-5
```

### 错误2b: djc-flowable:pom:1.9.2-20230518.080634-5
```
Failed to collect dependencies at 
  com.gec:gec-stockapply-client:jar:1.42.25-SNAPSHOT 
  → com.zcj:zcj-contract-core:jar:1.48.8-SNAPSHOT 
  → Could not find artifact com.djc:djc-flowable:pom:1.9.2-20230518.080634-5
```

### 错误2c: djc-flowable-core:1.9.2-20230519.061438-6
```
Could not find artifact com.djc:djc-flowable-core:pom:1.9.2-20230519.061438-6
```

### 关键区别（重要！）
| artifactId | 目录 | 时间戳 | 
|-----------|------|--------|
| `djc-flowable` | `com/djc/djc-flowable/1.9.2-SNAPSHOT/` | `080634-5` |
| `djc-flowable-bom` | `com/djc/djc-flowable-bom/1.9.2-SNAPSHOT/` | `080737-5` |
| `djc-flowable-core` | `com/djc/djc-flowable-core/1.9.2-SNAPSHOT/` | `061438-6` |

### 修复
每个 artifact 需要两个目录：
```
com/djc/djc-flowable/1.9.2-SNAPSHOT/          ← 时间戳文件放这里
com/djc/djc-flowable/1.9.2-20230518.080634-5/ ← Maven 真正查找的目录
```

### 常见陷阱
- 看到报错 `djc-flowable-bom` 以为已修复（之前复制过），忽略了三胞胎的另外两个
- 检查时必须逐个 artifact ID 确认，不能只看 groupId + version

---

## 案例3：gec-org 缺失（artifact 类型混淆）

### 错误信息
```
com.gec:gec-org-core:jar:1.18.1 was not found
```

### 根因
用户报错是 `gec-org-core:1.18.1`，但当时目标仓库中已有 `gec-org-core:1.18.0` 和 `1.24.7-security-SNAPSHOT`，唯独没有 `1.18.1`。

同时用户反馈缺少的还有 `gec-org:1.18.1`（无 `-core`），这是另一个 artifact（pom 类型父工程），也需要独立复制。

### 修复
```
com/gec/gec-org-core/1.18.1/   ← jar + pom (1.3MB)
com/gec/gec-org/1.18.1/       ← pom only (父工程类型)
```

---

## 案例4：失败缓存污染（隐藏杀手）

### 错误信息
```
This failure was cached in the local repository and resolution is 
not reattempted until the update interval of nexus has elapsed or 
updates are forced
```

### 根因
目标机器之前尝试从 Nexus 解析失败，生成了 `.lastUpdated` 或 `resolver-status.properties`。即使把正确的 jar 文件复制过去，Maven 依然跳过不检查。

### 修复
在目标机器上：
```bash
# 1. 删除缓存的失败记录
rm -rf ~/.m2/repository/com/gec/gec-org-core/1.18.1/

# 2. 或者用离线模式（跳过 Nexus 检查）
mvn compile -o -Dmaven.repo.local=D:\mallrepository
```

### 预防
在提取仓库时**必须清理**目标目录中的 `_remote.repositories` 和 `resolver-status.properties` 文件。

---

## 速查：硬编码 BOM import 版本表

以下是从 POM 中直接提取（非变量版本）的关键 BOM：

| BOM groupId | BOM artifactId | 版本 | 来源 |
|-------------|---------------|------|------|
| com.gmsoft | platform-bom | 1.0.1-20200413.070047-1 | com.gmsoft:basic:1.0.0-SNAPSHOT |
| org.springframework | spring-framework-bom | 4.3.2.RELEASE | com.gmsoft:basic:1.0.0-SNAPSHOT |
| org.springframework.boot | spring-boot-dependencies | 1.4.0.RELEASE | com.gmsoft:basic:1.0.0-SNAPSHOT |
| org.glassfish.jersey | jersey-bom | 2.23.1 | com.gmsoft:basic:1.0.0-SNAPSHOT |
| org.springframework.cloud | spring-cloud-dependencies | Brixton.RELEASE | com.gmsoft:basic:1.0.0-SNAPSHOT |

---

## 案例5：djc-flowable:1.5.0-20220119.071011-5（时间戳目录源仓库也没有）

### 错误信息
```
Failed to collect dependencies at 
  com.gec:gec-stockapply-client:jar:1.42.25-SNAPSHOT 
  → com.zcj:zcj-contract-core:jar:1.48.8-SNAPSHOT 
  → com.xcj:xcj-stockapplyindependent-core:jar:1.9.6-SNAPSHOT 
  → Could not find artifact com.djc:djc-flowable:pom:1.5.0-20220119.071011-5
```

### 根因
`djc-flowable:1.5.0` 在依赖列表中出现了（从 `dependency:resolve` 解析），但两个关键文件缺失：

1. `1.5.0-SNAPSHOT/` 目录内的 `.pom` 文件
2. `1.5.0-20220119.071011-5/` 独立时间戳目录（Maven 离线模式查找的目标）

**更关键的问题：源仓库也没有独立时间戳目录！** 文件都在 `1.5.0-SNAPSHOT/` 目录下。
必须在目标仓库中**手动创建** `1.5.0-20220119.071011-5/` 目录。

### 源仓库情况
```
com/djc/djc-flowable/1.5.0-SNAPSHOT/
├── djc-flowable-1.5.0-20220119.071011-5.pom     ← 时间戳文件名，在SNAPSHOT目录内
├── djc-flowable-1.5.0-SNAPSHOT.pom
├── maven-metadata-nexus.xml                     ← 记录了两个版本号的映射
└── _remote.repositories

# 源仓库没有：com/djc/djc-flowable/1.5.0-20220119.071011-5/ （独立目录不存在！）
```

### maven-metadata.xml 内容
```xml
<metadata>
  <groupId>com.djc</groupId>
  <artifactId>djc-flowable</artifactId>
  <version>1.5.0-SNAPSHOT</version>
  <versioning>
    <snapshot>
      <timestamp>20220119.071011</timestamp>
      <buildNumber>5</buildNumber>
    </snapshot>
  </versioning>
</metadata>
```

### 修复命令
```bash
# 1. 先确保 SNAPSHOT 目录存在
mkdir -p /tmp/mallrepository/com/djc/djc-flowable/1.5.0-SNAPSHOT
cp /mnt/d/apache-maven/localRepository3.6.3/com/djc/djc-flowable/1.5.0-SNAPSHOT/djc-flowable-1.5.0-20220119.071011-5.pom /tmp/mallrepository/com/djc/djc-flowable/1.5.0-SNAPSHOT/

# 2. 创建独立时间戳目录（源仓库也没有，手动创建！）
mkdir -p /tmp/mallrepository/com/djc/djc-flowable/1.5.0-20220119.071011-5
cp /mnt/d/apache-maven/localRepository3.6.3/com/djc/djc-flowable/1.5.0-SNAPSHOT/djc-flowable-1.5.0-20220119.071011-5.pom /tmp/mallrepository/com/djc/djc-flowable/1.5.0-20220119.071011-5/
```

### 教训
**源仓库的 maven-metadata.xml 中记录的每个 `<snapshotVersion>`，都需要在目标仓库中创建对应的独立时间戳目录。** 源仓库本身可能没有这些目录（它只把文件放在 `-SNAPSHOT/` 内），但 Maven 在离线模式下需要独立目录才能找到文件。

---

## 案例6：验证不到位导致反复出错（过程层面）

### 典型错误循环
```
用户报错 → 我说"已补齐" → 用户检查发现没有 → 我说"重新复制" → 还是不在 → ...
```

### 根因
**只看了脚本日志（"copied X files"），没有用 `ls` 实际验证文件是否在目标仓库。** 本session中发生过两次：
1. `djc-flowable:1.5.0-SNAPSHOT` 我说复制了但实际没有 → 原因是写到了另一个仓库路径
2. `platform-bom:1.0.1-20200413.070047-1` 我说复制了但实际没有 → 也是路径问题

### 修复
**每次复制后必须执行验证：**
```bash
# ✅ 正确验证
ls -la /tmp/mallrepository/com/djc/djc-flowable/1.5.0-SNAPSHOT/
# 确认看到至少一个 .pom 文件

# ❌ 错误验证
# 只看脚本输出 "copied 1 files" 就汇报
```

### 教训
- 复制操作用绝对路径，避免混淆
- 每次汇报前做 `ls` 确认
- 尤其注意是否因为 `mallrepository` vs `mallrepository-precise` 等路径混淆导致文件写到别处
