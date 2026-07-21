# Focused Re-run Pattern for Low-Agreement Categories

After a full regression run, re-test only categories with low agreement (≤40%) or individual mismatched items to verify skill improvements.

## Two Approaches

### Approach A: Streaming Mismatch Re-test (recommended for 300MB+ XML)

Use `scripts/test_mismatches.py` — a streaming XML parser that reads the 300MB file line-by-line, matches only the target (catalog, brand) pairs, and tests one item per pair (dedup). See `references/streaming-xml-parser.md` for the parser pattern.

**Setup:** Edit the `TARGETS` set in the script to your mismatched pairs, then:

```bash
cd /home/administrator && python3 -u test_mismatches.py > /tmp/retest.log 2>&1
```

**Pros:** No memory issues, starts producing results as soon as a match is found, only ~40 API calls vs 185.

### Approach B: Full Re-run with Low-Category Filter

For smaller XML files or when you need all items from specific categories:

```bash
cd /home/administrator && python3 test_low_cats.py > /tmp/audit_low.log 2>&1
```

## Key Differences from Full Test Script

### 1. Targeted category/brand list
```python
TARGETS = {
    ('色带', 'DPK'), ('小型客车（含MPV）', '长安'), ...
}
```
Only items matching these (catalog, brand) pairs are collected from the XML.

### 2. Per-item detail in report (CRITICAL)
The report includes a full **Section 2: 逐条明细** table with:
- Brand, model, fast/human/skill three-column comparison
- Skill reason (from API response `auditReason`)
- Execution time per item
- Thread ID + Web UI link

### 3. Mismatch analysis
Items where `skill ≠ human` are grouped by category with:
- Direction: "skill误拒" (pred=0, human=1) or "skill误放" (pred=1, human=0)
- Skill reason text
- Thread ID link

### 4. Comparison with previous run
Include a "上次" column and "变化" delta to show improvement/regression.

## Pitfalls

### ⚠️ Threaded mode non-determinism
Threaded mode results are NOT reproducible across runs (5/9 items flipped in 2026-06-26 re-test). Prefer stateless `/runs/wait` for quantitative regression comparison. Threaded mode is for qualitative Web UI debugging only.

### ⚠️ Large payloads hang indefinitely
Items with massive standards text in paramPairs (会议桌, 办公家具) may hang the API. Mitigation: shorter timeout (180s), manual kill, or skip known offenders.

### ⚠️ Summary-Only Reports
Always write per-item details to the report file — do NOT rely on `/tmp/` log scraping (files cleaned between sessions).

## Report Sections
1. **Summary**: Per-catalog table with comparison to previous run
2. **逐条明细**: Full per-item table
3. **不一致项分析**: Mismatches grouped by category with root cause
4. *(optional)* **Optimization suggestions**
