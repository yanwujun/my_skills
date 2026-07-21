-- =============================================================================
-- 直采商城品牌去重 — 通用SQL脚本 (v3)
-- 适用于 xcj_mall_base.TB_B_Brand 表因首尾空格导致品牌重复的场景
-- 按 TRIM(BrandName) 去重，大小写不同的视为不同品牌
-- =============================================================================

-- █ 第0步：查看所有含品牌字段的表及其数据量
SELECT 
    t.TABLE_SCHEMA, 
    t.TABLE_NAME, 
    t.TABLE_ROWS AS '预估记录数',
    TRUNCATE(t.DATA_LENGTH / 1024 / 1024, 2) AS '数据容量(MB)',
    TRUNCATE((t.DATA_LENGTH + t.INDEX_LENGTH) / 1024 / 1024, 2) AS '总大小(MB)'
FROM information_schema.TABLES t
WHERE t.TABLE_SCHEMA = 'xcj_mall_base'
  AND t.TABLE_NAME != 'TB_B_Brand'
  AND t.TABLE_NAME IN (
      SELECT c.TABLE_NAME
      FROM information_schema.COLUMNS c
      WHERE c.TABLE_SCHEMA = 'xcj_mall_base'
        AND c.COLUMN_NAME IN ('BrandId', 'brandId', 'BrandID', 'brand_id', 'goodsRepBrandId')
  )
ORDER BY t.TABLE_ROWS DESC;


-- █ 第一步：映射表 — 查出重复品牌（删除ID→保留ID）
CREATE TABLE test.brand_duplicate_map (
    brand_name VARCHAR(100),
    keep_id    BIGINT,
    delete_id  BIGINT,
    PRIMARY KEY (delete_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 按 TRIM(BrandName) 分组，保留最小ID
INSERT INTO test.brand_duplicate_map (brand_name, keep_id, delete_id)
SELECT
    t.clean_name,
    t.keep_id,
    d.Id AS delete_id
FROM (
    SELECT TRIM(BrandName) AS clean_name, MIN(Id) AS keep_id
    FROM xcj_mall_base.TB_B_Brand
    GROUP BY TRIM(BrandName)
    HAVING COUNT(1) > 1
) t
INNER JOIN xcj_mall_base.TB_B_Brand d
    ON TRIM(d.BrandName) = t.clean_name AND d.Id != t.keep_id
ORDER BY t.clean_name;

-- 看看哪些品牌重复
SELECT * FROM test.brand_duplicate_map;


-- █ 第二步：更新所有引用表的 BrandId

-- ===== BrandId（驼峰8张） =====
UPDATE xcj_mall_base.TB_B_StockDirBrand t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id SET t.BrandId = m.keep_id;
UPDATE xcj_mall_base.TB_B_StockDirSeries t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id SET t.BrandId = m.keep_id;
UPDATE xcj_mall_base.TG_G_Provider     t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id SET t.BrandId = m.keep_id;
UPDATE xcj_mall_base.TG_Goods          t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id SET t.BrandId = m.keep_id;
UPDATE xcj_mall_base.base_goods        t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id SET t.BrandId = m.keep_id;
UPDATE xcj_mall_base.TF_CommerceGoods  t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id SET t.BrandId = m.keep_id;
UPDATE xcj_mall_base.TG_TempGoods      t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id SET t.BrandId = m.keep_id;
UPDATE xcj_mall_base.TF_E_QuoteDetail  t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id SET t.BrandId = m.keep_id;

-- ===== brandId（小写2张） =====
UPDATE xcj_mall_base.spu_goods             t INNER JOIN test.brand_duplicate_map m ON t.brandId = m.delete_id SET t.brandId = m.keep_id;
UPDATE xcj_mall_base.collect_shortlist      t INNER JOIN test.brand_duplicate_map m ON t.brandId = m.delete_id SET t.brandId = m.keep_id;

-- ===== goodsRepBrandId（商品代表品牌1张） =====
UPDATE xcj_mall_base.collect_project_goods  t INNER JOIN test.brand_duplicate_map m ON t.goodsRepBrandId = m.delete_id SET t.goodsRepBrandId = m.keep_id;


-- █ 第三步：清理品牌主表
-- 3a. TRIM 保留品牌的名称（清除首尾空格）
UPDATE xcj_mall_base.TB_B_Brand b
INNER JOIN (
    SELECT DISTINCT keep_id FROM test.brand_duplicate_map
) m ON b.Id = m.keep_id
SET b.BrandName = TRIM(b.BrandName);

-- 3b. 删除重复行
DELETE b FROM xcj_mall_base.TB_B_Brand b
INNER JOIN test.brand_duplicate_map m ON b.Id = m.delete_id;


-- █ 第四步：验证
-- 4a. 检查是否还有重复
SELECT TRIM(BrandName) AS name, COUNT(1) AS cnt
FROM xcj_mall_base.TB_B_Brand
GROUP BY TRIM(BrandName)
HAVING COUNT(1) > 1;

-- 4b. 检查删除ID是否在引用表中还有残留（全为0则OK）
SELECT 'TB_B_StockDirBrand' AS ref, COUNT(1) FROM xcj_mall_base.TB_B_StockDirBrand  t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id UNION ALL
SELECT 'TB_B_StockDirSeries', COUNT(1) FROM xcj_mall_base.TB_B_StockDirSeries  t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id UNION ALL
SELECT 'TG_G_Provider',       COUNT(1) FROM xcj_mall_base.TG_G_Provider        t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id UNION ALL
SELECT 'TG_Goods',            COUNT(1) FROM xcj_mall_base.TG_Goods             t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id UNION ALL
SELECT 'base_goods',          COUNT(1) FROM xcj_mall_base.base_goods           t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id UNION ALL
SELECT 'TF_CommerceGoods',    COUNT(1) FROM xcj_mall_base.TF_CommerceGoods     t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id UNION ALL
SELECT 'TG_TempGoods',        COUNT(1) FROM xcj_mall_base.TG_TempGoods         t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id UNION ALL
SELECT 'TF_E_QuoteDetail',    COUNT(1) FROM xcj_mall_base.TF_E_QuoteDetail     t INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id UNION ALL
SELECT 'spu_goods',           COUNT(1) FROM xcj_mall_base.spu_goods            t INNER JOIN test.brand_duplicate_map m ON t.brandId = m.delete_id UNION ALL
SELECT 'collect_shortlist',   COUNT(1) FROM xcj_mall_base.collect_shortlist    t INNER JOIN test.brand_duplicate_map m ON t.brandId = m.delete_id UNION ALL
SELECT 'collect_project_goods',COUNT(1) FROM xcj_mall_base.collect_project_goods t INNER JOIN test.brand_duplicate_map m ON t.goodsRepBrandId = m.delete_id;


-- █ 清理临时对象（确认无误后执行）
-- DROP TABLE IF EXISTS test.brand_duplicate_map;
