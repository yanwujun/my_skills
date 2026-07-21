# Report Output to Windows Path

## Default Report Directory

All test reports go to the Windows filesystem, not the Linux home directory:

```
D:\项目\gitlib\智能审核\doc\
```

From WSL, this translates to:

```
/mnt/d/项目/gitlib/智能审核/doc/
```

## Naming Convention

Match the data source + test approach.

## Report Content Template — Three-Column Comparison

Every report must include a three-way comparison (fast vs 人工 vs skill), NOT just skill vs human.

### Section 1: Summary Table

Markdown table with 目录, 商品, fast, 人工, skill（归一）, 匹配, 耗时 columns.

### Section 2: Per-Item Detail (逐条明细)

Each item must include:
- **商品**：品牌型号
- **人工结果**：✅/❌ 通过/不通过
- **fast结果**：✅/❌ 通过/不通过
- **skill结果**：✅/❌ 通过/不通过
- **AI原审核原因**：from `ai_audit_reason` column (NOT `ai_oper_name`)
- **人工审核原因**：show `(空)` if empty
- **skill原因**：from API response
- **会话ID**：`uuid` [查看](http://192.168.2.166:5175/?thread_id=uuid)
- **分析**：summary of comparison

### Section 3: Mismatch Analysis

Categorize mismatches by root cause type.

## Web UI Port

Use **port 5175** for session ID links: `http://192.168.2.166:5175/?thread_id=<uuid>`

## Thread ID Logging

Always log `tid=<uuid>` in per-item print output during test runs. Without this, thread IDs are irrecoverable after test completion.

## Result Normalization

Normalize `PASS`/`FAIL` → `1`/`0` in reports.

## Report Field Name

Use `AI原审核原因`, NOT `fast原因`. Source column is `ai_audit_reason`.

## ⚠️ Skill AuditReason Is NOT Recoverable Post-Hoc

The skill's `auditReason` is **only available in the live API response**. Run records persist as `{}` (empty dict). Once the test finishes, the reason is lost forever unless you logged it.

**MUST capture at test time:**
```python
# In the test script, save BOTH pred and reason:
pj = json.loads(clean)
pred = norm(str(pj.get("auditResult", "?")))
reason = pj.get("auditReason", "")[:200]
results.append({"pred": pred, "reason": reason, "tid": tid, ...})
```

**When the user asks for reasons after a test has already completed:**
- You MUST re-call the API for each mismatched item to get the skill's reason
- Use **stateless** `/runs/wait` (faster, no thread creation overhead)
- Expect 35 API calls × ~60s = ~30 minutes for a full mismatch re-test
- Old AI reasons from the data (`ai_audit_reason` column) can serve as a stopgap

### Mismatch Table Format (with Skill Reason)

When the user asks to "see reasons" for mismatches, the report must include:

| # | 目录 | 品牌 | pred | human | 耗时 | skill原因 | old_AI原因 | 查看 |
|---|------|------|------|-------|------|-----------|------------|------|

The skill原因 column is the **most important** — it tells the user whether the skill needs adjustment.
