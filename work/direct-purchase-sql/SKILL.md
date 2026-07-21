---
name: direct-purchase-sql
description: "直采商城（智采商城/行采家）日常SQL需求模板 — 商品查询、供应商管理、协议项目、目录授权、数据清理。仅限 xcj_mall_base 库。"
version: 2.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [直采商城, 智采商城, SQL, 行采家, 政府采购]
    related_skills: [framework-contract-sql]
---

# 直采商城 SQL 技能

## 数据库连接

| 项目 | 值 |
|------|-----|
| 主机 | 192.168.2.37 |
| 端口 | 31004 |
| 用户 | root |
| 密码 | mysql |
| 主库 | xcj_mall_base（326张表） |
| 其他库 | stddata（60表） |

**Navicat配置**：主机 192.168.2.37，端口 31004，用户名 root，密码 mysql，库名 xcj_mall_base

## 主动查询能力

**方式一（推荐）— MCP工具调用**（需要 Hermes Agent 重启生效）：
如果 MCP MySQL server 已配置（`mcp_servers.mysql` in config.yaml），可以直接使用工具查询：
- `mcp_mysql_execute_query` — SELECT 查询，参数 `query`、`connection_id`
- `mcp_mysql_list_tables` — 列出表，参数 `connection_id`
- `mcp_mysql_describe_table` — 表结构，参数 `table_name`、`connection_id`

Connection ID 对应关系：`default`=xcj_mall_base, `stddata`=stddata

**方式二 — pymysql直连**（WSL下已打通）

WSL 环境已通过 pymysql 打通数据库直连，无需 Navicat 中转即可执行任意 SQL。

**快捷查询工具**（推荐，不用手写Python连接代码）：
```bash
# 直采商城查询（默认库 xcj_mall_base）
python3 ~/.hermes/skills/dogfood/direct-purchase-sql/scripts/run_query.py "SELECT COUNT(*) FROM TG_Goods WHERE State=1"

# 指定库名
python3 ~/.hermes/skills/dogfood/direct-purchase-sql/scripts/run_query.py trade "SELECT State, COUNT(*) FROM TF_Orders GROUP BY State"

# 框架协议查询
python3 ~/.hermes/skills/dogfood/direct-purchase-sql/scripts/run_query.py ezc "SELECT projectName, projectNo FROM project ORDER BY id DESC LIMIT 5"
```

> ⚠️ **run_query.py 不支持多语句一次性执行**：不要用 `;` 分隔多个 SELECT 传给 run_query，会报 1064 语法错误。需要每次只传一条 SQL，或分别调用多次。

**或者用原始Python连接模式**（更灵活）：
```python
import pymysql
conn = pymysql.connect(host='192.168.2.37', port=31004, user='root', password='mysql',
                       database='库名', charset='utf8mb4')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM TG_Goods WHERE State=1')
print(cur.fetchone()[0])
cur.close()
conn.close()
```

**快捷方式（终端单条 SQL）**：
```bash
python3 -c "
import pymysql
c = pymysql.connect(host='192.168.2.37', port=31004, user='root', password='mysql', database='xcj_mall_base', charset='utf8mb4')
r = c.cursor()
r.execute('SELECT COUNT(*) FROM TG_Goods')
print(r.fetchone()[0])
r.close(); c.close()
"
```

**跨库查询**（限 xcj_mall_base + stddata；如需跨 ezc/trade 请加载 framework-contract-sql skill）：
```python
conn = pymysql.connect(host='192.168.2.37', port=31004, user='root', password='mysql', charset='utf8mb4')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM xcj_mall_base.TG_Goods')
cur.execute('SELECT COUNT(*) FROM ezc.project')
cur.execute('SELECT COUNT(*) FROM trade.TF_Orders')
```

## 概述

这是 **直采商城（智采商城/行采家）** 系统的日常SQL需求技能。数据库 `xcj_mall_base`（326张表），部分报表涉及 `stddata` 库。**不含 trade 库**。

## 核心业务表

