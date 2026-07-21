# Column Mapping Reference

## CSV Format (query5 export, tab-separated, no header)

| Index | Field | Type | Example |
|-------|-------|------|---------|
| 0 | protocol_goods_id | string (numeric) | `1629184433053810688` |
| 1 | goods_rep_id | string | — |
| 2 | project_id | string | — |
| 3 | project_name | string | `2026年度重庆市党政机关...` |
| 4 | package_id | string | — |
| 5 | package_name / level_description | string | `电池（电池8）` |
| 6 | level_description / relation_name | string | `电池8` |
| 7 | relation_name | string | — |
| 8 | category | string | `通用货物` |
| 9 | goods_class | string | `货物类` |
| 10 | base_brand | string | `久信` |
| 11 | base_model | string | `阀控式密封铅酸蓄电池 JXA-200` |
| 12 | base_catalog | string | `电池` |
| 13 | base_unit | string | `台` |
| 14 | charge_unit | string | `元` |
| 15 | base_supplier | string | `重庆元新永信新能源科技有限责任公司` |
| 16 | base_limit_price | decimal | `2400.0000` |
| 17 | base_quote_price | decimal | `1790.0000` |
| 18 | standard_description | string | `适用于不间断电源（UPS）。...` |
| 19 | goods_type | string | `1` |
| 20 | goods_name | string | `久信 JXA-200阀控式密封铅酸蓄电池` |
| 21 | goods_detail_html | string (multi-line) | HTML富文本 |
| 22 | goods_detail_text | string (multi-line) | 纯文本 |
| 23 | image_urls_json | JSON array string | `[...]` |
| 24 | image_count | int | `1` |
| 25 | detail_image_count | int | `0` |
| 26 | param_pairs_json | JSON array | `[]` |
| 27 | brand_match | int (0/1) | `1` |
| 28 | model_match | int (0/1) | `0` |
| 29 | catalog_match | int (0/1) | `1` |
| 30 | goods_model_in_name | string | `\N` |
| **31** | **audit_request_json** | **JSON string** | **`{"baseUnit":"台",...}`** |
| 32 | ai_audit_result_code | int (-1/0/2) | `-1` |
| 33 | ai_oper_name | string | `智能审核退回` |
| 34 | ai_audit_reason | string | `审核不通过，原因：...` |
| 35 | ai_audit_result | string | `智能审核退回` |
| 36 | human_oper_name | string | `退回` |
| 37 | human_audit_reason | string | `商品名称请修改为：...` |
| 38 | human_audit_result | int (0/1) | `0` |
| **39** | **training_scenario** | **string** | **`SCENARIO_3_BOTH_REJECT`** |
| **40** | **data_label_fidelity** | **string** | **`LOW`** |
| **41** | **possible_data_changed_after_ai** | **int (0/1)** | **`0`** |
| 42 | ai_audit_time | datetime | `2026-06-15 14:54:01.122` |
| 43 | human_audit_time | datetime | `2026-06-15 09:26:04.578` |

## XML Format (Excel Spreadsheet ML)

Same fields as CSV but **named** in the header row. Access by header name:

```python
headers = cell_data(rows[0])  # Parse header row
hmap = {h: i for i, h in enumerate(headers)}
# Then:  cells[hmap['audit_request_json']]
```

## Result Value Normalization

| Storage format | API format | Meaning |
|----------------|-----------|---------|
| `-1` (CSV ai_audit_result_code) | `"0"` | 不通过 |
| `2` (CSV ai_audit_result_code) | `"1"` | 通过 |
| `0` (CSV ai_audit_result_code) | `"0"` | 转人工（实际为不通过） |
| `0` (CSV human_audit_result) | `"0"` | 退回/不通过 |
| `1` (CSV human_audit_result) | `"1"` | 通过 |
