---
name: code-change-automation
description: "Code-change-driven automation for Java/Spring enterprise projects — test plan generation from svn/git diffs, API test execution via Swagger + MySQL verification, and business rule documentation updates. Used by /test_code and review-svn commands."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [test-automation, api-testing, business-rules, test-plan, swagger, mysql, code-review, java]
    related_skills: [government-procurement-ops, codebase-security-audit]
---

# Code Change Automation Pipeline

Covers the full pipeline from code change → test plan → test execution → business rule documentation. Designed for Java/Spring enterprise projects using `ai_docs/` convention for test and documentation artifacts.

## Pipeline Overview

```
svn diff / git diff
    │
    ├─► [Step 0] Test Plan Orchestration
    │     Match existing test plan or generate new one
    │     Output: ai_docs/test_cases/<name>_TEST_PLAN.md
    │
    ├─► [Step 1-2] Environment Setup
    │     Start backend service, connect Chrome DevTools, mock-login
    │
    ├─► [Step 3] API Test Execution
    │     For each case: prepare data → call API → assert → verify DB
    │     Output: Test results table
    │
    └─► [Trigger: review-svn] Business Rules Documentation
        Create/update ai_docs/business_rules/<prefix>_<class>_<method>.md
        When changes touch HTTP endpoints, scheduled tasks, or MQ consumers
```

## Code Delta Analysis (Pre-Change Discovery)

Before making any code change, systematically determine what already exists. Skipping this leads to duplicate logic, unnecessary work, or overwriting existing behaviour.

### 1. Search for Partial Implementations

Run targeted searches across both projects (trade + ezc):

```
grep -rn "featureName\|RelatedField\|methodName" --include="*.java"
```

Look for:
- **DTO fields** that already have the property (e.g. `allowNegativeGoodsNum` in `DealConfigCodeDTO`)
- **Enum entries** that might already exist or need a companion entry
- **Service methods** that already implement or partially implement the logic
- **Controller/API endpoints** that already expose the feature

### 2. Trace All Affected Code Paths

For any new field or behaviour, trace through every lifecycle stage:

| Stage | What to check | Example |
|-------|---------------|---------|
| Initialization | Is the check/field applied when the entity is first created? | `initOrderEditEntity()` |
| Save (temp) | Is it validated on draft save? | `saveOrder`, `saveSupplementOrderData` |
| Submit | Is it validated on final submit? | `validateDataWhenSubmit()` |
| Edit | Is it re-validated when the entity is modified? | `OrderEditServiceImpl:1491` |
| Receiving/delivery | Does receiving logic handle it? | `validateDataReasonableBeforeSave` |
| Contract signing | Does contract creation reference the value? | `OrderContractServiceImpl` |
| Filing/备案 push | Is the value included in push DTO assembly? | `setRegisterInfoGoodsInfo()` |
| Calculation | Do arithmetic operations handle the value correctly? | `price.multiply(goodsNum)` |

Trace each stage by searching the service implementation files for related method calls.

### 3. Determine the True Delta

After search + trace, map what's needed:

```
State: [Already works] / [Needs change] / [Not applicable]
```

Common outcomes:
- **DTO field exists, enum entry missing** → Add enum entry only
- **Method exists, not called from all paths** → Add call at missing entry points
- **Logic exists for one state (e.g. edit) but not another (e.g. init)** → Copy the call pattern
- **No prior implementation** → Full implementation needed

### 4. Apply Changes at the Right Points

Once delta is clear:

- Prefer adding calls to existing methods over creating new ones
- In WSL with SVN-checked-out files on NTFS: files are **read-only** (`-r-xr-xr-x`). Run `chmod -R u+w <src-dir>` **before** using the `patch` tool. The `workdir` parameter may also be blocked — use absolute paths.
- Update **interface first**, then implementation (Spring Service pattern)
- Validate imports after every edit — common missing imports: `ArrayList`, `Set`, `Map`
- When `patch` reports an `Escape-drift` error with escaped quotes, re-read the file with `read_file` and use the raw content — do NOT manually escape quotes
- Verify the change compiles by checking imports and method signatures. When Maven/JDK are on the Windows side, use the WSL-adapted wrapper from `references/wsl-svn-java-editing.md` (the stock `mvn` fails because Windows Java can't read `/mnt/d/` paths)
- See `references/wsl-svn-java-editing.md` for the full reference on WSL+SVN+Java editing mechanics (Java list pattern, import checklist, patch pitfalls, WSL Maven wrapper, Chinese quote encoding fix)

### 5. Principles

1. Assume the codebase has partial groundwork — always search first.
2. One behavioural change often needs tweaks at 3-5 different code points. Don't stop after the first match.
3. If a validation method exists but isn't called from all lifecycle paths, the fix is to add the call, not rewrite the validation.
4. Java/Spring projects commonly use a `checkService` / `Engine` facade pattern — look there for reusable validation methods before writing new ones.

## Commands

| Command | Triggers | Purpose |
|---------|----------|---------|
| `/test_code` | All 3 phases | Runs the full pipeline: plan → test |
| `review-svn` | Phase 3 only | Updates business rule docs for changed API entries |

---

## Section 1: Test Plan Orchestration

Triggered by `/test_code` Step 0. Reads code diffs and either matches existing test plans or generates new ones.

### 1.1 Identify Changes

Read `svn status` + `svn diff` (or `git status` + `git diff`):
- Determine modified files list
- Identify affected entry points: Controller methods, Service interfaces, Repository
- Tag change type: new / modified / deleted / refactor (no behavior change)

### 1.2 Match Existing Plans

Scan `ai_docs/test_cases/` directory:
- Read `TEST_CASE_INDEX.md` (if exists) for plan index
- Search `*_TEST_PLAN.md` files by name pattern
- Judge coverage against changed entry points

**Match rules:**
- Plan title/description explicitly mentions the changed entry point name
- Plan's last modification time is before the change (may need incremental update)
- Partial match → incrementally update existing plan, do NOT create new

### 1.3 Generate New Plan (when no match)

Write to `ai_docs/test_cases/`:

```markdown
# {Feature} Test Plan

## Change Summary
{brief svn diff description}

## Test Scope
| Entry | Change Type | Description |
|-------|-------------|-------------|
| {Controller/Service} | {new/modified} | {change} |

## Environment
- Backend: {project}, port {default 25325}
- Database: {db_name}
- Login: mock-login (see TEST_ENV.md)
- Browser debug port: 9222

## Prerequisites (DDL / data baseline)
{data that must be prepared}

## Test Cases

| caseId | Scene | Steps | Params | Expected HTTP | Expected Code | Expected DB | Pre SQL | Verify SQL |
|--------|-------|-------|--------|-------------|-------------|------------|---------|-----------|
| TC001 | {scene} | 1. {step} | {params} | 200 | 00000 | {table-field-value} | {sql} | {sql} |

## General Verify SQL
{run for all cases}

## Cleanup SQL
{cleanup after execution}
```

### 1.4 Update Index

If a plan is created or deleted, sync `TEST_CASE_INDEX.md`:

```markdown
# Test Case Index

| Plan File | Description | Case Count | Last Updated |
|-----------|-------------|------------|-------------|
| {filename} | {desc} | {count} | {date} |
```

### 1.5 Output

Orchestration conclusion should include:
- Plan file path (matched / new / incremental)
- Recommended caseId range to execute
- Prerequisites list (environment, data baseline)
- If diff is empty → "No test needed"

---

## Section 2: API Test Execution

Triggered by `/test_code` command once environment is ready (Chrome DevTools MCP available, backend running, mock-login done).

### 2.1 Per-Case Execution Loop

For each `caseId` in the test plan:

**Step 1: Prepare Data** — Execute pre-SQLs (INSERT/UPDATE for baseline data)

**Step 2: Call API** — Use Chrome DevTools MCP `evaluate_script` + `fetch`:

```javascript
const res = await fetch('{URL}', {
  method: '{POST/GET/PUT/DELETE}',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({params})
});
const data = await res.json();
JSON.stringify({ status: res.status, body: data });
```

- Prefer `fetch` direct API calls
- Fallback: interact through Swagger UI page (locate → fill params → Execute)
- Special tokens/headers from TEST_ENV.md or business rule docs

**Step 3: Assert** — HTTP status, business code, key data fields

**Step 4: DB Verify** — Execute verify SQL, check records and field values

**Step 5: Record Result:**

| Field | Content |
|-------|---------|
| caseId | TC001 |
| scene | {scene} |
| request | {URL + param summary} |
| response | {status + body summary} |
| db_check | {SQL result} |
| result | PASS / FAIL / BLOCKED |
| reason | {failure reason} |

### 2.2 Principles

- Read-only DB by default (SELECT only); writes only from marked pre-SQL/cleanup SQL
- On failure: collect response body + DB result + timestamp
- Single case failure does NOT block subsequent cases
- Environment issues → mark as BLOCKED (not FAIL)

### 2.3 MCP Selection Reference

| MCP | Best For | Notes |
|-----|----------|-------|
| **Chrome DevTools MCP** | Automated regression tests | `evaluate_script` + `fetch`: 5-10x faster than Swagger UI |
| **cursor-ide-browser** | Visual debugging, Swagger page check | Zero config, real screenshots — but no `evaluate_script` |
| **Apifox MCP** | CI / formal regression | Stable, no browser process — but API defs need sync |

### 2.4 Pitfalls

- **Don't** start backend service in this skill — delegate to `/start_app` command
- Chrome DevTools MCP port 9222 conflict: check port is free before starting
- cursor-ide-browser cookies don't persist across sessions — re-login each time
- Swagger UI login may differ from direct API login — ensure session cookie is valid

(Full reference: `references/mcp-comparison.md`)

---

## Section 3: Business Rules Documentation

Triggered by `review-svn` command when code changes touch **external entry points** defined below.

### 3.1 Trigger Conditions

**Must** update when changes affect:
- **HTTP Endpoints**: Controller methods (new/modified params, return values, validation logic, state transitions)
- **Scheduled Tasks**: `@Scheduled` methods (frequency, business logic, compensation changes)
- **MQ Consumers**: `@RocketMQMessageListener` et al. (consumption logic, retry, dead-letter strategy changes)

**Skip** when changes are purely internal (no change to external behavior semantics).

### 3.2 Document Location & Naming

**Directory**: `ai_docs/business_rules/`
**Naming**: `{type}_{class}_{method}.md`

| Behavior Type | Prefix | Example |
|---------------|--------|---------|
| HTTP endpoint | `API` | `API_ProviderEnterPlatOrgController_audit.md` |
| Scheduled task | `CRON` | `CRON_GoodsSyncTask_syncExpired.md` |
| MQ consumer | `MQ` | `MQ_MqService_supplyChainReAuditSingleListener.md` |

**Entry Index**: `ai_docs/business_rules/ENTRY_INDEX.md`
Each new/deleted entry doc must sync the index as a concise Markdown table: entry path → doc link → short description.

### 3.3 Document Template

```markdown
# 【Basic Info】

| Field | Content |
|-------|---------|
| Behavior Type | API / CRON / MQ |
| Behavior Name | {verb phrase, e.g., Platform admin audits platform entry list} |
| System | {project name, e.g., Mall Base (xcj-mallbase)} |

## 【Business Goal】

{One sentence describing the business problem this entry solves}

## 【Roles】

| Role | Function |
|------|----------|
| {role} | {description} |

## 【Prerequisites】

- {prerequisite 1}

## 【Input Data】

- {data item}: {description}

## 【Core Business Rules】

**RULE_{DOMAIN}_{NNN}**

- **Description**: {business semantics, NOT implementation details}
- **Trigger**: {when applicable}
- **Logic**: {behavioral constraints}
- **Data Dependencies**: {data sources}
- **Affected Objects**: {what the rule acts on}

## 【State Transitions】

{description: e.g., On approval, state goes from PENDING → APPROVED}

## 【Exception Rules】

**EX_{DOMAIN}_{NNN}**

- **Description**: {exception scenario}
- **Trigger**: {when triggered}
- **Logic**: {rejection / compensation behavior}
- **Data Dependencies**: {data used}
- **Affected Objects**: {scope}

## 【Side Effects】

- {side effect 1: e.g., triggers notification, operation log}

## 【Idempotency & Re-entry】

{Behavior on repeated calls}

## 【Boundaries】

- {what this entry does NOT cover}

## 【Dependencies】

```
DEPEND_ON: {dependency list}
UNIT_ID: {unique unit ID}
```
```

### 3.4 Principles

1. **Business semantics only, no implementation details.** No SQL, API calls, class names, variable names.
2. **Rules must be split into individual RULE_IDs.** Format: `RULE_{domain abbreviation}_{3-digit sequence}`.
3. **One document = one entry point.** One Controller method or one MQ consumer only — never merge multiple.
4. If document doesn't exist and this is NOT a "final consolidation" phase, create a placeholder with `TODO`.

---

## References

- `references/mcp-comparison.md` — MCP selection guide for API test execution
- `references/wsl-svn-java-editing.md` — WSL+SVN+Java editing mechanics (read-only SVN files, patch tool pitfalls, import verification, Spring interface+impl pattern)