| 表名 | 库 | 说明 |
|------|----|------|
| `TG_Goods` | xcj_mall_base | 商品主表（上架商品）。有 BrandName / model / StockDirName / Units 等字段 |
| `TG_G_ProviderQuote` | xcj_mall_base | 供应商报价表。**实际字段**：Id, ProviderOrgId, GoodsId, MarketId, ProviderGoodsId, GoodsName, **Units**(非GoodsUnit), State, QuotePrice, QuoteTime, CommerceNum, ProviderOrgName, _Limit, LastModifyTime。**无**GoodsBrandName/GoodsModel/GoodsUnit/StockDirName，品牌/规格/目录需LEFT JOIN TG_Goods |
| `TG_G_CommStatistic` | xcj_mall_base | 商品市场统计（市场商品上架信息） |
| `provider_enter` | xcj_mall_base | 供应商入驻表（含联系人、电话，**无地址**） |
| `provider_enter_stockdir` | xcj_mall_base | 供应商目录授权表 |
| `provider_agent_authorization` | xcj_mall_base | 供应商授权代理商表（含 `providerAddress` 地址字段） |
| `order_contract` | xcj_mall_base | 合同表（含 `providerOrgAddress` 供应商地址——**最完整**） |
| `TF_Orders` | trade | 订单主表 |
| `order_contract` | xcj_mall_base | 合同表 |
| `trade_settlement` | xcj_mall_base | 结算/验收表 |
| `plat_market` | xcj_mall_base | 平台市场配置表 |
| `plat_market_stockdir` | xcj_mall_base | 平台市场目录绑定表 |
| `TB_B_StockDir` | trade | 采购目录（递归树） |
| `TB_B_Param` | xcj_mall_base | 目录参数表 |
| `TG_G_Provider` | xcj_mall_base | 供应商商品关联 |
| `base_goods` | xcj_mall_base | 基础商品表（供应链商品） |
| `TG_TempGoods` | xcj_mall_base | 临时商品表（审核中商品） |
| `collect_project` | xcj_mall_base | 直采商城**协议项目**（征集活动），ID手动生成 |
| `collect_shortlist` | xcj_mall_base | 直采商城**入围供应商**（协议供应商），ID自增 |
| `collect_project_goods` | xcj_mall_base | 直采商城**协议商品**，ID手动生成 |
| `collect_project_stock_org` | xcj_mall_base | **协议采购人**（参与采购单位），ID自增，(projectId,stockOrgId)唯一 |

## 协议表 Schema 参考

见 `references/protocol-table-schemas.md` — 详细字段级文档，包含：
- 4张协议表的完整字段、类型、可空性、是否自增
- 插入顺序：collect_project → collect_shortlist → collect_project_goods → collect_project_stock_org
- 关键校验：哪些ID手动生成、哪些自增、唯一约束
- Excel初始化模板字段规则（每字段=一列，中文标题+必填标记）

> ⚠️ **直采商城协议数据 vs 框架协议数据**：
> - 直采商城协议 = `xcj_mall_base` 库的 `collect_project` / `collect_shortlist` / `collect_project_goods` / `collect_project_stock_org`
> - 用户说"直采商城协议项目"指的就是 `collect_project` 表，**不是** `ezc` 库的框架协议项目
> - ezc库的 `project` / `protocol` / `protocol_goods` 是另一套独立的封闭式框架协议系统

## 常用查询分类

### 1. 商品查询类

**查询已上架商品（含市场筛选）**：
```sql
SELECT g.*, pq.QuotePrice, pm.platCode
FROM xcj_mall_base.TG_Goods g
LEFT JOIN xcj_mall_base.TG_G_ProviderQuote pq ON g.Id = pq.GoodsId AND pq.State = 1
LEFT JOIN xcj_mall_base.plat_market pm ON pq.MarketId = pm.marketId
WHERE g.operState = 2 AND g.State = 1
  AND pm.platCode = 'XCJ';  -- 替换平台编码
```

**报价表+供应商联系人地址联合查询（按商品+供应商去重）**：

> 从报价表取商品/供应商信息，配合供应商联系人、联系电话和地址。地址分散存在，优先取 `provider_agent_authorization`，再兜底 `order_contract`。

