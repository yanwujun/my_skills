# 37-Catalog Test Results — goods-audit-eight (2026-06-26)

## Summary
- **37 catalogs × 5 items = 185 total**
- **141 matched, 44 mismatched = 76.2% agreement**
- **Mode:** Threaded (stateful), image_url embedding, detailImageUrls from goodsDetailHtml
- **Timeout:** 300s per item, ~5 hours wall time
- **Agent:** 6000bb28, Skill: goods-audit-eight

## Per-Catalog

| Catalog | Items | Matched | Rate |
|---------|:-----:|:-------:|:----:|
| A3彩色打印机 | 5 | 5 | 100% |
| A4黑白打印机 | 5 | 5 | 100% |
| 办公椅 | 5 | 5 | 100% |
| 台式计算机 | 5 | 5 | 100% |
| 墨盒/墨水 | 5 | 5 | 100% |
| 复印机 | 5 | 5 | 100% |
| 电池 | 5 | 5 | 100% |
| 电脑桌 | 5 | 5 | 100% |
| 票据打印机 | 5 | 5 | 100% |
| 粉盒 | 5 | 5 | 100% |
| 越野车（含SUV） | 5 | 5 | 100% |
| A4彩色打印机 | 5 | 4 | 80% |
| 不间断电源（UPS） | 5 | 4 | 80% |
| 会议桌 | 5 | 4 | 80% |
| 会议椅 | 5 | 4 | 80% |
| 其他打印机（存折） | 5 | 4 | 80% |
| 办公桌 | 5 | 4 | 80% |
| 屏风工位 | 5 | 4 | 80% |
| 扫描仪 | 5 | 4 | 80% |
| 投影仪 | 5 | 4 | 80% |
| 硒鼓 | 5 | 4 | 80% |
| 空调机 | 5 | 4 | 80% |
| 茶几 | 5 | 4 | 80% |
| A3黑白打印机 | 5 | 3 | 60% |
| 便携式计算机 | 5 | 3 | 60% |
| 复印纸 | 5 | 3 | 60% |
| 多功能一体机 | 5 | 3 | 60% |
| 小型客车（含MPV） | 5 | 3 | 60% |
| 折叠椅 | 5 | 3 | 60% |
| 桌前椅 | 5 | 3 | 60% |
| 沙发 | 5 | 3 | 60% |
| 硒鼓碳粉 | 5 | 3 | 60% |
| 轿车 | 5 | 3 | 60% |
| 其他打印机（证卡） | 5 | 2 | 40% |
| 投影幕 | 5 | 2 | 40% |
| 碎纸机 | 5 | 2 | 40% |
| 色带 | 5 | 2 | 40% |

## Patterns

- **DPK brand (7 failures):** 证卡(3), 色带(2), 存折(1), 票据(1)
- **Normalization gaps:** `pass` (lowercase) from 复印纸本刻; `parse_err` from 轿车长安/阿维塔
- **Skill improvement:** goods-audit-eight (76.2%) vs kjxy-goods-audit-two (50%)
