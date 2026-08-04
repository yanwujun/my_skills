---
name: diff-to-business-rules
description: Analyze code diffs to extract business rule changes and auto-update business rules documentation. Merges diff analysis + domain extraction + doc generation into one workflow.
argument-hint: "[--base <branch>] [--pr <number>] [--full]"
---

# /diff-to-business-rules

Analyze git diffs to identify business rule changes, extract affected domain flows, and auto-generate/update business rules documentation in `.understand-anything/business-rules/`.

## When to Use

- After committing feature changes — "what business rules did this PR change?"
- Before code review — "document what rules this branch introduces/modifies"
- Periodic documentation sync — "update business rules docs to match current code"
- Onboarding — "show me all the business rules in this codebase"

## Options

- `--base <branch>` — Compare against a specific base branch (default: `main`)
- `--pr <number>` — Analyze a GitHub/Gitee PR
- `--full` — Full scan mode: build a complete business rules doc from the entire codebase (not just diffs)

---

## Phase 0: Resolve PROJECT_ROOT

Set `PROJECT_ROOT` to the current working directory.

Detect git worktree and redirect to main repo root (same logic as `/understand`):
```bash
COMMON_DIR=$(git -C "$PROJECT_ROOT" rev-parse --git-common-dir 2>/dev/null)
GIT_DIR=$(git -C "$PROJECT_ROOT" rev-parse --git-dir 2>/dev/null)
if [ -n "$COMMON_DIR" ] && [ -n "$GIT_DIR" ]; then
  COMMON_ABS=$(cd "$PROJECT_ROOT" && cd "$COMMON_DIR" 2>/dev/null && pwd -P)
  GIT_ABS=$(cd "$PROJECT_ROOT" && cd "$GIT_DIR" 2>/dev/null && pwd -P)
  if [ -n "$COMMON_ABS" ] && [ "$COMMON_ABS" != "$GIT_ABS" ]; then
    MAIN_ROOT=$(dirname "$COMMON_ABS")
    if [ -d "$MAIN_ROOT" ]; then
      PROJECT_ROOT="$MAIN_ROOT"
    fi
  fi
fi
```

---

## Phase 1: Gather Changes

### Path A: Full Scan (`--full`)

Report: `[Phase 1/3] Full scan — analyzing entire codebase for business rules...`

1. Get ALL source files (respect .gitignore):
   ```bash
   git -C "$PROJECT_ROOT" ls-files --cached --others --exclude-standard | grep -E '\.(java|py|js|ts|go|rs|rb|php|cs|kt|swift)$'
   ```
2. Set `$CHANGED_FILES` to this full list.
3. Skip to Phase 2.

### Path B: Diff Analysis (default)

Report: `[Phase 1/3] Analyzing git diff for business rule changes...`

1. **Determine base branch:**
   - If `--base <branch>`: use that branch
   - Otherwise: try `main`, then `master`, then `develop`
   - Store as `$BASE_BRANCH`

2. **Get changed files:**
   ```bash
   git -C "$PROJECT_ROOT" diff $BASE_BRANCH..HEAD --name-only
   ```

3. **If no changes found** (or no commits ahead of base):
   - If on a branch with uncommitted changes, use `git diff --name-only` for staged/unstaged
   - If still empty: "No code changes detected." → STOP.

4. Filter to code files only (`.java`, `.py`, `.js`, `.ts`, `.go`, `.rs`, `.rb`, `.php`, `.cs`, `.kt`, `.swift`, `.sql`, `.xml`, `.yaml`, `.yml`, `.properties`)
   - Store as `$CHANGED_FILES`

5. Report what's being analyzed:
   > Found N changed code files across the diff.

---

## Phase 2: Knowledge Graph Cross-Reference (if available)

1. Check if `$PROJECT_ROOT/.understand-anything/knowledge-graph.json` exists.
2. **If it exists:**
   - For each changed file, find matching nodes in the graph:
     ```bash
     grep -o '"filePath":"[^"]*<relative-path>"' knowledge-graph.json
     ```
   - Follow edges to find affected domain flows (nodes with type `domain`, `flow`, `step` from domain-graph.json if available)
   - Note affected layers from the knowledge graph
3. **If it does NOT exist:** Skip graph context. Phase 3 will work purely from source code.
4. **If `$PROJECT_ROOT/.understand-anything/domain-graph.json` exists**, load it for domain/flow context.

Report what we found:
> Knowledge graph available with N nodes. Found M nodes related to changed files across L layers.

---

## Phase 3: Extract Business Rules

Report: `[Phase 2/3] Extracting business rules from changed files...`

This is the core analysis phase. For each changed file, extract business rules using pattern recognition.

### Business Rule Detection Patterns

