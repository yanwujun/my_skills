# 直采商城测试环境配置

> Absorbed from `direct-purchase-env-test` skill. Covers test environment URLs, authentication,
> agent-browser login, API call patterns, ZGC callback OAuth2, and full API reference for show1/test3.

## Environment Info

| Item | Value |
|------|-------|
| Frontend URL | https://zc-mall.xcjshow1.gm |
| API Gateway | https://www.xcjshow1.gm/xcj-gateway |
| API format | `{gateway}/api/v2/{serviceName}/{path}?__platDomain__=zc-mall.xcjshow1.gm` |
| Service names | xcjmallbase (goods), xcjmalltrade (trade), xcjezc (framework) |
| Login | https://www.xcjshow1.gm/login-app/login?back={return_url} |
| Swagger (local dev) | http://127.0.0.1:25325/xcjmallbase/doc.html |
| MySQL show1 | 192.168.2.37:31004 |
| MySQL test3 | 192.168.2.2:31004 |

## Auth Methods

### User Cookie (Browser)
```
Cookie: Auth=<token_from_browser>
```
Get from browser DevTools → Network → any request's Cookie header.

### ZGC Callback OAuth2
```bash
# Get token
POST https://www.xcjshow1.gm/djc-gateway/authing/oauth/token
Authorization: Basic $(echo -n 'zcsc_zdzs:123456' | base64)
Content-Type: application/x-www-form-urlencoded
Body: grant_type=client_credentials

# Call with token
POST {gateway}/api/v2/xcjmallbase/v1/public/zdzs/callback/product-audit-result?__platDomain__=zc-mall.xcjshow1.gm
Authorization: Bearer {access_token}
```

## Supplier Login (agent-browser)

Credentials: `ssss` / `GmsoftTest_1997` / captcha `111111`

```bash
agent-browser --config <config> open "https://www.xcjshow1.gm/login-app/login?back=https%3A%2F%2Fzc-mall.xcjshow1.gm"
sleep 3 && agent-browser snapshot -i
agent-browser type @e9 "ssss"
agent-browser type @e10 "GmsoftTest_1997"
agent-browser click @e5
sleep 3
agent-browser eval 'document.cookie'
```

## Platform Login (multi-step)

```bash
agent-browser type @e9 "admin"
agent-browser type @e10 "GmsoftTest_1997"
agent-browser click @e5          # step 1: password
sleep 2 && agent-browser snapshot -i
agent-browser click @e7          # step 2: select identity
sleep 2 && agent-browser snapshot -i
agent-browser type @e15 "111111" # step 3: captcha
agent-browser click @e9
sleep 3
agent-browser eval 'document.cookie'
```

> **admin cookie limitation**: Frontend login cookie lacks `ANY_PLATORG` platform role.
> `goods-manage/*`, `zgc/supplement` APIs require admin-app SSO auth (user manually).

## ZGC Callback API

```http
POST {gateway}/api/v2/xcjmallbase/v1/public/zdzs/callback/product-audit-result?__platDomain__=zc-mall.xcjshow1.gm
```

### Required fields
`goodsNo`, `zdSpu`, `state`, `goodsName`, `model`, `unit`, `brandName`, `categoryName`,
`stockDirName`, **`exPrice`** (NOT `price`), `gtin`, `gtinImgUrl`, `images[]`, `params`

### State Machine
| state | Behavior | completeness |
|:-----:|----------|:-----------:|
| 2 | Create/update base_goods, write matching params | 0 (partial) / 1 (full) |
| 1 | Needs existing TG_Goods association, not testable | — |

### Re-push behavior
- Same zdSpu → original row updated, **no fork**
- Complete all key params → completeness: 0→1 (auto), goodsCode recalculated
- Already bound + re-push → old row state: 1→0, new row created (fork)
- Fork keeps `baseGoodsId` on TG_Goods unchanged (manual re-binding after audit)
- **3-push simulation**: Push same zdSpu 3 times with increasing params — 1st creates record, 2nd updates with more params, 3rd completes all params. goodsName shows last push's value. completeness stays 0 (callback state=2 sets it). Useful for testing completeness transition and param matching.

### Known bug: Duplicate param "类型" under StockDirId=858
Two TB_B_Param rows with ParamName='类型'. Causes `IllegalStateException` on push.
**Avoid dir 858 for testing, or clean duplicates first.**

