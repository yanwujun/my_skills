#!/usr/bin/env python3
"""
生成直采商城月度SQL工作文件。

每月自动在 /mnt/d/平时处理文件/2026年X月/ 下创建：
  - /直采商城/ 目录及工作文件
  - /框架协议/ 目录及工作文件

用法：
  python3 generate_month_file.py [YYYY年M月]  # 默认当前月

示例：
  python3 generate_month_file.py "2026年5月"
"""

import os
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = "/mnt/d/平时处理文件"


def get_month_folder():
    """获取月份文件夹名，如 '2026年5月'"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    now = datetime.now()
    return f"{now.year}年{now.month}月"


def write_work_file(filepath, system_name, sections):
    """写入工作文件"""
    lines = [
        f"-- ============================================================",
        f"-- {system_name} 月度SQL工作文件",
        f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- ============================================================",
        f"-- 数据库: 192.168.2.37:31004 | root / mysql",
        f"-- ============================================================",
        f"-- 注意: 所有DML操作前请先SELECT确认影响范围，并备份到test库",
        f"-- ============================================================",
        f"",
        f"-- ============================================================",
        f"-- 一、本月新增SQL需求",
        f"-- (请在此记录本月实际处理的SQL需求，每个需求加时间备注)",
        f"-- ============================================================",
        f"",
        f"-- [示例] YYYY-MM-DD 需求描述",
        f"-- SELECT ...",
        f"-- UPDATE ...",
        f"",
        f"-- ============================================================",
        f"-- 二、常用查询模板",
        f"-- ============================================================",
        f"",
    ]

    for title, sql in sections:
        lines.append(f"-- ============================================================")
        lines.append(f"-- {title}")
        lines.append(f"-- ============================================================")
        lines.append(sql)
        lines.append("")

    lines.append(f"-- ============================================================")
    lines.append(f"-- 三、本月线上问题")
    lines.append(f"-- (简要记录本期处理的线上问题，详细方案见 -线上问题记录.md)")
    lines.append(f"-- 主记录文件: D:\\平时处理文件\\{system_name}-线上问题记录.md")
    lines.append(f"-- ============================================================")
    lines.append(f"-- 日期       | 问题简述                      | 严重程度 | 状态")
    lines.append(f"-- -----------|-------------------------------|---------|------")
    lines.append(f"")
    lines.append(f"-- ============================================================")
    lines.append(f"-- 四、本月备份记录")
    lines.append(f"-- (创建备份表后在此记录表名和备注)")
    lines.append(f"-- ============================================================")
    lines.append(f"-- 备份表         | 说明")
    lines.append(f"-- ---------------|---------------------------------------------")

    content = "\n".join(lines)
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def generate_direct_purchase(month_folder):
    """生成直采商城工作文件"""
    # 直采商城目录
    dir_path = os.path.join(BASE_DIR, month_folder, "直采商城")
    file_path = os.path.join(dir_path, f"直采商城SQL工作文件_{month_folder}.sql")

    sections = [
        # 模板1：商品导出
        ("导出商品信息", """\
-- 导出某平台已上架商品
SET @platCode = 'XCJ';  -- 替换平台编码
SELECT a.Id AS '报价ID', a.ProviderOrgName, c.GoodsName, c.StockDirName, c.model,
       a.QuotePrice, c.Units, a.QuoteTime
FROM xcj_mall_base.TG_G_ProviderQuote a
INNER JOIN xcj_mall_base.plat_market b ON a.marketId = b.marketId
INNER JOIN xcj_mall_base.TG_Goods c ON a.goodsId = c.Id
WHERE b.platCode = @platCode AND a.State = 1
ORDER BY a.ProviderOrgId, c.BrandName, c.model;
"""),
        # 模板2：供应商入驻查询
        ("查询入驻供应商", """\
SELECT pm.marketName AS '商城类型', pm.platCode,
       e.providerOrgName, e.providerOrgCode,
       e.providerLinkMan, e.providerLinkMobile,
       COALESCE(e.applyAuditTime, e.createTime) AS '入驻时间'
FROM xcj_mall_base.provider_enter e
INNER JOIN xcj_mall_base.plat_market pm ON pm.platCode = e.occurPlatCode
WHERE e.valid = 1 AND e.state IN (2, 5)
ORDER BY pm.marketName, e.providerOrgName;
"""),
        # 模板3：订单查询
        ("查询订单及验收状态", """\
SELECT o.OrdersNo, o.StockOrgName, o.ProviderOrgName,
       o.TotalPrice, o.EndTime, e.ItemNo,
       CASE ts.settlementState WHEN 3 THEN '已验收' WHEN 2 THEN '审核中'
            WHEN 1 THEN '暂存' WHEN 0 THEN '退回' ELSE '无' END AS '验收状态',
       oc.contractNo
