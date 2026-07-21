# ZGC 模板分叉手工走查验证结果

> 测试日期：2026-05-28
> 环境：远程测试环境 https://zc-mall.xcjshow1.gm（API 网关 www.xcjshow1.gm/xcj-gateway）
> 认证：供应商 cookie + 平台 cookie + OAuth2 token（中电指数回调）

---

## 流程 2：禁止修改已有模板参数值 ✅ PASS

**测试商品**：TG_Goods.id=1592958749528735745（HP 平板电脑）
**绑定模板**：base_goods.id=2016790028591566850（goodsSource=1, completeness=1, COMPLETE）

| 操作 | 结果 |
|------|------|
| 将 CPU型号 从"8核高速处理器"改为"9核高速处理器-TEST-FLOW2" 提交 | HTTP 400 |
| 错误消息 | `"不允许修改关键参数「CPU型号」的参数值"` |
| DB: baseGoodsId 不变 | ✅ 仍为 2016790028591566850 |
| DB: 无新分叉行 | ✅ 无 |

---

## 流程 3：中关村回调 — 未绑定 PARTIAL 补全 ⚠️ PARTIAL

**步骤 1（初始化 state=2，部分参数）**：

```bash
curl -sk -X POST ".../xcjmallbase/v1/public/zdzs/callback/product-audit-result?__platDomain__=zc-mall.xcjshow1.gm" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"goodsNo":"TEST-CB01-001","state":"2","zdSpu":"ZDSPU-TEST-FLOW3-001","goodsName":"测试商品回调","brandName":"测试品牌","stockDirName":"平板电脑","params":"{\"规格\":\"A4\",\"颜色\":\"蓝\"}","gtin":"1234567890123","gtinImgUrl":"https://...","model":"测试型号","chargeUnit":"元","unit":"台","images":["https://..."],"exPrice":100.00}'
```

| 预期 | 实际 | 结果 |
|------|------|------|
| 新建 state=1 | state=1 | ✅ |
| completeness=0（部分参数） | completeness=0 | ✅ |
| goodsSource=1（ZGC） | goodsSource=1 | ✅ |
| sku_version=1 | sku_version=1 | ✅ |

**步骤 2（同 zdSpu 再推补全参数）**：

| 预期 | 实际 | 结果 |
|------|------|------|
| 原 base_goods id 不变 | id 不变 | ✅ |
| completeness=1 | completeness 仍为 0 | ⚠️ 未自动更新 |
| 参数行补全 | 仅 3 条参数字段，未新增 | ⚠️ |

> **结论**：回调 API 创建 PARTIAL 模板功能正常，但 completeness 不会因 callback 的 `params` JSON 补全而自动变为 1。完备度计算可能由其他机制触发（如供应商在页面上补齐参数后提交）。

---

## 流程 5：中关村模板列表字段 ✅ PASS

API: `query_base_goods_provider?stockDirId=857`

返回每条均含：
- `completeness`：0=PARTIAL, 1=COMPLETE
- `skuVersion`：1（初始）/ 2+（分叉后）
- `parentBaseGoodsId`：分叉来源，null 表示无分叉
- `isLatestVersion`：0=非最新, 1=最新

---

## 测试环境关键信息

| 项目 | 值 |
|------|-----|
| API 网关 | `https://www.xcjshow1.gm/xcj-gateway` |
| 路径格式 | `/api/v2/{service}/{path}?__platDomain__=zc-mall.xcjshow1.gm` |
| Web 认证 | Cookie: `Auth=<value>` |
| 中电回调认证 | OAuth2 client_credentials → Bearer token |
| 供应商账号 | ProviderOrgId=21（重庆教14扇有限责任公司） |
| 平台运营账号 | 可访问所有管理端接口 |