```sql
SELECT 
    pq.GoodsId AS '商品ID',
    pq.ProviderOrgId AS '供应商ID',
    MAX(pq.GoodsName) AS '商品名称',
    MAX(pq.ProviderOrgName) AS '供应商名称',
    MAX(pe.providerLinkMan) AS '联系人',
    MAX(pe.providerLinkMobile) AS '联系电话',
    MAX(COALESCE(addr.providerAddress, addr2.providerOrgAddress, '')) AS '地址',
    MIN(pq.QuotePrice) AS '报价价格'
FROM xcj_mall_base.TG_G_ProviderQuote pq
LEFT JOIN xcj_mall_base.provider_enter pe 
    ON pq.ProviderOrgId = pe.providerOrgId AND pe.valid = 1
LEFT JOIN xcj_mall_base.provider_agent_authorization addr 
    ON pq.ProviderOrgId = addr.providerOrgId 
    AND addr.providerAddress IS NOT NULL AND addr.providerAddress != '' AND addr.providerAddress != 'asas'
LEFT JOIN (
    SELECT providerOrgId, providerOrgAddress
    FROM xcj_mall_base.order_contract
    WHERE providerOrgAddress IS NOT NULL AND providerOrgAddress != ''
    GROUP BY providerOrgId
) addr2 ON pq.ProviderOrgId = addr2.providerOrgId
WHERE pq.State = 1
GROUP BY pq.GoodsId, pq.ProviderOrgId
ORDER BY pq.GoodsId;
```

> ⚠️ 供应商地址注意事项：
> - `provider_enter` **没有地址字段**，只有 `providerLinkMan`(联系人) 和 `providerLinkMobile`(联系电话)
> - `TB_M_VarProvider` / `temp_VarProvider` 虽然字段齐全(Person,Phone,MobPhone,WorkAddress)但通常**0条数据**
> - 地址优先来源：`provider_agent_authorization.providerAddress`（供应商授权表）
> - 地址兜底来源：`order_contract.providerOrgAddress`（合同表，最完整，~2229条记录）
> - `trade.TF_Orders.ProviderOrgAddress` 也有订单级别的地址数据

**查询供应链商品（goodsSource=3）**：
```sql
SELECT * FROM xcj_mall_base.TG_Goods a
LEFT JOIN xcj_mall_base.base_goods b ON a.baseGoodsId = b.Id
WHERE b.goodsSource = 3;
```

**查询商品+目录完整路径（递归CTE）**：
```sql
WITH RECURSIVE path_tree AS (
    SELECT id, UpId, StockDirName, IsLastStage, State,
           CAST(StockDirName AS CHAR(2000)) AS content
    FROM trade.TB_B_StockDir
    WHERE UpId IS NULL OR UpId = 0
    UNION ALL
    SELECT a.id, a.UpId, a.StockDirName, a.IsLastStage, a.State,
           CONCAT(p.content, '->', a.StockDirName) AS content
    FROM trade.TB_B_StockDir a INNER JOIN path_tree p ON a.UpId = p.id
)
SELECT pt.content AS '目录完整路径', g.GoodsName, g.Price, g.providerOrgName
FROM xcj_mall_base.TG_Goods g
LEFT JOIN path_tree pt ON g.StockDirId = pt.id AND pt.State = 1
WHERE g.operState = 2 AND g.State = 1;
```

### 2. 供应商管理类

**多供应商批量查询（入驻+报价）**：按公司名 LIKE 模糊匹配批量查入驻状态+商品报价+汇总统计。模板在 `D:\平时处理文件\2026年5月\直采商城\供应商入驻及报价查询_20260529.sql`。注意 TG_G_ProviderQuote 无品牌/规格/目录字段，需 LEFT JOIN TG_Goods 取 g.BrandName / g.model / g.StockDirName。

**查询已入驻供应商（行采家 vs 智采商城）**：
```sql
SELECT pm.marketName AS '商城类型', pm.platCode,
       e.providerOrgName, e.providerOrgCode,
       e.providerLinkMan, e.providerLinkMobile,
       COALESCE(e.applyAuditTime, e.createTime) AS '入驻时间'
FROM xcj_mall_base.provider_enter e
INNER JOIN xcj_mall_base.plat_market pm ON pm.platCode = e.occurPlatCode
WHERE e.valid = 1 AND e.state IN (2, 5);
```

