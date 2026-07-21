---
name: framework-contract-sql
description: "框架协议（协议供货/封闭式框架协议）日常SQL需求模板 — 征集项目、协议商品/耗材、导购目录、参数调整、成交统计、操作追踪、数据修复。仅限 ezc + trade 库。"
version: 2.1.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [框架协议, 协议供货, SQL, 政府采购, 封闭式框架协议]
    related_skills: [direct-purchase-sql]
---

# 框架协议 SQL 技能

## 数据库连接

| 项目 | 值 |
|------|-----|
| 主机 | 192.168.2.37 |
| 端口 | 31004 |
| 用户 | root |
| 密码 | mysql |
| 库 | ezc（核心59表）、trade（商品订单307表） |

**Navicat配置**：主机 192.168.2.37，端口 31004，用户名 root，密码 mysql
**注意**：框架协议涉及 2 个库，查询时加上库名前缀

## 主动查询能力

WSL 环境已通过 pymysql 打通数据库直连。

**跨库查询模式**：
```python
import pymysql
conn = pymysql.connect(host='192.168.2.37', port=31004, user='root', password='mysql', charset='utf8mb4')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM ezc.project')            -- 119个项目
cur.execute('SELECT COUNT(*) FROM trade.TG_G_ProviderQuote')  -- 报价数据
cur.close()
conn.close()
```

## 概述

框架协议系统日常SQL需求。涉及 `ezc`（核心59表）、`trade`（商品/订单） 两个库。

## 核心业务表

| 表名 | 库 | 说明 |
|------|----|------|
| `project` | ezc | 征集项目表 |
| `project_package` | ezc | 项目分包表 |
| `protocol` | ezc | 协议表 |
| `protocol_goods` | ezc | 协议商品表（含耗材） |
| `package_subject_matter` | ezc | 包件标的表 |
| `provider_quote` | ezc | 供应商报价表 |
| `provider_quote_detail` | ezc | 报价明细表 |
| `quote_detaill_param_value` | ezc | 报价参数值表 |
| `param_value_range` | ezc | 参数取值范围表 |
| `oper_record` | ezc | 操作记录表（审核流水） |
| `project_deal_configuration` | ezc | 项目成交配置表 |
| `TB_B_ShopGuideDir` | trade | 导购目录（递归树） |
| `TB_B_StockDir` | trade | 采购目录（递归树） |
| `TG_G_ProviderQuote` | trade | 供应商商品报价表 |
| `TB_Market` | trade | 市场表（集采/协议等） |
| `TF_Orders` | trade | 订单表（与直采共用） |
| `TF_O_ReceiveDetail` | trade | 订单-商品关联桥表（OrderId→CommerceGoodsId，核心关联！） |
| `TF_CommerceGoods` | trade | 订单商品明细表（目录/品牌/商品/数量/单价） |
| `order_contract` | trade | 订单合同表（contractNo、contractTime） |
| `trade_settlement` | trade | 结算/验收表（settlementState：0退回 1暂存 2审核中 3已完成） |
| `TB_B_StockDirBrand` | trade | 目录品牌表（StockDirId + BrandId/BrandName，定义每个目录下允许的品牌） |

## 常用查询分类

### 1. 征集项目/分包查询

```sql
SELECT p.projectName, p.projectNo, pp.packageNo, pp.packageName,
       pp.standStockDirName, pp.expectedCount
FROM ezc.project p LEFT JOIN ezc.project_package pp ON p.id = pp.projectId
WHERE p.projectNo = 'CQS25A00003';
```

**查询指定分包下的入围供应商数**：
```sql
SELECT pp.packageNo, pp.packageName, COUNT(DISTINCT pg.providerOrgId) AS provider_count
FROM ezc.project_package pp
INNER JOIN ezc.project p ON pp.projectId = p.id
INNER JOIN ezc.package_subject_matter sm ON pp.id = sm.packageId
INNER JOIN ezc.protocol_goods pg ON sm.id = pg.subjectMatterId
WHERE p.projectNo = 'CQS25A00003'
GROUP BY pp.packageNo, pp.packageName;
```

### 2. 协议商品/耗材查询

