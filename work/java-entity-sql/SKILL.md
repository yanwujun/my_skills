---
name: java-entity-sql
description: Generate SQL DDL, upgrade scripts, and fix SQL from Java Entity classes. Covers Entity→DDL conversion, MyBatis XML query debugging, common pitfalls in MyBatis batch operations, and sorting issues. Use when the user says "根据这个Entity写SQL", "这个SQL为什么不生效", "写升级SQL", or asks about MyBatis XML queries.
---

# Java Entity → SQL Development

Generate and fix SQL from Java Entity classes in a Spring Boot + MyBatis codebase. Covers the full cycle: DDL generation, upgrade scripts, MyBatis XML debugging, and common MyBatis pitfalls.

## Trigger conditions

- User says "根据这个 Entity 写 DDL/升级 SQL/修改 SQL"
- User provides an Entity class and asks for corresponding SQL
- User says "这个 SQL/排序为什么不生效" (MyBatis debugging)
- User asks about MyBatis updateBatchById, foreach, or sorting behavior
- User provides MyBatis XML and asks "是否正确" or "有什么问题"

## Step 1: Entity → DDL conversion

When given a Java Entity class, generate standard DDL following these conventions:

### Conventions (observed from user's codebase)
- Table name matches `@TableName` annotation or class name (snake_case)
- Field names are snake_case in SQL
- Every column gets a COMMENT based on `@ApiModelProperty` or field context
- Use `bigint(20)` for Long IDs
- Use `varchar(N)` for String with appropriate length from `@Size` or annotations
- Use `datetime` for Date fields
- Use `decimal(M,D)` for BigDecimal
- Primary key: `@TableId` annotation → `PRIMARY KEY (id)`
- Default values: match Java field defaults

### Template

```sql
-- Add column to existing table
ALTER TABLE `table_name` 
ADD COLUMN `field_name` DATA_TYPE DEFAULT default_value COMMENT 'field_comment';

-- Or new table DDL
CREATE TABLE IF NOT EXISTS `table_name` (
  `id` bigint(20) NOT NULL COMMENT '主键ID',
  `field1` varchar(50) DEFAULT NULL COMMENT '说明',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表说明';
```

### Upgrade SQL pattern
- Always use `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (MySQL 8.0+) or check existence manually
- Include rollback comment (how to revert)
- Note which version/release this upgrade belongs to

## Step 2: MyBatis XML query debugging

When MyBatis XML queries don't produce expected results:

### Common pitfalls (in priority order)

1. **foreach on empty collection**: MyBatis silently produces invalid SQL when the collection is empty and no empty-collection guard exists.
   ```xml
   <!-- BAD: breaks on empty list -->
   <foreach collection="ids" item="id" open="AND id IN (" close=")" separator=",">
     #{id}
   </foreach>
   
   <!-- GOOD: guard against empty -->
   <if test="ids != null and ids.size() > 0">
     AND id IN
     <foreach collection="ids" item="id" open="(" close=")" separator=",">
       #{id}
     </foreach>
   </if>
   ```

2. **updateBatchById does NOT clear null fields**: MyBatis-Plus `updateBatchById` only updates non-null fields. Setting a field to null in Java will NOT update it to NULL in the database.

3. **Sorting not applied**: If `.orderByDesc()` in Java doesn't work, check:
   - MyBatis interceptor may strip ORDER BY (check `MybatisPlusConfig`)
   - Default sorting in the entity `@TableField` may conflict
   - Pagination plugin may override ORDER BY

4. **Missing `@Param` annotation**: When passing multiple parameters, MyBatis needs `@Param("name")` to map.

5. **AND without prefix**: Multiple `<if>` conditions without a wrapping `<where>` or leading `1=1` can produce broken SQL.
   ```xml
   <!-- BAD: first true condition starts with AND -->
   SELECT * FROM table WHERE
   <if test="a != null">AND a = #{a}</if>
   <if test="b != null">AND b = #{b}</if>
   
   <!-- GOOD -->
   SELECT * FROM table
   <where>
     <if test="a != null">AND a = #{a}</if>
     <if test="b != null">AND b = #{b}</if>
   </where>
   ```

## Step 3: Complex query patterns

### Mandatory-inclusion pagination ("必含供应商" pattern)

When the user needs specific records always included in paginated results:

```java
// Pattern: first query normal page, then query mandatory records, merge and trim
List<Entity> normalPage = repository.selectPage(page, query);
List<Entity> mandatory = repository.selectByIds(mandatoryIds);

// Merge, deduplicate, and trim to page size
Set<Long> seen = new HashSet<>();
List<Entity> result = new ArrayList<>();

// Add mandatory first
for (Entity e : mandatory) {
    if (seen.add(e.getId())) result.add(e);
}

// Fill remaining from normal page
for (Entity e : normalPage) {
    if (seen.add(e.getId()) && result.size() < pageSize) result.add(e);
}
```

Pitfalls:
- If mandatory count > page size, throw error early
- Only apply mandatory logic to page 1 (subsequent pages use normal pagination)
- Max 2 database queries (not N+1)

### Platform isolation

Government procurement system uses `occurPlatCode` or `__platDomain__` for multi-tenant isolation. When modifying queries, always check if the WHERE clause includes platform isolation.

## Step 4: SQL script file location

From user conventions:
- Save SQL scripts to `D:\平时处理文件\<年份月份>\<模块>\`
- Each requirement gets its own file, no aggregation
- Windows path format, not Linux/WSL paths

## Step 5: Offer to run against database

After generating SQL, ask the user if they want to execute it. If they have MCP MySQL configured, offer to run it against the appropriate environment (test3, show1, etc.).

**Important**: DDL (ALTER/CREATE/DROP) statements can only run on environments that support DDL through MCP. The MCP `execute_write` tool may be restricted to INSERT/UPDATE/DELETE only on some connections. Always check first.

## Pitfalls

- Never assume MySQL version — use portable syntax
- `datetime` vs `timestamp` — `datetime` is usually preferred (no timezone conversion)
- Character set: always `utf8mb4` (not `utf8`)
- Index names: follow convention `idx_table_field`
- When user provides Entity code in Chinese context, field comments should be in Chinese
- MyBatis-Plus `LambdaQueryWrapper` may not translate all conditions correctly — verify generated SQL via debug logging

## References

- `references/mybatis-common-errors.md` — Detailed MyBatis error patterns and fixes