### 3. 订单合同类

**查询订单+合同+验收状态**：
```sql
SELECT o.OrdersNo, o.StockOrgName, o.ProviderOrgName,
       o.TotalPrice, o.EndTime, e.ItemNo AS '计划号',
       CASE ts.settlementState WHEN 3 THEN '已验收' WHEN 2 THEN '审核中'
            WHEN 1 THEN '暂存' WHEN 0 THEN '退回' ELSE '无' END AS '验收状态',
       CASE WHEN oc.editState = 2 THEN '已完成' ELSE '未完成' END AS '合同签订状态',
       oc.contractNo
FROM trade.TF_Orders o
LEFT JOIN xcj_mall_base.TF_O_ReqOrgInfo e ON o.Id = e.OrdersId
LEFT JOIN xcj_mall_base.trade_settlement ts ON o.Id = ts.orderId
LEFT JOIN xcj_mall_base.order_contract oc ON o.Id = oc.orderId
WHERE o.State IN (4, 6);
```

**合同作废（订单已作废但合同未同步）**：
```sql
-- 先查范围
SELECT b.id, b.state, a.editState, b.ordersNo
FROM xcj_mall_base.order_contract a
LEFT JOIN trade.TF_Orders b ON a.orderId = b.id
WHERE b.State = -1 AND a.editState != -2;

-- 备份后更新
CREATE TABLE test.order_contract_bak_2026MMDD AS
SELECT a.* FROM xcj_mall_base.order_contract a
LEFT JOIN trade.TF_Orders b ON a.orderId = b.id
WHERE b.State = -1 AND a.editState != -2;
UPDATE xcj_mall_base.order_contract SET editState = -2
WHERE id IN (SELECT contractId FROM test.order_contract_bak_2026MMDD);
```

### 4. 目录授权类

**查询所有非禁用采购目录（含递归路径和参数）**：
```sql
WITH RECURSIVE path_tree AS (
    SELECT id, UpId, StockDirName, IsLastStage, State,
           CAST(StockDirName AS CHAR(2000)) AS content, 1 AS lvl
    FROM trade.TB_B_StockDir WHERE UpId IS NULL OR UpId = 0
    UNION ALL
    SELECT a.id, a.UpId, a.StockDirName, a.IsLastStage, a.State,
           CONCAT(p.content, '->', a.StockDirName) AS content, p.lvl + 1
    FROM trade.TB_B_StockDir a INNER JOIN path_tree p ON a.UpId = p.id
)
SELECT a.id, a.StockDirName, a.content AS '完整路径',
       CONCAT(a.lvl, '级') AS '级别',
       GROUP_CONCAT(DISTINCT b.ParamName ORDER BY b.OrderNo SEPARATOR ',') AS '参数'
FROM path_tree a
LEFT JOIN xcj_mall_base.TB_B_Param b ON a.id = b.StockDirId AND b.State = 1 AND b.IsKey = 1
WHERE a.State = 1 GROUP BY a.id;
```

### 5. 平台数据同步类

**同步供应商+目录授权+代理商+商品+报价到另一个平台**：见历史SQL文件
`/mnt/d/平时处理文件/2026年4月/直采商城/同步一个平台数据到宁外一个平台_cqdj.sql`

### 6. 数据清理/修复类

**品牌去重（通用方案，适合任何品牌字段）**：
核心思想：`TRIM(BrandName)` 去空格去重（⚠️ 不要用 `UPPER(TRIM())` — 大小写不同表示不同品牌），保留最小ID，建映射表驱动所有引用表批量更新。