```sql
SELECT p.projectNo, pp.packageNo, pg.stockDirName, pg.goodsRepName,
       pg.goodsRepBrand AS '品牌', pg.model AS '型号', pg.quotePrice AS '价格',
       pg.providerOrgName AS '供应商'
FROM ezc.project p
INNER JOIN ezc.project_package pp ON p.id = pp.projectId
INNER JOIN ezc.protocol_goods pg ON pp.id = pg.packageId
WHERE pg.operState = 1 AND pg.stockDirName LIKE '%色带%';
```

**耗材征集数据（含参数-多表关联）**：
```sql
SELECT p.projectNo, pp.packageNo, pg.stockDirName AS '采购目录',
       pg.goodsRepName AS '耗材名称', pg.goodsRepBrand AS '品牌',
       pg.model AS '型号', pg.quotePrice AS '价格',
       pqdg.paramName AS '参数名称', pqdg.paramValue AS '参数值'
FROM ezc.project p
LEFT JOIN ezc.project_package pp ON p.id = pp.projectId
INNER JOIN ezc.protocol_goods pg ON pp.id = pg.packageId
INNER JOIN ezc.package_subject_matter sm ON pg.subjectMatterId = sm.id AND sm.isReqQuote = 1
LEFT JOIN ezc.provider_quote pq ON pg.providerOrgId = pq.providerOrgId AND pq.packageId = pp.id
LEFT JOIN ezc.provider_quote_detail pqd ON pq.id = pqd.quoteId
LEFT JOIN ezc.quote_detaill_param_value pqdg ON pqd.id = pqdg.detailId;
```

### 3. 导购目录相关

**递归查询某个导购目录及其子集**：
```sql
SET @dirName = '输入输出设备';
WITH RECURSIVE cte AS (
    SELECT * FROM trade.TB_B_ShopGuideDir WHERE ShopGuideDirName = @dirName
    UNION ALL
    SELECT t.* FROM trade.TB_B_ShopGuideDir t
    INNER JOIN cte ON t.UpStockDirId = cte.Id
)
SELECT * FROM cte ORDER BY xcjId;
```

**同步到集采市场**：见 `references/sync-guide-dir.md`

### 4. 参数范围调整

**查询和修改标的参数范围**：
```sql
-- 先查
SELECT a.*, b.* FROM ezc.param_value_range a
LEFT JOIN ezc.package_subject_matter b ON a.subjectMatterId = b.id
LEFT JOIN ezc.project_package c ON b.packageId = c.id
LEFT JOIN ezc.project d ON c.projectId = d.id
WHERE c.packageNo IN (30) AND a.paramName = '能源形式' AND d.projectNo = 'CQS26A00194';

-- 再改（先确认范围）
UPDATE ezc.param_value_range SET valueJson = '["新值"]'
WHERE subjectMatterId = (查询到的id) AND paramName = '能源形式';
```

### 5. 操作记录/审计追踪

**协议审核耗时**：
```sql
SELECT a.projectNo, a.packageNo, a.providerOrgName,
       a.createTime, b.operTime AS '提交', c.operTime AS '通过',
       ROUND(TIMESTAMPDIFF(HOUR, b.operTime, c.operTime), 2) AS '审核耗时(时)'
FROM ezc.protocol a
LEFT JOIN ezc.oper_record b ON a.id = b.businessId AND b.operName = '提交'
LEFT JOIN ezc.oper_record c ON a.id = c.businessId AND c.operName = '通过'
WHERE a.projectNo = 'CQS25A00003' ORDER BY b.operTime;
```

**商品审核耗时（含初审+复审，招标办常用）**：
```sql
SELECT b.projectNo, b.packageNo, b.providerOrgName,
       b.createTime, c.operTime AS '提交',
       d.operTime AS '初审通过', e.operTime AS '通过',
       ROUND(TIMESTAMPDIFF(HOUR, c.operTime, d.operTime), 2) AS '初审耗时(时)',
       ROUND(TIMESTAMPDIFF(HOUR, c.operTime, e.operTime), 2) AS '复审耗时(时)'
FROM ezc.protocol_goods a
LEFT JOIN ezc.protocol b ON a.protocolId = b.id
LEFT JOIN ezc.oper_record c ON a.id = c.businessId AND c.operName = '提交'
LEFT JOIN ezc.oper_record d ON a.id = d.businessId AND d.operName = '初审通过'
LEFT JOIN ezc.oper_record e ON a.id = e.businessId AND e.operName = '通过'
WHERE b.projectNo = 'CQS25A00003';
```

