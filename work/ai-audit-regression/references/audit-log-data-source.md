# Production Audit Log Data Source

Third data source for regression testing: Excel export of the `audit_run_record` production table.

## File Location

`D:\平时处理文件\2026年7月\直采商城\新建Microsoft Excel 工作表.xlsx`

Converted to JSON: `D:\平时处理文件\2026年7月\直采商城\test_data_audit_log_103.json`

## Column Schema

| Column | Example | Notes |
|--------|---------|-------|
| `id` | 1650488820136980480 | Snowflake ID |
| `businessId` | 1648380725910880257 | FK to business record |
| `businessCode` | GOODS_COMPLETE_AUDIT | Always this value |
| `threadId` | c0995e4b-33d1-... | LangGraph thread UUID |
| `runId` | 019f3a6d-2137-... | LangGraph run UUID |
| `status` | COMPLETED/FAILED/PENDING/REPLACED | Run outcome |
| `resultJson` | `{"auditResult":"1","auditReason":"..."}` | Parsed when status=COMPLETED |
| `requestJson` | `{"baseBrand":"京瓷",...}` | The GoodsAiAuditRequestDTO payload |
| `errorMsg` | Various | Failure reason for FAILED status |
| `retryCount` | 0-3 | Number of retries |
| `createTime` | Excel serial date | Converted from numeric |

## JSON Escaping Fix

The `requestJson` uses double-escaped backslashes (`\\\\"`) inside `goodsDetailHtml`. Parse with:

```python
def fix_json(s):
    try: return json.loads(s)
    except:
        try: return json.loads(s.replace('\\\\"', '\\"'))
        except: return None
```

## test_type Classification

| test_type | status | gold standard | Purpose |
|-----------|--------|---------------|---------|
| `regression` | COMPLETED | `resultJson.auditResult` | Compare new skill vs old production result |
| `retry` | FAILED | None | Re-run failed items to get results |
| `pending` | PENDING | None | Items never executed |
| `replaced` | REPLACED | None | Withdrawn |

## Differences from XML Training Data

| Aspect | XML (061601.xml) | Audit Log |
|--------|------------------|-----------|
| Gold source | `human_audit_result` + `training_scenario` | `resultJson.auditResult` from prior run |
| Scenario labels | SCENARIO_2 / CONSISTENT_PASS etc | None — only auditResult |
| Data volume | 9,857 rows, 37 catalogs | 103 rows, 3 catalogs (硒鼓/粉盒/复印机) |
| Image paths | Clean relative (`groupkjxy/M00/...`) | Domain-prefixed (`//file.ccgp-chongqing.gov.cn/groupkjxy/...`) |
| category field | `"通用货物类"` (space, correct) | `"通用货物"` (no space, needs update) |
| brandMatch format | Integer (1) | Boolean (true) |
| detailImageUrls | Clean relative paths | Domain-prefixed paths |

## Known Data Issues

1. **category field is `"通用货物"` instead of `"通用货物类"`** — Must be updated before testing (see main SKILL.md pitfall)
2. **Image paths have `//file.ccgp-chongqing.gov.cn/` prefix** — Must strip before building gateway URLs
3. **Only 3 catalogs** (硒鼓/粉盒/复印机), 2 brands (京瓷/惠普) — limited coverage
4. **All paramPairs are empty** — no parameter validation testing possible
5. **All brandMatch/modelMatch/catalogMatch are true** — no Step2 termination testing possible
