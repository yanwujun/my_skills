---
name: llm-json-output-validation
description: "Validate LLM JSON output for AI features (出题/审核/批改/分析): schema-layer Pydantic model_validator + business shape checks + temperature-bump retry + layered table-driven tests."
---

# LLM JSON Output Validation

Trigger: building any AI feature where the LLM returns structured JSON that must be persisted or acted on — 出题 (quiz generation), 审核/批改 (grading), 单题判定, 薄弱点分析. Works with DeepSeek / any OpenAI-compatible `response_format={"type":"json_object"}` endpoint.

## Core rules

### 1. Two validation layers — never one

| Layer | Where | What it checks | Fails as |
|---|---|---|---|
| **Schema layer** | Pydantic `model_validator` on the **item model** | Structural invariants independent of config: type-dependent fields, enums, min_length, non-empty | `ValidationError` at `model_validate` |
| **Shape layer** | Aggregate method (e.g. `validate_shape(cfg)`) | Config-consistency: total count, type ratio, cross-item rules | `ValueError` with message |

**Why the split matters:** structural rules (e.g. "choice questions must have exactly 4 non-empty options; fill questions must NOT have options") MUST live in the schema model, not only in the service check. `Optional` fields silently accept missing/empty values at `model_validate` time — a choice question with 2 options or no options passes if the only guard is a downstream business check. Malformed LLM output must be rejected at the earliest point, before business logic runs.

### 2. Prompt & JSON mode

- DeepSeek requires the word "JSON"/"json" in the prompt for `response_format={"type":"json_object"}` to work — state the exact output shape in the system prompt.
- Validate BEFORE persisting: bad payload → retry, never crash the background task.

### 3. Retry with temperature bump

On validation failure, retry with a temperature bump (0.2 → 0.7), max 2 attempts. Still failing → mark the task `failed` in its state machine (generating→failed / submitted→failed, allow re-submit) and log. Do not raise into the request handler.

### 4. Layered table-driven tests

- **Schema layer**: `@pytest.mark.parametrize` payload matrix — valid payload, top-level missing key, empty list, illegal type literal, choice missing options, wrong option count, empty option string, fill-with-options. Each row `(payload, expect_ok)`.
- **Shape layer**: explicit cases — count mismatch, ratio mismatch, cross-item consistency.
- Split the two so a schema regression fails at the schema test, not the shape test.

## Pitfalls

- **Options-structure validation in the wrong layer** (the classic bug): it passes when placed only in `validate_shape()` — the schema test for "choice with 2 options" fails to raise. Fix: `model_validator(mode="after")` on the item model.
- **Tests that conflate layers**: a test expecting `model_validate` to reject a "1 question" payload (count is a SHAPE rule, not schema — `min_length=1` accepts it). Keep expectations per-layer.
- **Error message ordering**: if `validate_shape` checks multiple rules, the first hit wins — write test regexes to match the actual first rule (e.g. ratio check fires before count check depending on order).
- **Don't leak the ground truth**: if the API serves questions but the answer/explanation is for grading only, the response DTO must exclude answer fields (separate DTOs for client vs LLM/internal).

## Support files

- `references/quiz-generation-m1.md` — worked example: smart-learn-app M1 (DeepSeek 出题), the schema/shape models, the retry loop, and the failing→passing test history.