### 6. 订单/成交数据类

**⚠️ 核心关联链路**：`TF_Orders` → `TF_O_ReceiveDetail.OrderId` → `TF_O_ReceiveDetail.CommerceGoodsId` → `TF_CommerceGoods.Id`

> **常见陷阱**：`TF_CommerceGoods.CommerceId` **不是** `TF_Orders.Id`！不要用 CommerceId 直接 JOIN 订单表。唯一正确路径是通过 `TF_O_ReceiveDetail` 桥表。

**订单表头数据（含验收+合同，无商品明细）**：
```sql
SELECT o.OrdersNo, o.StockOrgName, o.ProviderOrgName, o.TotalPrice, o.EndTime,
       CASE ts.settlementState WHEN 3 THEN '已验收' WHEN 2 THEN '审核中'
            WHEN 1 THEN '暂存' WHEN 0 THEN '退回' WHEN -2 THEN '作废' ELSE '无'
       END AS '验收状态',
       CASE WHEN oc.editState = 2 THEN '已完成' ELSE '未完成' END AS '合同签订',
       oc.contractNo
FROM trade.TF_Orders o
LEFT JOIN trade.TF_O_ReqOrgInfo e ON o.Id = e.OrdersId
LEFT JOIN trade.trade_settlement ts ON o.Id = ts.orderId
LEFT JOIN trade.order_contract oc ON o.Id = oc.orderId
WHERE o.State IN (4, 6) AND o.VarId = 1392862688329338880;  -- VarId区分框架协议订单
```

**订单含商品明细（验收+合同+目录+品牌+商品+数量+单价）**：
```sql
SELECT o.StockOrgName       AS '采购单位',
       o.ProviderOrgName    AS '成交供应商',
       o.OrdersNo           AS '订单编号',
       oc.contractNo        AS '合同编码',
       cg.StockDirName      AS '成交目录',
       cg.BrandName         AS '成交品牌',
       cg.GoodsName         AS '厂家商品',
       cg.GoodsNum          AS '成交数量',
       cg.Price             AS '成交单价',
       ROUND(cg.GoodsNum * cg.Price, 2) AS '成交金额',
       oc.createTime        AS '合同确认时间',
       CASE ts.settlementState
            WHEN 3  THEN '已验收' WHEN 2 THEN '审核中'
            WHEN 1  THEN '暂存'   WHEN 0 THEN '退回'
            WHEN -2 THEN '作废'   ELSE '未验收'
       END                  AS '验收状态',
       o.CreateTime          AS '下单时间',
       o.State               AS '订单状态'
FROM trade.TF_Orders o
LEFT JOIN trade.order_contract oc ON o.Id = oc.orderId
LEFT JOIN trade.trade_settlement ts ON o.Id = ts.orderId
LEFT JOIN trade.TF_O_ReceiveDetail rd ON o.Id = rd.OrderId
LEFT JOIN trade.TF_CommerceGoods cg ON rd.CommerceGoodsId = cg.Id
WHERE o.VarId = 1392862688329338880
  AND o.State IN (4, 6)            -- 已确认/已完成
  AND (ts.settlementState IS NULL OR ts.settlementState != 3)  -- 未验收
ORDER BY o.CreateTime DESC;
```

**验收状态说明**（`trade_settlement.settlementState`）：
| 值 | 含义 |
|----|------|
| 3 | 已验收 |
| 2 | 审核中 |
| 1 | 暂存 |
| 0 | 退回 |
| -2 | 作废 |
| NULL | 未验收（无验收记录） |

**查询「未验收」订单**：用 `ts.settlementState IS NULL OR ts.settlementState != 3`，不能用 `IS NULL` 单条件——部分订单有 settlement 记录但状态不是 3（如退回、暂存），它们也算未验收。

### 7. 数据修复类

**修改供应商报价名称（公司改名）**：
```sql
SELECT DISTINCT ProviderOrgId, ProviderOrgName
FROM trade.TG_G_ProviderQuote WHERE ProviderOrgName = '旧名称';

UPDATE trade.TG_G_ProviderQuote SET ProviderOrgName = '新名称'
WHERE ProviderOrgName = '旧名称' AND State = 1;
```

