---
name: entity-to-sql
description: >-
  从 Java Entity 类生成 DDL SQL（建表/加字段/升级SQL）。
  用户提供 Entity 文件路径或类名，自动生成符合项目规范的 SQL 脚本并输出到 D:\平时处理文件\ 对应月目录。
  支持：CREATE TABLE、ALTER TABLE 加字段、IF NOT EXISTS、COMMENT。
---

# Entity → SQL 生成器

## 触发条件

用户消息包含以下任一模式时加载本技能：
- "写 SQL" / "创建 SQL" / "升级 SQL" / "修改 SQL"
- "根据 Entity 写 DDL" / "生成建表语句"
- "@XxxEntity.java" + "字段"/"sql"

## 工作流程

### 1. 确认输入

- 用户可能通过 `@` 引用 Entity 文件，也可能直接说类名。
- 若用户未指定 Entity，询问：「需要为哪个 Entity 生成 SQL？」
- 若用户说"升级 SQL"，是加字段场景（ALTER TABLE），不是建表。

### 2. 读取 Entity

- 在当前工作区搜索 Entity 文件：`*Entity.java` 或用户指定的文件名。
- 读取 Entity 类，提取：
  - `@TableName` → 表名
  - 每个字段的 `@TableField` → 列名（无则用驼峰转下划线）
  - 字段类型 → MySQL 类型映射
  - `@TableId` → 主键
  - 注释/JavaDoc → COMMENT

### 3. 类型映射表

| Java 类型 | MySQL 类型 |
|-----------|-----------|
| `String` | `VARCHAR(255)`（有 `@Column(length=N)` 则 `VARCHAR(N)`） |
| `Long` / `long` | `BIGINT` |
| `Integer` / `int` | `INT` |
| `BigDecimal` | `DECIMAL(18,2)`（金额）或 `DECIMAL(10,2)` |
| `Date` / `LocalDate` | `DATE` |
| `LocalDateTime` / `Timestamp` | `DATETIME` |
| `Boolean` | `TINYINT(1)` |
| `byte[]` / `Blob` | `LONGBLOB` |
| `text` / 大文本 | `TEXT` 或 `LONGTEXT` |

### 4. 生成 SQL

#### 建表 (CREATE TABLE)

```sql
-- 文件名: 01_create_xxx.sql
CREATE TABLE IF NOT EXISTS `{tableName}` (
  `{column1}` {type} NOT NULL COMMENT '{注释}',
  `{column2}` {type} DEFAULT NULL COMMENT '{注释}',
  ...
  PRIMARY KEY (`{pk}`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{表注释}';
```

- 主键 `BIGINT NOT NULL`，不用 AUTO_INCREMENT（项目用雪花 ID）。
- 每个字段必须带 COMMENT。
- 所有表和字段名用反引号。

#### 加字段 (ALTER TABLE - 升级 SQL)

```sql
-- 文件名: 02_upgrade_xxx_add_字段名.sql
ALTER TABLE `{tableName}`
  ADD COLUMN IF NOT EXISTS `{column}` {type} DEFAULT NULL COMMENT '{注释}';
```

- MySQL 5.7 不支持 `IF NOT EXISTS` 时用存储过程实现，或标注「需 DBA 确认字段不存在」。

### 5. 输出路径

```
D:\平时处理文件\YYYY年M月\{模块名}\{序号}_{描述}.sql
```

- 从当前月份和模块名自动构建路径。
- 若用户未指定模块名，从项目/包名推断（如 `xcj-mallbase` → `直采商城`，`xcj-ezc` → `框架协议`）。

### 6. 输出格式

```markdown
## 生成的 SQL

**输出路径**: D:\平时处理文件\2026年6月\直采商城\01_create_xxx.sql

**变更摘要**:
- 新增表 `xxx`，N 个字段

\`\`\`sql
... SQL 内容 ...
\`\`\`
```

## 注意事项

- 不要运行 SQL，只生成文件。
- 字段名严格按照 Java 驼峰 → 数据库下划线规则。
- 金额字段默认 `DECIMAL(18,2)`。
- 每个字段必须有 COMMENT。
- 涉及的 Entity 有 `createTime`/`updateTime` 时自动加上。
