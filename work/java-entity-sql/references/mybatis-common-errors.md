# MyBatis Common Errors & Fixes

Collected from real debugging sessions in the P2040 government procurement system (Spring Boot + MyBatis-Plus).

## 1. updateBatchById doesn't clear fields

**Symptom**: Setting a field to `null` in Java, calling `updateBatchById()`, but the database still has the old value.

**Root cause**: MyBatis-Plus `updateBatchById` uses dynamic SQL — it only includes non-null fields in the UPDATE SET clause. Setting a field to `null` means the field is excluded from the update.

**Fix**: Use explicit SQL or set the field to a sentinel value (empty string, 0) instead of null. Or use `UpdateWrapper` with explicit `set(field, null)`.

**Real session example** (2026-05): User set `pkg.setQuoteId(null)` before `updateBatchById(packages)`, expecting quoteId to be cleared. MyBatis skipped the null field.

## 2. foreach on empty list produces invalid SQL

**Symptom**: Query works when collection has items, but returns wrong results (or errors) when empty.

**Root cause**: `<foreach>` with no items produces SQL like `AND id IN ()` which is invalid.

**Fix**: Always wrap foreach in `<if test="collection != null and collection.size() > 0">`.

## 3. ORDER BY stripped by pagination interceptor

**Symptom**: `.orderByDesc("field")` appears in code but final SQL has no ORDER BY or wrong ordering.

**Root cause**: MyBatis-Plus pagination plugin (`PaginationInterceptor`) may count total rows first, then re-query with its own ordering — stripping the original ORDER BY.

**Fix**: 
- Check if `MybatisPlusConfig` has a custom interceptor
- Use `Page.setOrders()` instead of relying on wrapper
- For complex sorting, use manual XML `<choose>` blocks

**Real session example** (2026-04): `ProviderQuoteServiceImpl` orderBy sort not working despite `result.setOrders(orders)` having values.

## 4. AND without wrapping `<where>` tag

**Symptom**: First dynamic condition produces SQL starting with `AND`.

**Root cause**: Multiple `<if>` blocks directly inside WHERE without `<where>` wrapper.

**Fix**: Use `<where>` tag which automatically strips leading AND/OR:
```xml
<where>
  <if test="a != null">AND a = #{a}</if>
  <if test="b != null">AND b = #{b}</if>
</where>
```

Or use `WHERE 1=1` prefix (less elegant but works).

## 5. Missing @Param for multiple parameters

**Symptom**: `Parameter 'xxx' not found` or wrong parameter binding.

**Root cause**: MyBatis requires `@Param("name")` when a method has multiple parameters. Without it, parameters are accessed as `arg0`, `arg1`, etc. or `param1`, `param2`.

**Fix**: Add `@Param` to all parameters in mapper interface methods with 2+ parameters.

## 6. N+1 queries from eager fetching

**Symptom**: Slow performance, many small queries logged.

**Root cause**: Calling a service/repository inside a loop over query results.

**Fix**: Batch fetch related data with a single query using `IN (ids)` pattern, then join in Java.

**Real session example** (2026-04): Querying mandatory suppliers after pagination — user correctly limited to 2 DB queries maximum.

## 7. Field name mapping mismatch

**Symptom**: Column value is NULL despite data existing.

**Root cause**: Java field name (camelCase) doesn't match database column (snake_case), and MyBatis auto-mapping fails.

**Fix**: Add `@TableField("column_name")` or enable `map-underscore-to-camel-case: true` in application.yml.

## 8. Docker/network issues causing "Communications link failure"

**Symptom**: `com.mysql.cj.jdbc.exceptions.CommunicationsException: Communications link failure` in WSL.

**Root cause**: WSL's networking layer may lose connectivity to Windows-host MySQL.

**Fix**: 
- Check if MySQL is running: `ss -tlnp | grep 3306`
- Use Windows IP (`ipconfig | grep IPv4` in Windows, not localhost)
- Restart WSL: `wsl --shutdown` then reopen

## Summary checklist for MyBatis debugging

When a query doesn't work:
1. Enable SQL logging: `logging.level.com.xxx.repository=DEBUG`
2. Check the actual SQL output (not the MyBatis XML)
3. Verify parameter binding
4. Check for interceptors modifying the SQL
5. Verify database schema matches Entity fields
6. Test the raw SQL directly in MySQL client
