# CONSISTENT_PASS Case Study: Huawei L540x-A016

Tested 2026-06-16 on 061601.xml data.

## Item Details

| Field | Value |
|-------|-------|
| Catalog | 便携式计算机 |
| Brand | 华为（HUAWEI） |
| Model | 华为擎云 L540x-A016 |
| Training scenario | CONSISTENT_PASS |
| Data label fidelity | MEDIUM |
| Images | 0 |
| Parameters | 6 total, all `goodsValue=null` |
| Detail text | Empty string `""` |
| `modelMatch` | `false` |
| `brandMatch` | `true` |
| `catalogMatch` | `true` |
| Fast (original AI) | ✅ Pass (2) |
| Human | ✅ Pass (1) |
| **Skill** | **❌ Fail (0)** |

## Skill Audit Results

| Step | Result | Detail |
|------|--------|--------|
| 1 — 品类识别 | ✅ pass | 计算机设备 |
| **2 — 品牌/型号/目录** | **❌ fail [terminated]** | modelMatch=false |
| 3 — 名称格式 | ⏭ skip | Terminated by Step2 |
| **4 — 参数符合性** | **❌ fail** | All 6 params null |
| **5 — 图片合规** | **❌ fail** | imageCount=0 (requires ≥3) |
| **6 — 详情合规** | **❌ fail** | Empty detail text |

## Issues Found (9 total)

1. **型号**: 型号与入围不一致 (fix: confirm model matches 华为擎云 L540x-A016)
2. **内存配置容量（GB）**: 参数值缺失 (fix: ≥8)
3. **CPU物理核数**: 参数值缺失 (fix: ≥8)
4. **固态存储容量（GB）**: 参数值缺失 (fix: ≥512)
5. **显卡类型**: 参数值缺失 (fix: 集成显卡)
6. **CPU主频（GHz）**: 参数值缺失 (fix: ≥2.3)
7. **CPU支持的内存最高速率（MT/s）**: 参数值缺失 (fix: ≥6400)
8. **商品图片**: 图片数量不足 (fix: upload ≥3)
9. **商品详情**: 详情为空 (fix: add description)

## Key Insight

This is a textbook example of CONSISTENT_PASS where **both the old AI engine AND the human reviewer missed genuine data quality issues**. The Skill correctly identified:

- The model name in `goodsName` (`华为擎云 L540x-A016`) doesn't match `baseModel` (`华为擎云 L540x-A016` — there's a trailing space difference that causes `modelMatch=false`)
- All 6 required parameters were never filled in
- No images uploaded despite requirement for ≥3
- No detail description

**Lesson:** CONSISTENT_PASS mismatches (Skill returns 0, gold says 1) are NOT automatically Skill errors. They may reveal gaps in the original audit pipeline. Before marking as a Skill bug, verify the item's actual data quality.