Scan each changed file for these patterns. Read the diff hunks (not entire files when possible) to focus on changed lines.

| Pattern | What to look for | Rule type |
|---|---|---|
| **Validation rules** | `if`/`throw`/`raise`/`validate`/`check` on fields, annotations like `@NotNull`, `@Valid`, `@Min`, `@Max`, `@Pattern` | Validation |
| **Authorization rules** | `@PreAuthorize`, `@RolesAllowed`, `hasRole`, `hasPermission`, `can_`, `allowed_`, role checks | Authorization |
| **Status transitions** | State machine enums, status change methods, `transition`, `changeStatus`, `setStatus`, switch on status | Workflow |
| **Calculation rules** | Business math in services — pricing, discounts, taxes, commissions, scores, rankings | Calculation |
| **Data constraints** | Unique checks, `existsBy`, duplication guards, `UNIQUE` constraints in SQL, `@Column(unique=true)` | Data Integrity |
| **Workflow rules** | Approval chains, multi-step processes, event handlers, `@EventListener`, `on_`, `handle_` | Process |
| **Configuration rules** | Feature flags, `@Value`, `getProperty`, `.env` references that control behavior | Configuration |
| **Integration rules** | External API calls with retry/timeout, `@Retryable`, `CircuitBreaker`, error handling policies | Integration |

### Extraction Method

For each changed file:

1. **Get the diff** (not the full file) to focus on what changed:
   ```bash
   git -C "$PROJECT_ROOT" diff $BASE_BRANCH..HEAD -- "$FILE_PATH"
   ```

2. **Read the full file** if the diff shows significant new logic or if this is a new file.

3. **Classify each rule found:**
   - `rule_id`: kebab-case unique identifier (e.g., `order-amount-validation`)
   - `rule_type`: one of: `validation`, `authorization`, `workflow`, `calculation`, `data_integrity`, `process`, `configuration`, `integration`
   - `rule_name`: short human-readable name
   - `description`: what the rule enforces/does
   - `source`: file:line range where the rule is implemented
   - `domain`: business domain this belongs to (from knowledge graph or inferred from package/namespace)
   - `flow`: business flow this is part of (from domain graph if available)
   - `change_type`: `added`, `modified`, or `removed`

4. **Identify affected business rules** — even if the changed line isn't a rule itself, it may affect existing rules:
   - A modified validation constant affects all validation rules using it
   - A new field in a DTO affects all rules that process that DTO
   - A changed API endpoint affects the integration rules calling it

5. **Cross-reference with existing docs** — if `.understand-anything/business-rules/` already has markdown files:
   - Check which existing rules are touched by these changes
   - Mark them as `modified` or `removed`
   - Preserve rules that haven't changed

### Output Structure

Write the extraction result to `$PROJECT_ROOT/.understand-anything/intermediate/business-rules-extract.json`:

```json
{
  "version": "1.0.0",
  "generatedAt": "<ISO timestamp>",
  "baseBranch": "<branch>",
  "gitCommitHash": "<current HEAD>",
  "changedFiles": ["<file paths>"],
  "rules": [
    {
      "rule_id": "order-minimum-amount",
      "rule_type": "validation",
      "rule_name": "Order Minimum Amount",
      "description": "Orders must have a minimum total amount of ¥100 before submission. Enforced in OrderService.validateOrder().",
      "source": "src/main/java/com/xcj/service/OrderService.java:145-158",
      "domain": "订单管理",
      "flow": "用户下单流程",
      "change_type": "added"
    }
  ],
  "affected_existing_rules": ["order-status-transition"],
  "rule_count_by_type": {
    "validation": 5,
    "authorization": 2,
    "calculation": 3
  },
  "statistics": {
    "total_rules_found": 12,
    "new_rules": 8,
    "modified_rules": 3,
    "removed_rules": 1,
    "unchanged_rules_preserved": 45
  }
}
```

---

## Phase 4: Generate/Update Business Rules Documentation

Report: `[Phase 3/3] Generating business rules documentation...`

### Step 1: Prepare output directory
```bash
mkdir -p "$PROJECT_ROOT/.understand-anything/business-rules/"
```

### Step 2: Determine document structure

Based on the extracted rules and existing docs, choose one of:

**A. Domain-organized** (recommended for multi-domain projects):
```
business-rules/
├── README.md              (index with all domains and summary)
├── orders.md              (订单相关规则)
├── payments.md            (支付相关规则)
├── users.md               (用户相关规则)
├── products.md            (商品相关规则)
└── suppliers.md           (供应商相关规则)
```

**B. Single document** (for smaller projects or first run):
```
business-rules/
└── business-rules.md      (all rules in one document)
```