**修复临时商品状态异常**（operState=0暂存 ↔ protocol_goods operState=-1退回）：
```sql
UPDATE trade.TG_TempGoods a
LEFT JOIN ezc.protocol_goods b ON a.id = b.goodsRepId AND b.operState = -1
SET a.operState = 1 WHERE a.operState = 0 AND b.id = 具体ID;
```

**触发数据同步**（修改时间戳触发）：
```sql
UPDATE ezc.project_package SET expectedCount = 1 WHERE projectId = 1602250458452504576;
UPDATE ezc.project_deal_configuration
SET lastModifyTime = DATE_ADD(lastModifyTime, INTERVAL 1 SECOND)
WHERE projectId = 1602250458452504576;
-- 恢复
UPDATE ezc.project_package SET expectedCount = NULL WHERE projectId = 1602250458452504576;
UPDATE ezc.project_deal_configuration
SET lastModifyTime = DATE_SUB(lastModifyTime, INTERVAL 1 SECOND)
WHERE projectId = 1602250458452504576;
```

### 8. 品牌匹配与确认状态更新

**场景**：供应商报价后，需要将其报价品牌（`shortlistbrandName`）与目录品牌（`trade.TB_B_StockDirBrand`）对比，匹配一致的更新品牌ID/名称并设置确认状态。

**核心关联**：`project_package.stockDirId` → `TB_B_StockDirBrand.StockDirId`
**报价品牌字段**：`provider_quote.shortlistbrandName`（供应商报价时填的品牌名称）

**第一步：查询匹配的数据（先确认影响范围）**

```sql
SET @projectId = (SELECT id FROM ezc.project WHERE projectNo = '项目编号');
SET @packageStart = 1;  -- 起始包号
SET @packageEnd = 50;   -- 结束包号

SELECT a.id, a.shortlistbrandName AS 报价品牌, b.BrandName AS 目录品牌,
       a.brandName AS 当前品牌, c.packageNo, c.packageName, a.editState
FROM ezc.provider_quote a
LEFT JOIN ezc.project_package c ON a.packageId = c.id
LEFT JOIN trade.TB_B_StockDirBrand b ON c.stockDirId = b.StockDirId
    AND a.shortlistbrandName = b.BrandName
WHERE b.Id IS NOT NULL
  AND a.shortlistbrandName IS NOT NULL
  AND a.projectId = @projectId
  AND a.enterpriseScale IS NOT NULL
  AND c.PackageNo BETWEEN @packageStart AND @packageEnd;
```

**第二步：更新品牌并设置确认状态**

editState 含义：
- `-1`：退回
- `0`：暂存
- `1`：审核中（提交审核）
- `2`：已确认/编辑完成

```sql
-- 先备份
CREATE TABLE test.provider_quote_bak_YYYYMMDD AS
SELECT a.* FROM ezc.provider_quote a
LEFT JOIN ezc.project_package c ON a.packageId = c.id
LEFT JOIN trade.TB_B_StockDirBrand b ON c.stockDirId = b.StockDirId
    AND a.shortlistbrandName = b.BrandName
WHERE b.Id IS NOT NULL AND a.shortlistbrandName IS NOT NULL
  AND a.projectId = @projectId AND a.enterpriseScale IS NOT NULL
  AND c.PackageNo BETWEEN @packageStart AND @packageEnd;

-- 更新 provider_quote：品牌ID/名称 + 确认状态
UPDATE ezc.provider_quote a
LEFT JOIN ezc.project_package c ON a.packageId = c.id
LEFT JOIN trade.TB_B_StockDirBrand b ON c.stockDirId = b.StockDirId
    AND a.shortlistbrandName = b.BrandName
SET a.brandId = b.BrandId,
    a.brandName = b.BrandName,
    a.editState = 2   -- 2=已确认（或1=提交审核）
WHERE b.Id IS NOT NULL
  AND a.shortlistbrandName IS NOT NULL
  AND a.projectId = @projectId
  AND a.enterpriseScale IS NOT NULL
  AND c.PackageNo BETWEEN @packageStart AND @packageEnd;

-- 同步更新 provider_quote_detail
UPDATE ezc.provider_quote_detail d
LEFT JOIN ezc.provider_quote a ON d.quoteId = a.id
LEFT JOIN ezc.project_package c ON a.packageId = c.id
LEFT JOIN trade.TB_B_StockDirBrand b ON c.stockDirId = b.StockDirId
    AND a.shortlistbrandName = b.BrandName
SET d.brandId = b.BrandId,
    d.brandName = b.BrandName
WHERE b.Id IS NOT NULL
  AND a.shortlistbrandName IS NOT NULL
  AND a.projectId = @projectId
  AND a.enterpriseScale IS NOT NULL
  AND c.PackageNo BETWEEN @packageStart AND @packageEnd;
```