### Directory support limitation (2026-07-02 verified)
回调 stockDirName 匹配逻辑仅支持 **IT 设备类**目录（台式计算机、便携式计算机、显示器、路由器、鼠标、键盘等），**不支持办公耗材类**（墨盒、墨粉、办公耗材等全部返回 400 "目录不存在"）。TB_B_StockDir 中有记录不代表回调可匹配。详情见 direct-purchase-sql 技能的 `references/zgc-callback-testing.md`。

### Param name exact match
TB_B_Param matching is exact string comparison. One character off = no match. Watch for:
- `计价单位` ≠ `计费单位` (common typo)
- `内存容量` ≠ `内存` (be specific, check actual TB_B_Param names)
Always query `SELECT ParamName, IsKey, State FROM TB_B_Param WHERE StockDirId=?` before constructing params.

### Image transfer from external URLs
When pushing images from external CDNs (e.g. oss.zgcindex.com):
- System auto-downloads images to FastDFS
- `base_goods.imagePath` gets populated with internal path (`group1/M00/...`)
- Push duration signals success: ~12s (downloading) vs ~2-3s (no download)
- The `Introduce` field is NOT writable via callback — use `images[]` array instead
- `goodsDetailHtml` is not a recognized callback field
- If image download fails → HTTP 400 "图片下载失败"

## API Matrix

| API | Path | Auth |
|-----|------|:----:|
| ZGC callback | `zdzs/callback/product-audit-result` | ZGC OAuth2 |
| Supplier template list | `base-goodss/query_base_goods_provider` | Supplier cookie |
| Supplier edit goods | `edit-goods/modify/*` | Supplier cookie |
| Platform audit | `goods-manage/modifyAuditPass` | Platform cookie |
| Ops supplement | `base-goodss/zgc/supplement` | Platform cookie (ANY_PLATORG) |
| Platform manage | `goods-manage/*` | Platform cookie |

## Audit API Summary

| API | Function | State: before → after |
|-----|----------|:---------------------:|
| `modifyAuditPass/{goodsId}` | Approve modify | OperState:3→2, editState:1→2 |
| `completeAuditPass/{goodsId}` | Approve entry | OperState:1→2, editState:1→2 |
| `completeAuditCancel/{goodsId}` | Reject entry |  |
| `modifyAuditCancel/{goodsId}` | Reject modify |  |

## State Machine

| OperState | Meaning | editState(pending) | editState(rejected) | editState(done) |
|-----------|---------|:------------------:|:-------------------:|:---------------:|
| 1 | Entry audit | 1 | -1 | 2 |
| 2 | Active | — | — | 2 |
| 3 | Modify audit | 1 | -1 | 2 |

## Test Report Template

```markdown
# show1 Test Report

## Environment
- App: xcj-mallbase
- Gateway: https://www.xcjshow1.gm/xcj-gateway/api/v2/xcjmallbase
- DB connection_id: {connection}

## Results
| Flow | Case | Result | Evidence |
|------|------|:------:|----------|

## Detail
### Flow1 PM-01~PM-03
- Operation:
- API/Page result:
- DB result:
- Conclusion:
```

## Test Sample IDs

| Object | ID |
|--------|----|
| ZGC base_goods (COMPLETE) | 2016790028591566850, 2016803760005812226 |
| ZGC base_goods (PARTIAL) | 1635986520370503680 |
| ZGC base_goods (forked) | 1635997194505060352 |
| TG_Goods bound to ZGC | 1592958749528735745 |
| TG_Goods forked verified | 1592972113822773249 |

## Verification Status (as of 2026-05)

| Test | Result |
|------|:------:|
| DDL columns exist (4 new fields) | ✅ |
| Supplier API auth (cookie) | ✅ |
| Platform API auth (cookie) | ✅ |
| ZGC callback OAuth2 | ✅ |
| Block modify key param values | ✅ 400 rejected |
| Callback create PARTIAL | ✅ completeness=0 |
| Re-push to complete | ✅ auto 0→1 |
| Callback trigger fork | ✅ old deactivated, new created, no auto rebind |
| completeAuditPass flow | ✅ OperState:1→2, editState:1→2 |
| agent-browser login | ✅ |
| admin-app backend access | ❌ cross-domain SSO unsupported |
