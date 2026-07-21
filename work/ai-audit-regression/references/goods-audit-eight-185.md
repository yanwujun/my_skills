# goods-audit-eight 37-Catalog × 5 Test (2026-06-26)

Full regression test with updated skill `goods-audit-eight` (brand English names from baseBrand, numeric param structured comparison, Step3 unified name format).

## Configuration

- **Data**: 061601.xml (9857 rows)
- **Agent**: 6000bb28, Skill: goods-audit-eight
- **Mode**: Threaded (有状态), 300s timeout per item
- **Image**: image_url embedding + detailImageUrls from goodsDetailHtml
- **Selection**: Brand-dedup per catalog, 5 items each, HIGH fidelity only
- **Script**: `scripts/run_xml_batch_v2.py` (updated: brand dedup, norm() extended, detail image extraction)

## Results

- **185 items across 37 catalogs**
- **141 matched / 44 mismatched = 76.2% agreement**
- **2 parse_err** (轿车 长安, 轿车 阿维塔)
- **1 normalization miss** (复印纸 本刻: pass lowercase → should be 1)

## Per-Catalog Agreement

### 100% (11 catalogs)
A3彩色打印机, A4黑白打印机, 办公椅, 台式计算机, 墨盒/墨水, 复印机, 电池, 电脑桌, 票据打印机, 粉盒, 越野车(含SUV)

### 80% (11 catalogs)
A4彩色打印机, 不间断电源(UPS), 会议桌, 会议椅, 其他打印机(存折), 办公桌, 屏风工位, 扫描仪, 投影仪, 硒鼓, 空调机, 茶几

### 60% (11 catalogs)
A3黑白打印机, 便携式计算机, 复印纸, 多功能一体机, 小型客车(MPV), 折叠椅, 桌前椅, 沙发, 硒鼓碳粉, 轿车

### 40% (4 catalogs — critical)
其他打印机(证卡), 投影幕, 碎纸机, 色带

## Mismatch Patterns

1. **DPK brand (7 mismatches)**: 证卡打印机(3), 存折打印机(1), 色带(2) — DPK image brands don't match text brand (fujitsu/富士通 in images)
2. **Rule-layer failures (15)**: 投影幕, 碎纸机, 色带 — brand/model/catalog matching
3. **Data quality (10)**: Items where old fast engine also rejected (海尔便携, 唛哒空调, etc.)
4. **LLM-layer (12)**: 多功能一体机, 复印纸, 沙发, 桌椅 — param/detail consistency

## Structured Output Format

The agents-platform supports `use_structured_output` in `config.configurable.frontend_structured_output`. Response format:
- Tool message with `Returning structured response: {json}` containing the audit result
- Faster than normal mode (2-10s for rule items)
- Must parse differently: search tool messages for `Returning structured response:`

## Comparison

| Metric | goods-audit-two (2026-06-18) | goods-audit-eight (2026-06-26) |
|--------|:---:|:---:|
| Sample | 10 items | 185 items |
| Agreement | 50% | 76.2% |
| BrandMatch fix | ❌ A3彩色夏普 fails | ✅ passes |
| Output format | PASS/FAIL inconsistency | Mostly unified |
| detailImageUrls | Not parsed | Parsed from goodsDetailHtml |

## Skill Improvement Drivers

The +26pp improvement came from user's skill changes:
1. Brand English names from baseBrand (not from image OCR)
2. Numeric params use baseMin/MaxValue + Symbol for structured comparison
3. Step3 unified name format: English name follows baseBrand, model written directly without brackets
