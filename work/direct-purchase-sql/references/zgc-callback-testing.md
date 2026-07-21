# 中关村回调 API 测试（show1 环境）

## API 端点

```
POST https://www.xcjshow1.gm/xcj-gateway/api/v2/xcjmallbase/v1/public/zdzs/callback/product-audit-result
     ?__platDomain__=zc-mall.xcjshow1.gm
```

## Token 获取（OAuth2）

```
POST https://www.xcjshow1.gm/djc-gateway/authing/oauth/token
Authorization: Basic base64(zcsc_zdzs:123456)
Content-Type: application/x-www-form-urlencoded
Body: grant_type=client_credentials
```

Token 有效期短，每次测试前重新获取。WSL 中 curl 可能被安全策略拦截，改用 Python urllib：

```python
import urllib.request, base64, ssl, json

auth = base64.b64encode(b"zcsc_zdzs:123456").decode()
req = urllib.request.Request(token_url, method="POST")
req.add_header("Authorization", f"Basic {auth}")
req.add_header("Content-Type", "application/x-www-form-urlencoded")
ctx = ssl._create_unverified_context()
resp = urllib.request.urlopen(req, data=b"grant_type=client_credentials", context=ctx)
token = json.loads(resp.read())["access_token"]
```

## 回调 Body 结构

必填字段：
```json
{
  "zdSpu": "唯一标识",
  "goodsNo": "151||zdSpu值",
  "state": 2,
  "goodsName": "商品名称",
  "brandName": "品牌",
  "stockDirName": "采购目录名",
  "model": "型号",
  "unit": "台",
  "exPrice": 2999.00,
  "gtin": "GTIN码",
  "gtinImgUrl": "图片URL",
  "images": ["图片URL数组"],
  "params": "JSON字符串，如 {\"参数名\":\"参数值\"}"
}
```

## 已验证可用的图片 URL

```
✅ https://www.xcjshow1.gm/group1/M00/30/A2/OBS_161b52a5ce823000.png
❌ https://www.xcjshow1.gm/group1/M00/99/12/OBS_16b431782b02e000.png → HTTP 400 "图片下载失败"
```

## 参数匹配规则

1. 回调只存 params 中 **参数名精确匹配** `TB_B_Param.ParamName` 且 `State=1` 的参数
2. `IsKey=1, State=0` 的参数（如平板电脑的规格/产地/颜色/材质等）不会被存储
3. completeness 字段始终为 0，回调不计算完备度

### 平板电脑(857)目录参数陷阱

目录中 `State=1, IsKey=1` 的 7 个参数：
- CPU型号、操作系统、**计价单位**、存储容量、屏幕分辨率 (ppi)、存储容量 (GB)、销售规格

⚠️ **常见笔误**：`计价单位` ≠ `计费单位`（差一个字），写错导致参数不入库。

## 三推模拟（经典测试场景）

同 zdSpu 推 3 次，观察参数逐步补齐的过程：

| 推送 | params | 预期 |
|:----:|--------|------|
| 1 | 2个无关参数（如规格、颜色，均为 state=0） | base_goods 创建，0 条参数入库 |
| 2 | 4个关键参数（CPU、OS、存储、销售规格） | 4 条参数入库 |
| 3 | 全部7个关键参数 | 6~7 条参数入库（取决于拼写） |

每次推送更新同一条 base_goods 记录（相同 zdSpu），不会创建新行。

## 已验证可用的目录名（stockDirName）

回调接口用 stockDirName 字符串匹配，非 ID 匹配。**匹配逻辑在回调服务（xcjmallbase）内部实现，与 TB_B_StockDir 表不完全一致。**

### 已验证的目录

| 目录名 | 状态 | 备注 |
|--------|:----:|------|
| 台式计算机 | ✅ | 稳定，推荐用于性能测试 |
| 便携式计算机 | ✅ | |
| 显示器 | ✅ | 2026-07-02 再次验证通过 |
| 路由器 | ✅ | |
| 平板式微型计算机 | ❌ | TB_B_StockDir 有记录但回调拒绝。实际回调内部映射为「平板电脑」（base_goods 中 28 条记录用此名） |
| 工作站计算机 | ❌ | TB_B_StockDir 不存在 |
| 色带 | ❌ | TB_B_StockDir 不存在 |