```sql
-- 1. 建映射表（delete_id → keep_id）
CREATE TABLE test.brand_duplicate_map (
    brand_name VARCHAR(100),
    keep_id    BIGINT,
    delete_id  BIGINT,
    PRIMARY KEY (delete_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO test.brand_duplicate_map (brand_name, keep_id, delete_id)
SELECT t.clean_name, t.keep_id, d.Id AS delete_id
FROM (
    SELECT TRIM(BrandName) AS clean_name, MIN(Id) AS keep_id
    FROM xcj_mall_base.TB_B_Brand
    GROUP BY TRIM(BrandName)
    HAVING COUNT(1) > 1
) t
INNER JOIN xcj_mall_base.TB_B_Brand d
    ON TRIM(d.BrandName) = t.clean_name AND d.Id != t.keep_id;

-- 2. 动态查出所有含品牌字段的表（通用写法）
-- 支持字段名: BrandId / brandId / BrandID / brand_id / goodsRepBrandId
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME
FROM information_schema.COLUMNS
WHERE COLUMN_NAME IN ('BrandId','brandId','BrandID','brand_id','goodsRepBrandId')
  AND TABLE_NAME != 'TB_B_Brand'
  AND TABLE_SCHEMA IN ('xcj_mall_base', 'trade', 'stddata')
ORDER BY COLUMN_NAME, TABLE_NAME;

-- 3. 对每张查到表执行 UPDATE（JOIN 映射表驱动）
UPDATE xcj_mall_base.TG_Goods t
INNER JOIN test.brand_duplicate_map m ON t.BrandId = m.delete_id
SET t.BrandId = m.keep_id;

-- 4. TRIM 保留品牌的首尾空格
UPDATE xcj_mall_base.TB_B_Brand b
INNER JOIN (SELECT DISTINCT keep_id FROM test.brand_duplicate_map) m ON b.Id = m.keep_id
SET b.BrandName = TRIM(b.BrandName);

-- 5. 删除重复行
DELETE b FROM xcj_mall_base.TB_B_Brand b
INNER JOIN test.brand_duplicate_map m ON b.Id = m.delete_id;

-- 6. 验证
SELECT TRIM(BrandName), COUNT(1) FROM xcj_mall_base.TB_B_Brand GROUP BY TRIM(BrandName) HAVING COUNT(1) > 1;
```

> ⚠️ 多个字段名（驼峰/小写）统一用 `IN ('BrandId','brandId','goodsRepBrandId')` 查 information_schema，不要手工拼表列表。
>
> ✅ 已验证的11张关键表：TB_B_StockDirBrand、TB_B_StockDirSeries、TG_G_Provider、TG_Goods、base_goods、TF_CommerceGoods、TG_TempGoods、TF_E_QuoteDetail、spu_goods、collect_shortlist、collect_project_goods
>
> 完整sql见 `references/brand-dedup-template.sql`

**删除重复报价（按GoodsId+ProviderOrgId+MarketId去重）**：
```sql
DROP TABLE IF EXISTS test.TG_G_ProviderQuote_bak_2026MMDD;
CREATE TABLE test.TG_G_ProviderQuote_bak_2026MMDD AS
SELECT pq.* FROM xcj_mall_base.TG_G_ProviderQuote pq
INNER JOIN (SELECT Id FROM (
    SELECT Id, ROW_NUMBER() OVER (PARTITION BY GoodsId, ProviderOrgId, MarketId
        ORDER BY QuoteTime DESC, Id DESC) AS rn
    FROM xcj_mall_base.TG_G_ProviderQuote
) t WHERE t.rn > 1) d ON d.Id = pq.Id;
DELETE pq FROM xcj_mall_base.TG_G_ProviderQuote pq
INNER JOIN test.TG_G_ProviderQuote_bak_2026MMDD b ON b.Id = pq.Id;
```

**主数据去重（品牌/分类等）**：

因导入或录入不规范，主表（如 `TB_B_Brand`）可能出现同名记录（首尾空格导致）。处理流程：

1. 用 `UPPER(TRIM(name)) GROUP BY` 发现重复对
2. 查 `information_schema.COLUMNS` 找所有引用表
3. 确定保留/删除策略（优先保留引用多的）
4. 备份后，CASE WHEN 批量更新引用表的 FK
5. TRIM 清洗保留记录，删除重复行

详细步骤 + TB_B_Brand 结构 + 引用表清单见 `references/master-data-dedup.md`

