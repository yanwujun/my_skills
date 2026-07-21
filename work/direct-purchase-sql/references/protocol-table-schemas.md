# 直采商城协议表 Schema 参考

> 库：`xcj_mall_base`
> 4张表构成直采商城协议体系，关系如下：
> ```
> collect_project (协议项目)
>   ├── collect_shortlist (入围供应商)       ← 供应商维度，每个供应商一条
>   │     └── collect_project_goods (协议商品)  ← 商品维度，每个商品一条
>   └── collect_project_stock_org (协议采购人)  ← 采购单位维度，每个单位一条
> ```

---

## 1. collect_project — 协议项目

**ID是否自增**：❌ 否，需手动生成  
**建表/改表时间**: `collect_project` / `collect_shortlist` 新表（行采家自建表，2025年新建）

| 字段 | 类型 | 可空 | 必填 | 说明 |
|------|------|------|------|------|
| id | bigint(20) | NO | ✅ | PK，手动生成（参考现有值范围） |
| projectName | varchar(100) | NO | ✅ | 项目名称，如"2026年办公设备框架协议" |
| projectNo | varchar(20) | YES | ✅ | 项目编号，如 ZJ2026001 |
| projectType | varchar(1) | YES | ✅ | A=货物 B=工程 C=服务 |
| occurPlatCode | varchar(255) | YES | ✅ | 业务发生平台，如 XCJ |
| validityStartTime | datetime(3) | YES | ✅ | 协议生效日期 |
| validityEndTime | datetime(3) | YES | ✅ | 协议截止日期 |
| createOrgId | bigint(20) | YES | 建议 | 创建单位ID |
| createOrgName | varchar(50) | YES | 建议 | 创建单位名称 |
| collectOrgId | bigint(20) | YES | 建议 | 征集单位ID |
| collectOrgName | varchar(100) | YES | 建议 | 征集单位名称 |
| collectOrgLinkManName | varchar(100) | YES | 可选 | 征集联系人 |
| collectOrgLinkTel | varchar(50) | YES | 可选 | 联系电话 |
| collectOrgLinkMobile | varchar(50) | YES | 可选 | 联系手机 |
| agentOrgLinkMobile | varchar(50) | YES | 可选 | 代理机构手机 |
| chargeFlag | tinyint(1) | YES | 可选 | 1=收费 null=不收费 |
| createTime | datetime(3) | YES | 自动 | 默认为当前时间 |

---

## 2. collect_shortlist — 入围供应商（协议供应商）

**ID是否自增**：✅ 是，自动生成

| 字段 | 类型 | 可空 | 必填 | 说明 |
|------|------|------|------|------|
| id | bigint(20) | NO | 自动 | PK，自增，无需手动生成 |
| projectId | bigint(20) | NO | ✅ | 关联 collect_project.id |
| providerOrgId | bigint(20) | NO | ✅ | 供应商ID（provider_enter表） |
| providerOrgName | varchar(100) | NO | ✅ | 供应商名称 |
| protocolNo | varchar(30) | YES | ✅ | 协议号，每个供应商唯一，如 XY-KJ-2026-0001 |
| occurPlatCode | varchar(255) | YES | ✅ | 平台编码 |
| validityStartTime | datetime(3) | YES | 建议 | 协议生效日期 |
| validityEndTime | datetime(3) | YES | 建议 | 协议截止日期 |
| projectNo | varchar(20) | YES | 建议 | 冗余字段：项目编号 |
| projectName | varchar(100) | YES | 建议 | 冗余字段：项目名称 |
| collectOrgId | bigint(20) | YES | 建议 | 征集单位ID |
| collectOrgName | varchar(100) | YES | 建议 | 征集单位名称 |
| providerOrgLinkManName | varchar(100) | YES | 可选 | 供应商联系人 |
| providerOrgLinkMobile | varchar(50) | YES | 可选 | 供应商手机 |
| providerOrgAddress | varchar(500) | YES | 可选 | 供应商地址 |
| brandId | bigint(20) | YES | 可选 | 入围品牌ID |
| brandName | varchar(100) | YES | 可选 | 入围品牌名 |
| packageId | bigint(20) | YES | 按需 | 采购包ID（分包用） |
| packageNo | int(11) | YES | 按需 | 包编号 |
| packageName | varchar(200) | YES | 按需 | 包名称 |
| viewPlatCode | varchar(500) | YES | 可选 | 可见平台，多个逗号分隔 |
| createTime | datetime(3) | YES | 自动 | 默认当前时间 |
| itemCount | int(11) | YES | 自动 | 协议商品数量（默认0） |

---

## 3. collect_project_goods — 协议商品

