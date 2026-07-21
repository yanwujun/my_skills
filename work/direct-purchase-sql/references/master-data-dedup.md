# 主数据去重流程（品牌/分类/供应商等）

## 适用场景

主表（如 TB_B_Brand）中因首尾空格、大小写差异、导入重复等原因，产生同一名称多条记录，需要：
1. 合并外键引用到保留的那条记录
2. TRIM清洗保留的记录名
3. 删除冗余记录

## 前置检查

### 1. 发现重复

```sql
-- 忽略大小写+空格后的重复查找
SELECT UPPER(TRIM(name_column)) AS clean_name,
       COUNT(1) AS cnt,
       GROUP_CONCAT(Id ORDER BY Id) AS ids,
       GROUP_CONCAT(CONCAT('"', name_column, '"') ORDER BY Id) AS original_names
FROM target_table
GROUP BY UPPER(TRIM(name_column))
HAVING COUNT(1) > 1
ORDER BY cnt DESC;
```

> ⚠️ 使用 `CONCAT('"', name, '"')` 包裹名称可以看到首尾空格。

### 2. 检查各重复对的引用情况

```sql
-- 对每个重复对，查每个引用表的命中数
SELECT tbl, col, old_id, COUNT(1) AS ref_count FROM ...
```

### 3. 确定保留/删除策略

| 条件 | 策略 |
|------|------|
| 一个ID有引用，另一个0引用 | 保留有引用的 |
| 两个都有引用 | 保留引用更多的 |
| 两个都0引用 | 保留名称干净的（无首尾空格） |

### 4. 建备份

```sql
DROP TABLE IF EXISTS test.table_bak_YYYYMMDD;
CREATE TABLE test.table_bak_YYYYMMDD AS SELECT * FROM xcj_mall_base.source_table;
```

**每个会修改的表都要单独备份。**

## 执行合并

### 5. 更新引用表（CASE WHEN 批量）

```sql
UPDATE xcj_mall_base.target_table
SET BrandId = CASE BrandId
    WHEN old_id_1 THEN keep_id_1
    WHEN old_id_2 THEN keep_id_2
    ...
END
WHERE BrandId IN (old_id_1, old_id_2, ...);
```

> ⚠️ 注意列名大小写：`BrandId` vs `brandId`。不同表可能不一致，先 `DESC table` 确认。

### 6. TRIM清洗保留记录

```sql
UPDATE xcj_mall_base.target_table
SET brand_name = TRIM(brand_name)
WHERE brand_name != TRIM(brand_name);
```

### 7. 删除冗余记录

```sql
DELETE FROM xcj_mall_base.target_table WHERE Id IN (old_id_1, old_id_2, ...);
```

## 验证

```sql
-- 确认无剩余重复
SELECT UPPER(TRIM(name_column)), COUNT(1)
FROM target_table
GROUP BY UPPER(TRIM(name_column))
HAVING COUNT(1) > 1;

-- 确认删除的ID不再被引用
SELECT COUNT(1) FROM referencing_table WHERE fk_column IN (deleted_ids);
```

## 本系统引用 BrandId 的表一览

| 表 | 库 | 字段名 | 类型 |
|----|-----|-------|------|
| TG_Goods | xcj_mall_base | BrandId | bigint |
| base_goods | xcj_mall_base | BrandId | bigint |
| TG_G_Provider | xcj_mall_base | BrandId | bigint |
| TB_B_StockDirBrand | xcj_mall_base | BrandId | bigint |
| spu_goods | xcj_mall_base | brandId | bigint |
| TB_B_StockDirSeries | xcj_mall_base | BrandId | bigint |
| TB_M_Variety | xcj_mall_base | BrandId | bigint |
| TG_TempGoods | xcj_mall_base | BrandId | bigint |
| collect_shortlist | xcj_mall_base | brandId | bigint |
| provider_response_detail | xcj_mall_base | brandId | bigint |
| orders_makeup_goods | xcj_mall_base | brandId | bigint |
| TG_S_ZGCBrandContrast | xcj_mall_base | BrandId | bigint |

> trade库也有相同表名，但经检查无引用这些品牌ID的数据，无需处理。

## TB_B_Brand 表结构

| 字段 | 类型 | 说明 |
|------|------|------|
| Id | bigint PK | 主键 |
| BrandName | varchar(100) | 品牌名称（有空格问题） |
| State | tinyint | 状态 |
| Mnemonic | varchar(100) | 助记码 |
| CZBBrandName | varchar(100) | 财政品牌名 |
| GenuineVerifyURL | varchar(500) | 正品验证URL |