**删除未入驻供应商的报价数据**：
```sql
SELECT COUNT(1) FROM xcj_mall_base.TG_G_ProviderQuote a
INNER JOIN xcj_mall_base.plat_market m ON a.MarketId = m.marketId
LEFT JOIN xcj_mall_base.provider_enter b ON a.ProviderOrgId = b.providerOrgId AND b.occurPlatCode = m.platCode
WHERE (b.state NOT IN (2, 5) OR b.id IS NULL) AND m.platCode = 'cqct';
```

### 7. 月度工作文件（按月生成）

**脚本路径**：`~/.hermes/skills/dogfood/direct-purchase-sql/scripts/generate_month_file.py`

每月1号9:00定时任务自动运行，在 `/mnt/d/平时处理文件/2026年X月/直采商城/` 下生成带SQL模板的月度工作文件（含商品导出、供应商查询、订单查询、平台同步等模板）。同时也生成 `/框架协议/` 下的对应文件。

**手动执行**：
```bash
python3 ~/.hermes/skills/dogfood/direct-purchase-sql/scripts/generate_month_file.py "2026年5月"
```

文件结构：
- 本月新增SQL需求记录区
- 常用查询模板
- 备份记录表（DML操作前必须先在test库建备份）

## 常用平台编码（platCode）

| 编码 | 说明 | 创建时间 |
|------|------|---------|
| XCJ | 行采家（主平台） | 2025-09 |
| cqsz | 石柱直采商城 | 2025-05 |
| cqck | 城口直采商城 | 2025-07 |
| cqfj | 奉节直采商城 | 2025-08 |
| cqws | 巫山直采商城 | 2025-08 |
| cqxs | 秀山直采商城 | 2025-08 |
| cqyy | 云阳直采商城 | 2025-08 |
| cqps | 彭水直采商城 | 2025-08 |
| cqtn | 潼南直采商城 | 2025-08 |
| cqrc | 荣昌直采商城 | 2025-08 |
| cqfd | 丰都直采商城 | 2025-08 |
| cqzx | 忠县直采商城 | 2025-08 |
| cqqjq | 黔江直采商城 | 2025-09 |
| cqkz | 开州直采商城 | 2025-09 |
| cqgxq | 高新区直采商城 | 2025-10 |
| cqjlp | **九龙坡区直采商城** | **2025-12** |
| cqjj | 江津区直采商城 | 2025-12 |
| cqct | 长寿智采商城（重庆文旅） | 2025-08 |
| cqdj | 垫江智采商城 | 2026-04 |
| cqwx | 巫溪直采商城 | 2026-03 |
| cqyc | 永川/梁平区直采商城 | 2026-03 |
| cqsjlzl.gec123.com | 市级集中采购 | - |
| cqsjlzl.xcjshow1.gm | 梁平区教委 | 2026-01 |
| cqsjlzl.xcjshow1.gm | 重庆质检院 | 2026-04 |

> 查所有平台：`SELECT marketId, platCode, marketName, platName, creaTime FROM xcj_mall_base.plat_market ORDER BY creaTime DESC`

## 中关村回调 API 测试

完整的 show1 环境 ZGC 回调推送测试指南见 `references/zgc-callback-testing.md`，包含：

**性能测试**：`scripts/zgc_perf_test.py` — 可重复执行的压测脚本，支持自定义迭代次数和目录。
```bash
python3 ~/.hermes/skills/dogfood/direct-purchase-sql/scripts/zgc_perf_test.py 20
python3 ~/.hermes/skills/dogfood/direct-purchase-sql/scripts/zgc_perf_test.py 5 显示器
```
基准数据：show1 环境台式计算机 ~1.9s avg（线上 ~8s，差 4 倍）。

参考文档包含：
- OAuth2 token 获取（含 WSL curl 被拦截时的 Python urllib 替代方案）
- 回调 Body 模板
- **目录支持范围**：仅 IT 设备类（计算机/显示器/路由器等），**不支持耗材类**（墨盒/墨粉/办公耗材全部返回 400）
- 已验证可用的图片 URL
- 参数匹配规则（exact match on TB_B_Param.ParamName, state=1 only）
- 平板电脑(857)目录参数陷阱：`计价单位` ≠ `计费单位`
- 三推模拟测试流程及 DB 验证 SQL
- **字段写入行为**：Introduce / detailImageUrl / content 始终 null，只有 images[0]→imagePath 和 params 被处理

