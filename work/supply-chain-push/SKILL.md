---
name: supply-chain-push
description: 直采商城供应链商品推送——批量推送商品、查询目录、修改商品/价格、查询审核结果，含OAuth2认证流程。
version: 1.0.0
author: Hermes + 许俊
license: MIT
metadata:
  hermes:
    tags: [supply-chain, 直采商城, 供应商, 商品推送]
---

# 供应链商品推送

向直采商城平台批量推送供应商商品，支持商品信息修改、价格变更、审核结果查询。

## 触发条件

- 用户说"推送供应链商品"、"供应链推送"、"测试供应链接口"
- 用户提供商品数据要推送到直采商城
- 用户询问供应链对接相关的问题

## 一、环境地址

| 前缀 | 环境 | 地址 |
|------|------|------|
| op_base_url | test3 内部 | https://www.djctest3.gm/djc-gateway/authing |
| op_base_url | test3 外部 | https://test3.gec123.com/djc-gateway/authing |
| op_base_url | show1 | `https://www.xcjshow1.gm/djc-gateway/authing` 或 `https://www.djcshow1.gm/djc-gateway/authing` ⚠️ 待确认 |
| op_base_url | 正式 | https://www.djc123.com/djc-gateway/authing |
| mall_base_url | test3 内部 | https://www.xcjtest3.gm/xcj-gateway/api/v2/xcjmallbase |
| mall_base_url | test3 外部 | https://test3.gec123.com/djc-gateway/djctradetool |
| mall_base_url | show1 | https://www.xcjshow1.gm/xcj-gateway/api/v2/xcjmallbase ✅ 已验证连通 |
| mall_base_url | 正式 | https://www.gec123.com/xcj-gateway/xcjmallbase |

> **注意**：mall_base_url 必须包含 `/api/v2/`，否则后端路由不到。
> **⚠️ 凭据隔离**：`zcsc_nsdys / 123456` 仅用于 test3。show1 和正式环境需要独立的 client_id + client_secret。

## 二、认证信息

向平台申请获取：client_id + client_secret。

**推送前先用 session_search 搜索 "供应链 client_id" 查找历史认证信息。找不到必须向用户询问，绝不猜测。**

## 三、三步推送流程

### 步骤1：获取Token (OAuth2 Client Credentials)

```bash
TOKEN=$(curl -s -X POST "${OP_BASE_URL}/oauth/token" \
  -H "Authorization: Basic $(printf '%s:%s' "$CLIENT_ID" "$CLIENT_SECRET" | base64)" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

有效期约2小时，过期需重新获取。

### 步骤2：推送商品

```
POST ${MALL_BASE_URL}/v1/public/supply-chain/goods/push
Authorization: Bearer ${TOKEN}
Content-Type: application/json
```

### 步骤3：解读响应

响应结构：
```json
{"code": 200, "message": "请求成功", "data": {...}}
```
- `data.total`：推送总数
- `data.accept`：成功入库数
- `data.illegal`：校验未通过数
- `data.illegalDetails`：失败明细 [{skuId, reason}]

## 四、请求体字段（applyList[] 每个元素）

**必填字段：**
- skuId / spuId — String(100)，供应商侧唯一标识
- goodsName — String(255)
- stockDirId — Long，商品目录ID（从目录接口获取）
- brandName / model / units — String
- price — Decimal，>0，保留2位
- chargeUnit — String(100)
- imagePath — String(200)，公网可访问主图URL
- images — Array[String]，最少3张最多9张
- introduce — String，支持HTML
- stockDirName — String(200)，目录名称

**可选字段：**
seriesName(100), inventoryQuantity, barCode(100), inMarketTime(YYYY-MM-DD), stopProductionTime(YYYY-MM-DD), ifXcProduct(0/1), providerOrgName(200), specialNote(100), remark(200)

**params数组（必填，须包含目录关键参数）：**
```json
[{"paramCode": "CPU", "paramName": "CPU", "paramValue": "i7-1365U", "ifSpuParam": 0}]
```

## 五、Controller验证规则

来自 `SupplyChainApplyController.applyGoods()`：

1. 单次最多500个商品 → 超过返回400
2. 同批次skuId不能重复 → 重复返回400
3. `clientPrincipal.getName()` 不能为null → 否则403"未完善供应商信息"
4. 必须有对应供应商记录 → 否则403"未分配权限"
5. Spring Validation验证字段约束 → 失败商品计入illegalDetails
6. 通过验证的商品进入数据库判重（已存在skuId会失败）
7. **部分成功模式**：成功的已入库，失败的需修正后重推

## 六、其他接口

### 修改商品信息
```
POST ${MALL_BASE_URL}/v1/public/supply-chain/goods/edit
```
必填：skuId, goodsName, brandName, model, units, chargeUnit, imagePath, images, introduce

### 修改价格
```
POST ${MALL_BASE_URL}/v1/public/supply-chain/goods/price/edit
```
必填：skuId, price

### 查询审核结果
```
GET ${MALL_BASE_URL}/v1/public/supply-chain/goods/goods/audit-result/query?skuIdList=SKU1,SKU2&pageNum=1&pageSize=20
```
auditState：-1审核中 / 0不通过 / 1通过

## 七、错误码

| code | 含义 |
|------|------|
| 200 | 成功 |
| 3 | 无法解析参数 |
| 4 | 无权限(token过期/无效) |
| 400 | 请求参数错误/已知业务错误 |
| 500 | 服务器异常 |

## 八、频率限制

- 获取token：10次/分钟
- 商品推送：10次/分钟（每次≤500个）
- 修改商品：20次/分钟
- 修改价格：30次/分钟
- 查询审核：100次/分钟

## 九、执行示例

```python
import requests, base64, json

CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
ENV = "test_internal"  # test_internal / test_external / prod

ENV_MAP = {
    "test_internal": ("https://www.djctest3.gm/djc-gateway/authing",
                       "https://www.xcjtest3.gm/xcj-gateway/api/v2/xcjmallbase"),
    "test_external": ("https://test3.gec123.com/djc-gateway/authing",
                      "https://test3.gec123.com/djc-gateway/djctradetool"),
    "prod": ("https://www.djc123.com/djc-gateway/authing",
             "https://www.gec123.com/xcj-gateway/xcjmallbase"),
}
OP_BASE, MALL_BASE = ENV_MAP[ENV]

# 获取token
auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
r = requests.post(f"{OP_BASE}/oauth/token",
    headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"},
    data={"grant_type": "client_credentials"})
TOKEN = r.json()["access_token"]

# 推送商品
GOODS = [{
    "skuId": "TEST-001", "spuId": "TEST-001",
    "goodsName": "测试商品", "stockDirId": 10002,
    "brandName": "测试品牌", "model": "M1",
    "units": "台", "price": 999.00, "chargeUnit": "元",
    "imagePath": "https://example.com/img/main.jpg",
    "images": ["https://example.com/img/1.jpg",
               "https://example.com/img/2.jpg",
               "https://example.com/img/3.jpg"],
    "introduce": "<p>测试商品介绍</p>",
    "stockDirName": "电脑",
    "params": [{"paramCode": "CPU", "paramName": "CPU", "paramValue": "i7"}]
}]

r = requests.post(f"{MALL_BASE}/v1/public/supply-chain/goods/push",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={"applyList": GOODS})

result = r.json()
print(f"total={result['data']['total']} accept={result['data']['accept']} illegal={result['data']['illegal']}")
for d in result['data'].get('illegalDetails', []):
    print(f"  FAIL: {d['skuId']} - {d['reason']}")
```

## 十、目录参数踩坑记录

### 复印纸（stockDirId=130117571742531750）

关键参数（缺一不可）：
- 品牌（BRAND）
- 型号（MODEL）
- 规格（SPEC）
- 包装数量（PACK_QTY）— 有枚举值校验，如 "500张/包"
- 单位重量（UNIT_WEIGHT）— **仅有 "70g" 通过**，"80g"、"70g/㎡" 等均不在允许列表中
- 颜色（COLOR）— "白色"
- 纸张类型（PAPER_TYPE）— "复印纸"

### 数据库对应关系

| 环境 | DB host | 库名 | connection_id |
|------|---------|------|:---:|
| test3 | 192.168.2.2 | xcj_mall_base | test3 |
| show1/默认 | 192.168.2.37 | xcj_mall_base | default |

| 表 | 用途 |
|----|------|
| sc_product_sku | 商品主表（推送成功即入库） |
| sc_product_sku_audit_record | 审核记录（audit_state: 0=不通过, 1=通过；无记录=审核中） |

## 十一、代码参考

- Controller: `com.xcj.mallbase.controller.outer.supplychain.SupplyChainApplyController`
- API文档: D:\项目\svn\P2040直采与框架协议\版本管理\直采商城(新）\历史\25年\1.3.5 供应链接口对接\直采商城供应商商品对接接口文档V1.0-202510231024.md
