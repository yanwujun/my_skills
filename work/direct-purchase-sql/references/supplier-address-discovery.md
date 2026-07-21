# 供应商地址字段发现记录

> 查询时间：2026-05-12
> 场景：从报价表取供应商联系人+电话+地址

## 表结构检查结果

### provider_enter（供应商入驻表）— 870条已入驻
有联系人(869/870)和手机(744/870)，但**无地址字段**。

| 字段 | 类型 | 备注 |
|------|------|------|
| providerOrgId | bigint | 供应商标识 |
| providerOrgName | varchar | 供应商名称 |
| providerOrgCode | varchar | 社会信用代码 |
| providerLinkMan | varchar | 联系人 ✅ |
| providerLinkMobile | varchar | 联系电话 ✅ |
| state | tinyint | 状态(2=已入驻, 5=已入驻保证金已缴) |

### TG_G_ProviderQuote（报价表）— 主表，有报价的供应商506家
| 字段 | 说明 |
|------|------|
| GoodsId | 商品ID |
| ProviderOrgId | 供应商ID |
| GoodsName | 商品名称 |
| QuotePrice | 报价价格 |
| State | 状态(1=有效) |
| ProviderOrgName | 供应商名称（冗余字段） |

### 供应商地址来源

1. **provider_agent_authorization.providerAddress** — 优先取，827家供应商有记录，但仅36家有真实非"asas"地址
2. **order_contract.providerOrgAddress** — 最完整，2229条记录覆盖210家不同供应商，推荐兜底
3. **trade.TF_Orders.ProviderOrgAddress** — 订单级别的地址，真实数据多，但只能覆盖有订单记录的供应商

### 空表（含地址字段但无数据）
- `TB_M_VarProvider` — 0条数据（有 WorkAddress, Person, Phone, MobPhone）
- `temp_VarProvider` — 0条数据
- `TO_Org_Provider_Old` — 0条数据（有 WorkAddress, RegAddress, CEOAddress 等）