## 核查平台交易数据

当需要核查某个新平台（如 cqjlp）的整体交易状况时，按以下顺序系统性地调查：

### 步骤1：确认平台存在
```sql
SELECT marketId, platCode, marketName, platName, creaTime 
FROM xcj_mall_base.plat_market 
WHERE platCode = '目标平台编码';
```
记下 `marketId`（即 MarketId）。

### 步骤2：检查订单数据（trade.TF_Orders）
```sql
-- 按MarketId查询
SELECT State, COUNT(1) AS 订单数, COALESCE(SUM(TotalPrice), 0) AS 金额
FROM trade.TF_Orders WHERE MarketId = 目标marketId
GROUP BY State ORDER BY COUNT(1) DESC;

-- 按OccurPlatCode查询（兼容方案）
SELECT State, COUNT(1) FROM trade.TF_Orders 
WHERE OccurPlatCode = '目标平台编码'
GROUP BY State;
```

### 步骤3：检查合同数据（order_contract）
```sql
SELECT editState, COUNT(1) AS 合同数,
       COUNT(DISTINCT stockOrgName) AS 采购方数,
       COUNT(DISTINCT providerOrgName) AS 供应商数
FROM xcj_mall_base.order_contract 
WHERE marketId = 目标marketId
GROUP BY editState;

-- 查看合同明细
SELECT id, contractNo, stockOrgName, providerOrgName, 
       createTime, editState, contractTime
FROM xcj_mall_base.order_contract 
WHERE marketId = 目标marketId
ORDER BY createTime DESC;
```

### 步骤4：检查结算/验收（trade_settlement）
```sql
SELECT COUNT(1), settlementState 
FROM xcj_mall_base.trade_settlement 
WHERE marketId = 目标marketId
GROUP BY settlementState;
```

### 步骤5：检查供应商入驻（provider_enter）
```sql
SELECT providerOrgName, providerLinkMan, providerLinkMobile, 
       state, createTime
FROM xcj_mall_base.provider_enter 
WHERE occurPlatCode = '目标平台编码' AND valid = 1 AND state IN (2, 5);
```

### 步骤6：检查协议项目（collect_project）
```sql
SELECT projectName, projectNo, createTime, validityStartTime, validityEndTime
FROM xcj_mall_base.collect_project 
WHERE occurPlatCode = '目标平台编码';
```

### 步骤7：汇总结论
综合以上6步的数据，判断该平台的活跃程度：
- ❌ **无数据** = 新平台未运营
- ⏸️ **仅合同草稿** = 试运行/测试阶段（合同editState=0为暂存）
- ✅ **有订单有结算** = 正常运营

## 数据库模式分析 & 字段统一

跨库查找某字段在所有表中的分布、对比实际数据长度与定义长度，生成 ALTER 脚本统一长度。

### 步骤1：查所有含某字段的表（信息收集）

```sql
-- 精确字段名匹配
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, CHARACTER_MAXIMUM_LENGTH,
       IS_NULLABLE, COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'xcj_mall_base'
  AND (COLUMN_NAME LIKE 'goodsName' OR COLUMN_NAME LIKE 'GoodsName' OR COLUMN_NAME LIKE 'goods_name')
ORDER BY TABLE_NAME, COLUMN_NAME;

-- 模糊匹配（如所有含 Brand/品牌 的字段）
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'xcj_mall_base'
  AND COLUMN_NAME IN ('BrandId','brandId','BrandID','brand_id','goodsRepBrandId');
```

### 步骤2：检查实际数据最大长度（判断是否需扩容/缩容）

```sql
-- 单表逐条执行（MCP 不支持 UNION ALL 跨表）
SELECT MAX(LENGTH(GoodsName)) FROM TG_Goods;
SELECT MAX(LENGTH(goodsName)) FROM base_goods;
```

> ⚠️ `LENGTH()` 返回**字节数**，varchar(n) 限制的是**字符数**。UTF-8 下中文每字3字节。示例：若 `MAX(LENGTH)=248`，实际约83个中文字符，`varchar(255)` 完全够用。

