# 代码验证速查表

审查改动清单时的逐项验证流程。按此顺序检查，从数据层到调用链。

## 验证顺序

### 1. Entity / DTO 字段验证

```
search_files(pattern="class ProviderAgentAuthorizationEntity", file_glob="*.java", target="content")
→ read_file 检查是否有 marketId 等字段
```

关键检查：Entity 中字段是否存在、DTO 中传输字段是否对齐。

### 2. Service 方法签名验证

```
search_files(pattern="checkProviderDirState", file_glob="*.java", target="content")
→ 逐个 read_file 查看方法签名
```

关键检查：入参是否包含新字段、返回值类型是否变化。

### 3. SQL / MyBatis XML JOIN 验证

```
search_files(pattern="provider_agent_authorization", file_glob="*.xml", target="content")
→ read_file 查看 JOIN 条件
```

关键检查：JOIN 条件是否对齐 marketId / occurPlatCode，是否缺少过滤条件。

### 4. Feign 接口验证

```
search_files(pattern="方法名", file_glob="*.java", path=".../feign/")
→ 交叉对比 provider 端 Controller 和 client 端 FeignApi
```

关键检查：Feign 接口和 Controller 签名是否一致，调用方是否传入新参数。

### 5. 调用方验证

```
search_files(pattern="方法名(", file_glob="*.java", path=".../malltrade/")
→ 确认所有调用点都传了新参数
```

关键检查：跨服务调用是否同步升级，是否有遗漏的调用点。

### 6. LIMIT 1 / get(0) 检查

```
search_files(pattern="LIMIT 1|\.get\(0\)", file_glob="*.java", target="content")
→ 逐个判定是否需要改为市场维度查询
```

关键检查：多市场场景下 `get(0)` 会取错市场。

## 典型验证案例

### 案例：验证 `checkProviderDirState` 是否有 marketId

```
# Step 1: 搜 PrivateController（provider 端）
search_files(pattern="checkProviderDirState", file_glob="*.java", target="content")
# → 定位到 PrivateController.java:103

# Step 2: read_file 看签名
# → 签名: (providerOrgId, stockDirIds, occurPlatCode) — 无 marketId ✓

# Step 3: 搜 MallBaseFeignApi（client 端）
# → 签名一致，无 marketId ✓

# Step 4: 搜 malltrade 调用方
search_files(pattern="checkProviderOrgState", file_glob="*.java", path=".../malltrade/")
# → BusinessCheckServiceImpl.java:443 — 无 marketId ✓

# 结论：清单「需增 marketId」描述准确
```

### 案例：验证 `offShelfProviderGoods` 下架范围

```
# Step 1: 定位方法
search_files(pattern="offShelfProviderGoods", file_glob="*.java", target="content")
# → ProviderAgentAuthorizationServiceImpl.java:1367

# Step 2: read_file 看实现
# → L1376-1380: 查询 plat_market WHERE platCode = entity.occurPlatCode
# → 遍历所有 marketIds 下架

# 结论：当前是「全平台下架」，清单要求改为「仅 entity.marketId」✓
```

## 常见陷阱

- **XML 文件路径**：在 `src/main/resources/mapping/` 下，不是 `src/main/java/`
- **search_files 超时**：NTFS 大目录时退化为 `terminal grep -rn`
- **SVN 目录嵌套**：`master/` 下才是实际代码，不要直接在 `C1后端服务/商城基础/` 搜索
- **MVC/legacy 不在 mallbase/malltrade 中**：涉及门户浏览市场的改动需单独确认路径