### ❌ 耗材类目录（全部不支持）

**结论：回调接口完全不支持耗材类（办公耗材及其子目录）。** 2026-07-02 对墨盒商品的完整测试：

| 目录名 | TB_B_StockDir | 回调结果 | 备注 |
|--------|:------------:|:--------:|------|
| 墨盒 | 3条，IsLastStage=1 | ❌ "目录[墨盒]不存在" | 位于 办公耗材 → 墨盒 路径下 |
| 墨盒/墨水 | 2条，IsLastStage=1 | ❌ "目录[墨盒/墨水]不存在" | |
| 墨盒组件 | 1条，IsLastStage=1 | ❌ "目录[墨盒组件]不存在" | |
| 复印机、多功能一体机墨盒 | 1条，IsLastStage=1 | ❌ | |
| 办公耗材 | 墨盒的父目录 | ❌ "目录[办公耗材]不存在，无法创建商品" | 父目录也不行 |

> ⚠️ **规律**：回调接口支持 IT 设备类目录（计算机、显示器、路由器、鼠标、键盘等），不支持办公耗材类（墨盒、墨粉、办公耗材等）。从 `base_goods` 历史数据验证：已成功推送的目录全是设备类，没有任何耗材类记录。这是回调服务端代码的限制，需要后端开发在目录匹配逻辑中加白名单或修复匹配规则。

## 性能基准（show1 环境）

2026-07-01 测试，10次推送台式计算机（3参数），结果：

| 指标 | 时间 |
|:-----|:----:|
| Min | 1.37s |
| Max | 2.99s |
| Avg | **1.90s** |
| Median | 1.78s |

参数数量基本不影响耗时（3参数 vs 31参数都在 1.7-2.8s 范围）。show1 测试环境比线上（~8s）快约 4 倍，线上慢的主要原因可能是 ZGC 外部 CDN 图片下载转存。

性能测试脚本：`scripts/zgc_perf_test.py`

## 回调字段写入行为（重要）

`/callback/product-audit-result` 接口**不是完整商品数据同步接口**，只处理以下字段：

| 字段 | 写入？ | 说明 |
|------|:------:|------|
| `images[0]` → `imagePath` | ✅ | 第1张外部URL下载转存到FastDFS，路径如 `group1/M00/F3/16/OBS_...jpg` |
| `params` → `base_goods_param_value` | ✅ | 仅精确匹配 `TB_B_Param.ParamName` 且 `State=1` 的参数入库 |
| `goodsName`, `model`, `brandName`, `exPrice` 等基本字段 | ✅ | 写入 `base_goods` 表 |
| `Introduce` | ❌ | **始终 null**，无论传HTML还是分号分隔URL都不写入 |
| `detailImageUrl` | ❌ | **始终 null**，接口不处理此字段 |
| `content` | ❌ | **始终 null** |
| `images[1:]`（第2张及以后） | ❌ | `images` 数组只有第1张被转存为 `imagePath` |
| `completeness` | ❌ | 始终为 0，回调不计算完备度 |

> ⚠️ 如果商品详情图片（Introduce 中的 img）需要转存，需走其他接口，`/callback/product-audit-result` 做不到。

## 数据库验证

```sql
-- 查 base_goods（注意 Introduce/content/detailImageUrl 始终为 null）
SELECT Id, goodsName, imagePath, Introduce, content, completeness, zdzSkuId
FROM xcj_mall_base.base_goods WHERE zdzSkuId = '目标zdSpu';

-- 查参数
SELECT ParamName, ParamValue, IsKey, ParamNo
FROM xcj_mall_base.base_goods_param_value
WHERE baseGoodsId = 目标ID ORDER BY ParamNo;

-- 查目录定义的所有参数
SELECT ParamName, IsKey, State FROM xcj_mall_base.TB_B_Param WHERE StockDirId = 目录ID;
```
