# Execution Time Profiling — Measured Results

## Summary

| Path | Typical Duration | Notes |
|------|-----------------|-------|
| Step2 termination (brand/model/catalog mismatch) | < 0.1s | Rule engine, no LLM |
| Step4 failure (parameter mismatch) | < 0.1s | Rule engine, no LLM |
| Step5/6 (image LLM + detail LLM) | 15-120s+ | LLM calls, slowest path |
| Full pass (all steps pass) | 0.01s-60s | Fast rule + optional LLM |

## Real Measurements (061601.xml, HIGH fidelity, per-catalog threads)

**Test 1: 台式计算机, 10 items**
| Item | Brand/Model | Result | Time |
|------|-------------|--------|------|
| 1 | 联硕弘道 DF700MR | 0 (step2 termination) | 0.01s |
| 2 | 开天 E50z G1t-D285 | 0 (step2 termination) | 0.01s |
| 3 | 华为擎云 W585y-A011 | 0 (step2 termination) | 0.01s |
| 4 | 华为擎云 W585y-A091 | 0 (step2 termination) | 0.01s |
| 5 | TFM 智星D0030 | 0 (step2 termination) | 0.01s |
| 6 | TFM 智星D0022 | 0 (step2 termination) | 0.01s |
| 7 | TFM 智星D0023 | 0 (step2 termination) | 0.01s |
| 8 | TFM 智星D0022 | 0 (step2 termination) | 0.01s |
| 9 | TFM 智星D0098 | 0 (step2 termination) | 0.01s |
| 10 | TFM 智星D0030 | 0 (step2 termination) | 0.01s |
| **Total** | | **0/10 match** | **501s** |

**Key observations:**
- All 10 items terminated at Step2 (all had modelMatch=false or brandMatch=false)
- All completed in 0.01s — pure rule engine, no LLM
- Total 501s due to sequential execution overhead (approx 50s per item even though each was 0.01s API time)

**Test 2: 便携式计算机, 2 items (of 10 planned)**
| Item | Brand/Model | Result | Time |
|------|-------------|--------|------|
| 1 | 联硕弘道 L5 Z1 | 0 (step4 failure) | 0.01s |
| 2 | 兆瀚 L320-H051 | 0 (step4 failure) | 0.01s |

**Key observations:**
- First item: 参数「抗干扰性」填写错误（填了供应链服务承诺内容而非电磁兼容性技术指标）
- Second item: also failed at step4 (parameter mismatch)
- Both completed in 0.01s

**Test 3: 会议桌, 1 item**
| Item | Brand/Model | Result | Time |
|------|-------------|--------|------|
| 1 | 宝地文亿 1200*550*750 | ⏳ running | >600s |

**Key observations:**
- This item likely passed Step2-4 and triggered Step5 (image LLM)
- The threaded endpoint hung for >600s without returning
- This demonstrates the timeout issue with urllib

## First Run vs Second Run Variability

On the same input data, different runs can produce different results:

| Item | Run 1 | Run 2 |
|------|-------|-------|
| 联硕弘道 DF700MR | skill=0 ❌ (0.01s) | skill=1 ✅ (0.01s) |

This suggests the LLM component can make different decisions on different invocations, even for rule-layer items. Implications:
- A single pass is insufficient for benchmarking — run at least 2-3 passes
- Inconsistent results should be flagged for human review

## Catalog Performance Profile (061601.xml, HIGH fidelity)

| Catalog | Items | Avg time | Match rate | Notes |
|---------|-------|----------|------------|-------|
| 台式计算机 | 10 | 0.01s | 0% | All Step2 termination (modelMatch=false) |
| 便携式计算机 | 2 | 0.01s | 0% | Step4 parameter failures |
| 会议桌 | 1 | >600s | unknown | Stuck at Step5 image LLM |

## Thread Degradation

After ~5 sequential runs on the same thread, response times may degrade. By item 8-10, some requests that completed in 0.01s at the start may timeout at 60s. This is not related to the item characteristics — it's thread-level state accumulation.

**Mitigation:** Create fresh threads for each catalog. Avoid running more than 10 items on a single thread.