### 步骤3：跨库对比（同名表不同库定义可能不一致）

```sql
SELECT a.TABLE_NAME, a.COLUMN_TYPE AS xcj_mall_base,
       b.COLUMN_TYPE AS trade
FROM information_schema.COLUMNS a
INNER JOIN information_schema.COLUMNS b
  ON a.COLUMN_NAME = b.COLUMN_NAME AND a.TABLE_NAME = b.TABLE_NAME
WHERE a.TABLE_SCHEMA = 'xcj_mall_base'
  AND b.TABLE_SCHEMA = 'trade'
  AND a.COLUMN_NAME IN ('GoodsName', 'goodsName')
  AND a.COLUMN_TYPE != b.COLUMN_TYPE;
```

### 步骤4：生成 ALTER 语句

保留字段原有的 NULL/NOT NULL 属性和 COMMENT。字段名大小写必须与原定义一致。

```sql
-- 改其他长度 → 255
ALTER TABLE 表名 MODIFY COLUMN 字段名 varchar(255) DEFAULT NULL COMMENT '商品名称';
-- 已经是255的重新ALTER确认（重置表结构确保线上一致）
ALTER TABLE 表名 MODIFY COLUMN 字段名 varchar(255) DEFAULT NULL COMMENT '商品名称';
```

### 注意事项

1. **ALTER 会锁表**，大表（10万+行）需在业务低峰期执行
2. `varchar(300)` 改 `varchar(255)` 前必须确认实际数据：若 `MAX(LENGTH(x))/3 > 255` 会截断
3. 不同库同名表长度可能不同（如 `TG_Goods.GoodsName`：xcj_mall_base=255，trade=100）
4. 备份表（`*_bak_*`）不需要操作
5. 执行前先确认当前库：`USE xcj_mall_base;`

## 📁 SQL文件保存约定（必须遵守）

用户明确要求：**所有直采商城和框架协议的SQL文件必须保存到月度工作目录下**，不允许保存到 /tmp/ 或其他临时目录。

| 类型 | 路径 |
|------|------|
| 直采商城SQL | `/mnt/d/平时处理文件/2026年X月/直采商城/` |
| 框架协议SQL | `/mnt/d/平时处理文件/2026年X月/框架协议/` |

文件名格式：`描述_YYYYMMDD.sql`（如 `供应商入驻及报价查询_20260529.sql`）

> **⚠️ 常见错误**：Session中写SQL后直接 `write_file` 到 `/tmp/` 会被用户纠正。**必须先确认当月目录**，直接写入对应月文件夹。

## 注意事项

1. **DML操作前必须先备份到 test 库**，SELECT确认影响范围后再执行
2. 平台同步前确保目标平台在 plat_market/plat_market_stockdir 中已配置
3. **跨库注意库前缀**：`xcj_mall_base.TG_Goods` vs `trade.TB_B_StockDir` vs `trade.TF_Orders`
4. 递归CTE（目录树）需MySQL 8.0+
5. 临时商品表 TG_TempGoods 的 operState 要跟 ezc.protocol_goods 对应确认后再修复
6. `trade.TF_Orders` 和 `xcj_mall_base.order_contract` 是两个库的表，关联查询时注意库前缀
7. **⚠️ `order_contract.orderId` 可能不存在于 `trade.TF_Orders`**：有些合同记录的 orderId 在 TF_Orders 表中查不到（已删除或来自独立测试数据）。如果 `LEFT JOIN` 后全是 NULL，说明订单数据已丢失或从未正式创建交易流水，合同可能仅是草稿（editState=0）。
8. **合同 editState 状态码**：`-1`=退回, `0`=暂存(草稿,未正式签订), `1`=审核中, `2`=已完成
9. **订单 State 状态码**：`-1`=已作废, `1`=暂存, `2`=待编辑合同, `3`=待确认合同, `4`=待打印, `5`=作废, `6`=正常完成, `7`=解除合同, `9`=待厂家确认, `10`=放弃(顺序轮候), `11`=待审核, `12`=审核退回
10. WSL直连查库用 pymysql，不要用 `os.system('mysql ...')`，因为 `mysql` CLI 未安装