**ID是否自增**：❌ 否，需手动生成

| 字段 | 类型 | 可空 | 必填 | 说明 |
|------|------|------|------|------|
| id | bigint(20) | NO | ✅ | PK，手动生成 |
| projectId | bigint(20) | NO | ✅ | 关联 collect_project.id |
| shortlistId | bigint(20) | YES | ✅ | 关联 collect_shortlist.id |
| goodsId | bigint(20) | NO | ✅ | 商品ID（TG_Goods中已存在） |
| goodsName | varchar(100) | NO | ✅ | 商品名称 |
| stockDirId | bigint(20) | NO | ✅ | 采购目录ID（TB_B_StockDir中有效） |
| stockDirName | varchar(100) | NO | ✅ | 采购目录名称 |
| unit | varchar(20) | NO | ✅ | 计量单位，如"台""平方米·月""次" |
| quotePrice | decimal(18,4) | NO | ✅ | 入围单价（限价），保留4位小数 |
| providerOrgId | bigint(20) | YES | ✅ | 供应商ID |
| providerOrgName | varchar(100) | YES | ✅ | 供应商名称 |
| occurPlatCode | varchar(255) | YES | ✅ | 平台编码 |
| protocolNo | varchar(30) | YES | 建议 | 协议号（冗余） |
| goodsRepBrandId | bigint(20) | YES | 建议 | 品牌ID |
| model | varchar(100) | YES | 建议 | 型号规格 |
| packageId | bigint(20) | YES | 按需 | 采购包ID |
| packageNo | int(11) | YES | 按需 | 包编号 |
| packageName | varchar(200) | YES | 按需 | 包名称 |
| areaCode | tinyint(4) | YES | 可选 | 1=主城区 2=非主城区 null=不区分 |
| imagePath | varchar(200) | YES | 可选 | 商品图片路径 |
| viewPlatCode | varchar(500) | YES | 可选 | 可见平台，多个逗号分隔 |
| chargeUnit | varchar(20) | YES | 自动 | 计价单位，默认"元" |
| priceValidityStartTime | datetime(3) | YES | 可选 | 价格有效期起 |
| priceValidityEndTime | datetime(3) | YES | 可选 | 价格有效期止 |
| sourceType | int(11) | YES | 自动 | 数据来源类型 |
| createTime | datetime(3) | YES | 自动 | 默认当前时间 |

---

## 4. collect_project_stock_org — 协议采购人

**ID是否自增**：✅ 是，自动生成  
**唯一索引**：`(projectId, stockOrgId)` — 不可重复插入同一采购人

| 字段 | 类型 | 可空 | 必填 | 说明 |
|------|------|------|------|------|
| id | bigint(20) | NO | 自动 | PK，自增 |
| projectId | bigint(20) | NO | ✅ | 关联 collect_project.id |
| stockOrgId | bigint(20) | NO | ✅ | 采购单位ID |
| stockOrgName | varchar(200) | NO | ✅ | 采购单位名称 |
| occurPlatCode | varchar(255) | YES | ✅ | 平台编码 |
| areaCode | tinyint(4) | YES | 可选 | 1=主城 2=非主城 |
| viewPlatCode | varchar(500) | YES | 可选 | 可见平台 |
| createTime | datetime(3) | YES | 自动 | 默认当前时间 |

---

## 5. 初始化注意事项

### 插入顺序
```
1️⃣ collect_project          → 拿到 projectId（手动生ID）
2️⃣ collect_shortlist        → 拿到 shortlistId（自增）
3️⃣ collect_project_goods    → 引用 projectId + shortlistId（手动生ID）
4️⃣ collect_project_stock_org → 引用 projectId（自增）
```

### 关键校验
- **`collect_project.id`**：不自增，需参考现有数据规则生成（避免冲突）
- **`collect_project_goods.id`**：不自增，同上
- **`collect_shortlist.id`**：自增，不用填
- **`collect_project_stock_org.id`**：自增，不用填
- **`(projectId, stockOrgId)` 唯一**：不可重复插入同一采购人
- **`goodsId`**：必须是 `TG_Goods` 中已存在的商品ID
- **`providerOrgId`**：必须是 `provider_enter` 中已入驻的供应商（state IN (2,5)）
- **`stockDirId`**：必须是 `TB_B_StockDir` 中有效的目录节点
- **`occurPlatCode`**：必须是 `plat_market` 中存在的平台编码

### Excel模板字段规则
生成初始化xlsx模板时：
- 每字段=一列，每数据=一行
- 第1行：中文标题 + （必填）/（选填）标记
- 第2行：英文字段名（数据库列名，灰底小字参考）
- 第3行起：数据行