**参考历史SQL**：`/mnt/d/平时处理文件/2026年1月/框架协议/框架协议同步确认中标详情.sql`

### 10. 特殊订单申请（非入围供应商申请）

**场景**：框架协议下采购人发起"特殊订单申请"（也称"非入围供应商申请"），邀请入围供应商响应报价，采购人可终止响应中的申请。

**⚠️ 命名混淆注意**：项目中存在两个不同的"非入围供应商授权"相关模块：
- **`provider_agent_authorization`**（#9 供应商代理商授权管理）— 供应商授权给销售代理商代为销售，后端在 `商城基础` 项目
- **`special_orders_apply`**（本节 特殊订单申请）— 采购人向非入围供应商发起询价申请，后端在 `行采家trade` 项目
- 当用户提到"有响应的未结束的，采购人可以终止"时，用的是 **`special_orders_apply`** 模块

**表**：`trade.special_orders_apply`

**状态枚举**（`SpecialOrderStateEnum`）：

| 值 | 含义 | 说明 |
|----|------|------|
| 1 | 暂存 | 采购人编辑未提交 |
| 2 | 入围供应商响应中 | 已提交，等待供应商报价响应 |
| 3 | 申请成功（待填写成交结果） | 供应商响应完毕，采购人待填结果 |
| 4 | 申请成功（已填写成交结果） | 采购人已填写成交结果 |
| 5 | 申请失败 | 无人响应或响应失败 |
| 6 | 申请终止 | 采购人手动终止（已有此状态） |

**核心字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `Id` | bigint | 主键 |
| `applyNo` | varchar(20) | 申请流水号 |
| `state` | tinyint | 状态（1-6 如上） |
| `stockOrgId` | bigint | 采购单位ID |
| `stockOrgName` | varchar(200) | 采购单位名称 |
| `providerOrgId` | bigint | 供应商ID |
| `providerOrgName` | varchar(200) | 供应商名称 |
| `varId` | bigint | 框架协议标识 |
| `varName` | varchar(100) | 框架协议名称 |
| `TotalPrice` | decimal | 总金额 |
| `submitTime` | datetime | 提交时间 |
| `resultDescription` | varchar(1000) | 结果说明 |

**查询采购人创建的申请列表**：
```sql
SELECT Id, applyNo, state, stockOrgName, providerOrgName,
       TotalPrice, submitTime
FROM trade.special_orders_apply
WHERE stockOrgId = 采购单位ID
  AND occurPlatCode = 'CQ_ZS'
ORDER BY createTime DESC;
```

**查询"响应中"可终止的申请**：
```sql
SELECT Id, applyNo, stockOrgName, providerOrgName,
       submitTime, TotalPrice
FROM trade.special_orders_apply
WHERE state = 2  -- 入围供应商响应中
  AND stockOrgId = 采购单位ID
  AND occurPlatCode = 'CQ_ZS'
ORDER BY submitTime DESC;
```

**终止操作实现要点**（采购人终止 state=2→state=6）：
- 接口：`POST /v1/public/special-orders-applys/terminate`
- 请求体：`{ "id": 申请ID, "terminateReason": "终止理由" }`
- 权限：`Roles.ANY_STOCK`（采购人）
- 校验：`checkSpecialOrdersApplyState(id, PROVIDER_RESPONSE)`（必须是 state=2）
- 终止理由通过 `oper_record.remark` 记录，**不需在表上加字段**
- 操作类型：`OperTypeEnum.CANCEL`，操作名 `"终止"`
- 后端路径：`行采家trade/branches/optimization/xcj-trade/`
  - Controller：`.../controller/outer/special/SpecialOrdersApplyController.java`
  - Service：`.../service/special/SpecialOrdersApplyServiceImpl.java`
  - DTO：`.../dto/special/SpecialOrdersApplyDTO.java`（含 `TerminateDTO` 内部类）

**查询操作记录（含终止理由）**：
```sql
SELECT * FROM trade.oper_record
WHERE businessType = 'SPECUIAL_ORDER_APPLY'
  AND businessId = 申请ID
ORDER BY operTime DESC;
```

