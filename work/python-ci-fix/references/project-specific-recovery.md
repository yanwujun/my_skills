# business-rule-graph CI Recovery Commands

Project-specific commands to fix common CI drift in `yanwujun/business-rule-graph`.

## Ruff

```bash
cd ~/business-rule-graph
.venv/bin/ruff format src/ tests/
.venv/bin/ruff check --fix src/ tests/
```

## Doc drift

```bash
# README / AGENTS / llms-install / MCP server card counts
.venv/bin/python dev/build_readme_counts.py --apply

# COMMANDS.md
.venv/bin/python scripts/build_commands_doc.py
```

## Common code-level issues

### Missing `_query_try_catch` method
File: `src/roam/business_rules/extractor.py`
The method was called but never implemented. It uses `TREE_SITTER_QUERIES["try_catch_business"]` from patterns.py. The query captures `@caught_type` — the exception type. Implementation follows the same pattern as `_query_if_throw` / `_query_standalone_throw`.

### Missing `@roam_capability` decorators
File: `src/roam/business_rules/commands/cmd_br_extract.py`
All 8 `business-rules-*` commands must be decorated. Import `roam_capability` from `roam.capability`. Test: `test_capability_decoration.py::test_every_command_decorated`.

### `src` variable undefined (F821)
File: `src/roam/business_rules/extractor.py`, method `_extract_tree_sitter`
The commit `29dd9412` removed `src = source  # alias` but didn't update the downstream calls. Change all `src` references to `source` in the `_query_*` calls.

## Test assertion mismatches

### test_atomic_writes.py
`test_conditional_install_file_rejects_same_size_rewrite_with_restored_mtime` — the exception message changed from `"tempfile content changed"` to either `"atomic-install source changed while it was inspected"` or `"atomic-write tempfile content changed before install"` depending on code path. Use broader `match="changed"` pattern.
