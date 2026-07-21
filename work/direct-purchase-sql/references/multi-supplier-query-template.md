# 多供应商入驻+商品报价联合查询模板

## 场景
需要查询指定多个供应商在某平台上的入驻状态和商品报价情况。

## 核心思路
1. **入驻**：`provider_enter` 表，通过 `providerOrgName LIKE` 模糊匹配
2. **报价**：`TG_G_ProviderQuote` 表，通过 `ProviderOrgName LIKE` 模糊匹配
3. **平台过滤**：`occurPlatCode`（入驻表）或 `plat_market.platCode`（报价表）

## SQL 模板

### 第一部分：入驻情况

```sql
SELECT
    e.providerOrgName          AS '供应商名称',
    e.providerOrgCode          AS '统一社会信用代码',
    e.providerLinkMan          AS '联系人',
    e.providerLinkMobile       AS '联系电话',
    CASE e.state
        WHEN 2 THEN '已入驻'
        WHEN 5 THEN '入驻(已完善)'
        WHEN 1 THEN '待审核'
        WHEN 0 THEN '草稿'
        WHEN -1 THEN '退回'
        ELSE CONCAT('未知(', e.state, ')')
    END                        AS '入驻状态',
    e.applyAuditTime           AS '审核通过时间',
    e.createTime               AS '创建时间',
    m.platCode                 AS '平台编码',
    m.marketName               AS '商城名称'
FROM xcj_mall_base.provider_enter e
LEFT JOIN xcj_mall_base.plat_market m ON m.platCode = e.occurPlatCode
WHERE e.valid = 1
  AND e.occurPlatCode = '目标平台编码'
  AND (
         e.providerOrgName LIKE '%公司A%'
      OR e.providerOrgName LIKE '%公司B%'
      OR e.providerOrgName LIKE '%公司C%'
  )
ORDER BY e.providerOrgName;
```

### 第二部分：商品报价情况

```sql
SELECT
    q.ProviderOrgName          AS '供应商名称',
    q.GoodsId                  AS '商品ID',
    q.GoodsName                AS '商品名称',
    q.GoodsBrandName           AS '品牌',
    q.GoodsModel               AS '规格型号',
    q.GoodsUnit                AS '单位',
    q.QuotePrice               AS '报价(元)',
    q.QuoteTime                AS '报价时间',
    q.StockDirName             AS '所属目录',
    q.State                    AS '报价状态',
    CASE q.State
        WHEN 1 THEN '有效'
        WHEN 0 THEN '无效'
    END                        AS '报价状态说明',
    m.platCode                 AS '平台编码'
FROM xcj_mall_base.TG_G_ProviderQuote q
LEFT JOIN xcj_mall_base.plat_market m ON m.marketId = q.MarketId
WHERE m.platCode = '目标平台编码'
  AND q.State = 1
  AND (
         q.ProviderOrgName LIKE '%公司A%'
      OR q.ProviderOrgName LIKE '%公司B%'
      OR q.ProviderOrgName LIKE '%公司C%'
  )
ORDER BY q.ProviderOrgName, q.GoodsId;
```

### 第三部分：入驻汇总统计

```sql
SELECT
    CASE WHEN e.id IS NOT NULL THEN '已入驻' ELSE '未入驻' END AS '状态',
    COUNT(1) AS '供应商数'
FROM (
    SELECT '公司A全称' AS name
    UNION SELECT '公司B全称'
    UNION SELECT '公司C全称'
) s
LEFT JOIN xcj_mall_base.provider_enter e
    ON e.providerOrgName LIKE CONCAT('%', REPLACE(REPLACE(s.name, '（', '('), '）', ')'), '%')
   AND e.valid = 1
   AND e.occurPlatCode = '目标平台编码'
GROUP BY CASE WHEN e.id IS NOT NULL THEN '已入驻' ELSE '未入驻' END;
```

## 注意点

1. **全半角括号**：公司名中的中文括号 `（）` 和英文括号 `()` 需兼容。`LIKE` 模式直接写不带括号的关键词即可（如 `'%曼哈格%'` 能匹配 `曼哈格（上海）生物科技有限公司`）
2. **平台编码**：用变量形式的 `@platCode` 在 Navicat 中需先 `SET @platCode = 'xxx'`，或者直接替换为字面量
3. **test环境数据**：show1 环境（192.168.2.37:31004）的 provider_enter 数据为**打乱过的测试数据**，真实公司名不会匹配