### 11. 非入围供应商授权管理

⚠️ 本节涉及 xcj_mall_base 库（直采商城范围），详见 direct-purchase-sql skill。
当需要查询授权列表、授权状态、终止操作时，请加载 direct-purchase-sql skill。

## 工作流指引

### 优先查历史SQL
用户有重复出现的框架协议SQL需求。**先查历史SQL文件**，可能有现成模板比从头写更快：
- 位置：`/mnt/d/平时处理文件/YYYY年M月/框架协议/`
- 也检查 `框架协议-线上问题记录.md`、`direct-purchase-issues` skill
- 用户参考自己历史的SQL是常见的，不要等用户提醒才去查

## 常用项目号参考
|--------|------|
| CQS25A00003 | 2025年度乘用车（新能源车）封闭式框架协议 |
| CQS26A00194 | 2026年度乘用车（新能源车）封闭式框架协议 |

## 月度工作文件

脚本路径：`~/.hermes/skills/dogfood/direct-purchase-sql/scripts/generate_month_file.py`

每月1号9:00自动在 `/mnt/d/平时处理文件/2026年X月/框架协议/` 下生成带模板的SQL工作文件。

## 📁 SQL文件保存约定（必须遵守）

用户明确要求：**所有框架协议和直采商城的SQL文件必须保存到月度工作目录下**，不允许保存到 /tmp/ 或其他临时目录。

| 类型 | 路径 |
|------|------|
| 框架协议SQL | `/mnt/d/平时处理文件/2026年X月/框架协议/` |
| 直采商城SQL | `/mnt/d/平时处理文件/2026年X月/直采商城/` |

文件名格式：`描述_YYYYMMDD.sql`（如 `供应商入驻及报价查询_20260529.sql`）

> **⚠️ 常见错误**：Session中写SQL后直接 `write_file` 到 `/tmp/` 会被用户纠正。**必须先确认当月目录**，直接写入对应月文件夹。

## 注意事项

1. **DML前必须备份到 test 库**，先SELECT确认影响范围
2. ezc=框架协议核心，trade=商品/订单（与直采共享），注意库前缀别落
3. 导购目录同步涉及递归CTE+叉乘，注意主键自增逻辑
4. 集采市场按 trade.TB_Market.MarketType=3 / label='集中采购' 区分
5. 框架协议订单通过 VarId=1392862688329338880 区分
6. WSL直连查库用 pymysql，不要用 `os.system('mysql ...')`，因 mysql CLI 未安装

## ⚠️ oper_record 表数据范围与清理情况

**ezc.oper_record 已被清理/归档**，当前仅保留到 **2025-09-16**（共503条记录）。所有2026年的审核操作记录已不在此表中。如果用户查询近期（2026年）的审核数据，需先说明该情况。

同一服务器上共有6个数据库包含 `oper_record` 表，各自覆盖不同业务域：

| 数据库 | 数据截至 | 业务域 |
|--------|---------|--------|
| `ezc.oper_record` | 2025-09-16（503条） | 框架协议审核流水（已清理） |
| `trade.oper_record` | 2026-03-04（1014条） | 订单/合同/撤单/验收 |
| `xcjenquiry.oper_record` | 至今（10万+条） | 询价系统 |
| `xcjexpert.oper_record` | 至今 | 专家系统 |
| `oea.oper_record` | 至今 | OA/合同 |
| `xcj_eri.oper_record` | 至今 | 网上报名 |

**框架协议审核操作名对照**（ezc.oper_record）：
- 协议签订复审：`businessId=protocol.id` + `operName='通过'`（采购中心复审）
- 入库商品初审：`businessId=protocol_goods.id` + `operName='初审通过'`（大家软件）
- 入库商品复审：`businessId=protocol_goods.id` + `operName='通过'`（采购中心复审）
- 升级换代审核：`protocol_goods.operState=6`（换代审核）或 `protocol_change.changeType=3`
- 协议签订操作人：operOrgUserName 记录操作人姓名（如"唐元景"、"卢彦名"）

**若用户需要2026年审核统计数据**，建议询问：
1. 是否有 oper_record 的备份或归档表
2. 是否可以从应用层日志/微服务数据库查到（如 djc_ecoco、djc_selector 等）
3. 是否有其他数据库实例