Choose based on rule count: >20 rules → domain-organized, ≤20 → single document.

### Step 3: Write/update documentation

Each rule document follows this template:

```markdown
# <Domain Name> Business Rules

> Auto-generated from code analysis. Run `/diff-to-business-rules` to update.
> Last updated: <timestamp> | Base branch: <branch> | Commit: <hash>

## Rules Summary

| Rule ID | Type | Description | Source | Status |
|---|---|---|---|---|
| order-minimum-amount | validation | Orders must be ≥ ¥100 | OrderService.java:145-158 | ✅ Active |
| supplier-approval-required | authorization | Only approved suppliers can bid | SupplierAuth.java:89-95 | ✅ Active |

---

## Validation Rules

### order-minimum-amount — Order Minimum Amount

**Rule:** Orders must have a minimum total amount of ¥100 before submission.

**Enforcement:** `OrderService.validateOrder()` throws `BusinessException(ORDER_AMOUNT_TOO_LOW)` when total < 100.

**Source:** `src/main/java/com/xcj/service/OrderService.java:145-158`

**Affected flows:** 用户下单流程

**Change:** ✅ Added in this analysis

---

### order-category-required — Order Category Required

**Rule:** Every order must be assigned to a valid product category.

**Enforcement:** `@NotNull` annotation on `Order.category` field. Database column `NOT NULL`.

**Source:** `src/main/java/com/xcj/model/Order.java:42`, `src/main/resources/db/migration/V2__add_category.sql:5`

**Affected flows:** 用户下单流程, 商品分类管理

---

## Authorization Rules

...

## Workflow Rules

...

## Calculation Rules

...
```

### Step 4: Write index README.md

```markdown
# Business Rules Documentation

> Auto-generated from the <project-name> codebase.
> **Run `/diff-to-business-rules` after making code changes** to keep this up to date.

## Domains

| Domain | File | Rules | Last Updated |
|---|---|---|---|
| 订单管理 | [orders.md](orders.md) | 12 rules | 2026-06-18 |
| 支付管理 | [payments.md](payments.md) | 8 rules | 2026-06-18 |
| 用户管理 | [users.md](users.md) | 5 rules | 2026-06-18 |

## Quick Stats

- **Total rules:** 25
- **By type:** validation(10), authorization(5), workflow(4), calculation(3), data_integrity(2), configuration(1)
- **This analysis:** +8 new, ~3 modified, -1 removed
```

### Step 5: Preserve existing rules that weren't touched

When updating, never delete rules that haven't changed. Merge:
1. Read existing `.md` files
2. Extract existing rules not in `affected_existing_rules`
3. Write: unchanged rules + new/modified rules from this analysis
4. Update the summary table and statistics

---

## Phase 5: Report

Output a clean summary:

```
══ Business Rules Analysis Complete ══

Project: <project-name>
Branch:   <current-branch> vs <base-branch>
Commit:   <short-hash>

📊 Rules Found: 12 (8 new, 3 modified, 1 removed)
📂 By Type:   validation(5), authorization(2), calculation(3), workflow(2)
🏷  By Domain: 订单管理(7), 支付管理(4), 用户管理(1)

📝 Documentation: .understand-anything/business-rules/
   ├── README.md        (index)
   ├── orders.md        (7 rules)
   └── payments.md      (5 rules)

💡 Tip: Run `/diff-to-business-rules` after your next commit to keep docs in sync.
```

---

## Error Handling

- If the project has no git repo, fall back to analyzing all source files (treat as `--full`)
- If knowledge graph is stale (different commit), still use it but add a warning
- If no business rules are detected in the diff, still update docs with a "no changes" entry
- ALWAYS preserve existing rules that weren't touched by the current diff
- If a file was deleted, mark its rules as `removed` in the docs (strikethrough or archive section)

---

## Pitfalls

1. **Don't treat every `if` statement as a business rule.** Focus on: validation logic, authorization checks, status transitions, calculations with business meaning, and configuration-driven behavior.
2. **Don't duplicate non-business logic.** Technical patterns (null checks, logging, retry infrastructure) are NOT business rules.
3. **Language awareness:**
   - Java/Spring: `@Valid`, `@NotNull`, `@PreAuthorize`, `@Transactional`
   - Python/Django: `clean()`, `validate_`, `has_perm`, `@permission_required`
   - Go: `if err != nil` with business error messages, middleware chains
   - TypeScript/Node: `zod`, `joi`, middleware, guards
4. **Respect existing documentation.** Never overwrite manually written sections. Add `<!-- MANUAL -->` markers around hand-maintained content.
5. **Chinese business terms:** When the codebase uses Chinese (like 直采商城), keep rule names and descriptions in Chinese to match the domain language.
