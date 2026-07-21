# Cached Test Data

Pre-parsed test items extracted from the 300MB XML file to avoid re-parsing overhead.

## File

`D:\项目\gitlib\智能审核\doc\线上数据\test_data_164.json`

WSL path: `/mnt/d/项目/gitlib/智能审核/doc/线上数据/test_data_164.json`

## Structure

```json
{
  "extracted_at": <unix timestamp>,
  "source": "061601.xml",
  "total": 164,
  "catalogs": 37,
  "per_scenario": 3,
  "items": [
    {
      "cat": "A4彩色打印机",
      "scenario": "SCENARIO_2_AI_REJECT_HUMAN_PASS",
      "fidelity": "HIGH",
      "brand": "佳能（Canon）",
      "model": "G3830",
      "fast": "0",
      "human": "1",
      "ai_reason": "...",
      "human_reason": "...",
      "audit_request_json": "{...}"
    }
  ]
}
```

## Usage

```python
import json

with open('/mnt/d/项目/gitlib/智能审核/doc/线上数据/test_data_164.json', encoding='utf-8') as f:
    data = json.load(f)

items = data['items']
# 164 items, 37 catalogs, per_scenario=3
# Each item has: cat, scenario, fidelity, brand, model, fast, human, ai_reason, human_reason, audit_request_json
```

## Selection Logic

- Brand-dedup per (catalog, scenario) pair
- 3 items per scenario type per catalog
- HIGH fidelity preferred over LOW
- Scenarios: SCENARIO_2_AI_REJECT_HUMAN_PASS, CONSISTENT_PASS, SCENARIO_3_BOTH_REJECT

## When to use

- **Always prefer this cached file** over re-parsing the 300MB XML
- Only re-parse XML if the data source has changed (new XML file)
- The JSON loads in <1 second vs ~30 seconds for XML parsing