FROM xcj_mall_base.TF_Orders o
LEFT JOIN xcj_mall_base.TF_O_ReqOrgInfo e ON o.Id = e.OrdersId
LEFT JOIN xcj_mall_base.trade_settlement ts ON o.Id = ts.orderId
LEFT JOIN xcj_mall_base.order_contract oc ON o.Id = oc.orderId
WHERE o.State IN (4, 6) AND o.EndTime IS NOT NULL;
"""),
        # 模板4：平台同步
        ("平台同步模板", """\
-- 替换 @source_plat 和 @target_plat
SET @source_plat = 'XCJ';
SET @target_plat = 'cqdj';

-- 1) 供应商入驻同步（先查后插）
SELECT e.providerOrgName, COUNT(1) AS to_sync
FROM xcj_mall_base.provider_enter e
WHERE e.occurPlatCode = @source_plat AND e.valid = 1
  AND NOT EXISTS (SELECT 1 FROM xcj_mall_base.provider_enter e2
    WHERE e2.providerOrgId = e.providerOrgId AND e2.occurPlatCode = @target_plat AND e2.valid = 1);
"""),
    ]

    write_work_file(file_path, "直采商城", sections)
    return file_path


def generate_framework_contract(month_folder):
    """生成框架协议工作文件"""
    dir_path = os.path.join(BASE_DIR, month_folder, "框架协议")
    file_path = os.path.join(dir_path, f"框架协议SQL工作文件_{month_folder}.sql")

    sections = [
        # 模板1：项目查询
        ("征集项目查询", """\
SELECT p.projectName, p.projectNo, pp.packageNo, pp.packageName,
       pp.standStockDirName, pp.expectedCount
FROM ezc.project p
LEFT JOIN ezc.project_package pp ON p.id = pp.projectId
WHERE p.projectNo = 'CQS26A00194'
ORDER BY pp.packageNo;
"""),
        # 模板2：协议商品查询
        ("协议商品查询", """\
SELECT p.projectNo, pp.packageNo, pg.stockDirName, pg.goodsRepName,
       pg.goodsRepBrand AS '品牌', pg.model AS '型号', pg.quotePrice AS '价格',
       pg.providerOrgName AS '供应商'
FROM ezc.project p
INNER JOIN ezc.project_package pp ON p.id = pp.projectId
INNER JOIN ezc.protocol_goods pg ON pp.id = pg.packageId
WHERE pg.operState = 1;
"""),
        # 模板3：导购目录递归查询
        ("递归查询导购目录", """\
SET @dirName = '输入输出设备';
WITH RECURSIVE cte AS (
    SELECT * FROM trade.TB_B_ShopGuideDir WHERE ShopGuideDirName = @dirName
    UNION ALL
    SELECT t.* FROM trade.TB_B_ShopGuideDir t
    INNER JOIN cte ON t.UpStockDirId = cte.Id
)
SELECT * FROM cte ORDER BY xcjId;
"""),
        # 模板4：操作记录
        ("查看协议审核耗时", """\
SELECT a.projectNo, a.packageNo, a.providerOrgName,
       a.createTime, b.operTime AS '提交', c.operTime AS '通过',
       ROUND(TIMESTAMPDIFF(HOUR, b.operTime, c.operTime), 2) AS '审核耗时(时)'
FROM ezc.protocol a
LEFT JOIN ezc.oper_record b ON a.id = b.businessId AND b.operName = '提交'
LEFT JOIN ezc.oper_record c ON a.id = c.businessId AND c.operName = '通过'
WHERE a.projectNo = 'CQS25A00003'
ORDER BY b.operTime;
"""),
    ]

    write_work_file(file_path, "框架协议", sections)
    return file_path


def main():
    month_folder = get_month_folder()
    print(f"生成 {month_folder} 月度SQL工作文件...")

    # 检查是否已存在
    dp_file = os.path.join(BASE_DIR, month_folder, "直采商城")
    fc_file = os.path.join(BASE_DIR, month_folder, "框架协议")

    dp_existing = list(Path(dp_file).glob("*.sql")) if os.path.isdir(dp_file) else []
    fc_existing = list(Path(fc_file).glob("*.sql")) if os.path.isdir(fc_file) else []

    if dp_existing or fc_existing:
        print(f"  注意：目录下已有SQL文件，将追加写入新文件:")
        if dp_existing:
            print(f"    直采商城: {[f.name for f in dp_existing]}")
        if fc_existing:
            print(f"    框架协议: {[f.name for f in fc_existing]}")

    dp_path = generate_direct_purchase(month_folder)
    fc_path = generate_framework_contract(month_folder)

    print(f"  ✓ 直采商城: {dp_path}")
    print(f"  ✓ 框架协议: {fc_path}")
    print("")
    print("请使用 skill_view(name='direct-purchase-sql') 查看直采商城SQL模板")
    print("请使用 skill_view(name='framework-contract-sql') 查看框架协议SQL模板")


if __name__ == "__main__":
    main()
