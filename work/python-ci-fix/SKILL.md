---
name: python-ci-fix
description: Systematic workflow for diagnosing and fixing Python project CI failures — ruff lint/format, doc drift, missing symbols, test assertion mismatches, and Dependabot PR handling.
tags: [ci, python, ruff, pytest, dependabot, linting]
---

# Python CI Fix Workflow

Use this skill when a Python project's CI is failing with multiple checks. The workflow moves from broad reproduction to targeted fixes in priority order.

## Trigger conditions

- 5+ failing CI checks on a Python project PR
- "CI is red", "all checks failed", "fix CI"
- Dependabot PRs with cascading failures (the root cause is usually not the dependency bump)

## Workflow

### 1. Reproduce locally first

```bash
cd <project>
uv sync --locked --no-default-groups --extra dev
```

Then run each failing check locally:
```bash
# Format check
.venv/bin/ruff format --check src/ tests/

# Lint check
.venv/bin/ruff check src/ tests/

# Tests (skip slow/perf tests that need `roam` CLI on PATH)
.venv/bin/python -m pytest tests/ -x -q -m "not slow"
```

### 2. Fix in priority order

**A. Format (zero risk)**
```bash
.venv/bin/ruff format src/ tests/
```

**B. Lint auto-fixable (low risk)**
```bash
.venv/bin/ruff check --fix src/ tests/
```

**C. Lint requires manual fix**
- F821 Undefined name: trace the variable — it may have been renamed or the alias line removed
- F401 Unused import: remove it (but verify it's truly unused across the file)
- F841 Unused variable: add an assertion or use `_` prefix
- I001 Import ordering: `--fix` usually handles this

**D. Doc drift**
Python projects often have auto-generated docs that count commands, MCP tools, etc. Look for:
- `dev/build_readme_counts.py --apply`
- `scripts/build_commands_doc.py`
- Any Makefile target that fixes doc drift

Run them, commit the changes. The test that checks this is often called `test_script_check_passes_at_head` or `test_commands_doc_in_sync_with_surface`.

**E. Test assertion mismatches**
When a test expects a specific error message but the code now raises a different message:
- Check the actual exception message from the traceback
- Update the test's `match=` pattern to match the new message
- If the exception is a subclass (e.g., `_AtomicInstallConflict` extends `FileExistsError`), the `pytest.raises` base class may still be correct — only the message pattern needs updating

**F. Missing decorators**
Some projects require `@roam_capability` or similar decorators on every CLI command entry point. Tests like `test_every_command_decorated` enforce this. Fix by adding the decorator with `name`, `category`, `summary`, `inputs`, `outputs`, and `examples` fields.

### 3. Dependabot PR handling

When a Dependabot PR has failing CI because `main` was broken:

**Preferred approach** (avoids force-push issues):
1. Apply the Dependabot change directly to `main`
2. Push to `main`
3. Close the Dependabot PR manually (it becomes redundant)

```bash
# Apply the Dependabot change
git checkout main
# Edit pyproject.toml or whatever file was changed
uv lock  # update lockfile if needed
git add -A
git commit -m "<copy Dependabot commit message>"
git push origin main
```

Then close the PR on GitHub. Dependabot will detect the change is already in `main` and won't re-open.

**Alternative** (when force-push is allowed):
```bash
git checkout -b dependabot/pip/xxx origin/dependabot/pip/xxx
git rebase main
git push origin dependabot/pip/xxx --force-with-lease
```

### 4. Verify

After all fixes:
```bash
.venv/bin/ruff check src/ tests/  && echo "LINT OK"
.venv/bin/ruff format --check src/ tests/  && echo "FORMAT OK"
.venv/bin/python -m pytest tests/ -x -q -m "not slow"
```

## Project-specific recovery commands

See `references/project-specific-recovery.md` for business-rule-graph specific commands (doc drift scripts, known missing methods, decorator patterns, test assertion fixes).

## Pitfalls

- **Don't fix Dependabot PRs by force-pushing**: Some environments block `--force-with-lease` on shared branches. Apply the change to `main` instead.
- **Don't skip the doc drift**: Running `ruff --fix` and `ruff format` isn't enough — generated docs (README counts, COMMANDS.md, AGENTS.md) must also be regenerated.
- **Tree-sitter imports may trigger false Pyright warnings**: `Query` and `.captures()` are dynamic at runtime but unknown to static analysis. These are expected in tree-sitter code.
- **Ruff I001 (import ordering) after manual edits**: If you edit imports manually, always run `ruff check --fix` afterward to re-sort.
