-- ============================================================
-- 框架协议入围结果快速确认
-- 用途: 匹配供应商报价品牌与目录品牌一致后，快速确认入围结果
-- 适用: ezc 库的框架协议征集项目（closed framework contract）
-- 创作: 2026-05-07
-- 来源: D:\平时处理文件\2026年5月\框架协议\框架协议入围结果快速确认.sql
-- ============================================================
-- 核心逻辑:
--   1. provider_quote.shortlistbrandName 是供应商报价时填报的品牌
--   2. project_package.stockDirId 关联到采购目录
--   3. trade.TB_B_StockDirBrand 是目录品牌表（StockDirId → BrandName）
--   4. 当 shortlistbrandName 匹配到 TB_B_StockDirBrand.BrandName 时，品牌一致
--   5. 匹配上的数据：更新 brandId/brandName（从目录品牌取值），设置 editState
--   6. 不同步更新 provider_quote_detail
-- ============================================================

-- ============================================================
-- 【使用前必改参数】
-- ============================================================
set @projectId=1609896021155164160;  -- 改成目标项目ID
set @packageNo1=1;                    -- 起始包号
set @packageNo2=98;                   -- 结束包号

-- ============================================================
-- 第一步：查询匹配的（品牌一致 → 可以确认的）
-- ============================================================
select a.*, c.packageName, b.BrandName as 目录品牌
from ezc.provider_quote as a 
left join ezc.project_package as c on a.`packageId`=c.id
LEFT JOIN trade.TB_B_StockDirBrand as b
    on c.`stockDirId`=b.StockDirId and a.`shortlistbrandName`=b.`BrandName`
where b.Id is not null
  and a.shortlistbrandName is not null
  and a.`projectId`=@projectId
  and a.enterpriseScale is not null
  and c.PackageNo between @packageNo1 and @packageNo2;

-- ============================================================
-- 第二步：查询不匹配的（品牌不一致 → 需要人工处理）
-- ============================================================
select a.`shortlistbrandName`, b.`BrandName`
from ezc.provider_quote as a 
left join ezc.project_package as c on a.`packageId`=c.id
LEFT JOIN trade.TB_B_StockDirBrand as b
    on c.`stockDirId`=b.StockDirId and a.`shortlistbrandName`=b.`BrandName`
where b.Id is null
  and a.shortlistbrandName is not null
  and a.`projectId`=@projectId
  and a.enterpriseScale is not null
  and c.PackageNo between @packageNo1 and @packageNo2;

-- ============================================================
-- 【DML操作前请备份到test库】
-- ============================================================
-- CREATE TABLE test.provider_quote_bak_20260507 AS
-- SELECT * FROM ezc.provider_quote WHERE projectId = @projectId;

-- ============================================================
-- 第三步：更新 provider_quote（匹配上的，设置品牌和状态）
-- editState: 1=提交审核 | 2=已确认
-- ============================================================
update ezc.provider_quote as a 
left join ezc.project_package as c on a.`packageId`=c.id
LEFT JOIN trade.TB_B_StockDirBrand as b
    on c.`stockDirId`=b.StockDirId and a.`shortlistbrandName`=b.`BrandName`
set a.`brandId`=b.BrandId, a.`brandName`=b.`BrandName`, a.editState=1
where b.Id is not null
  and a.shortlistbrandName is not null
  and a.`projectId`=@projectId
  and a.enterpriseScale is not null
  and c.PackageNo between @packageNo1 and @packageNo2;

-- ============================================================
-- 第四步：同步更新 provider_quote_detail
-- ============================================================
update ezc.provider_quote_detail as d
LEFT JOIN ezc.provider_quote as a on d.`quoteId`=a.`id`
left join ezc.project_package as c on a.`packageId`=c.id
LEFT JOIN trade.TB_B_StockDirBrand as b
    on c.`stockDirId`=b.StockDirId and a.`shortlistbrandName`=b.`BrandName`
set d.`brandId`=b.BrandId, d.`brandName`=b.`BrandName`
where b.Id is not null
  and a.shortlistbrandName is not null
  and a.`projectId`=@projectId
  and a.enterpriseScale is not null
  and c.PackageNo between @packageNo1 and @packageNo2;
