# Code Graph Base Tool Comparison (2026-07)

## Summary

Evaluated 4 candidates as the Layer-1 (code structure graph) foundation for the business rule graph system. **Decision: roam-code.**

## Detailed Comparison

### roam-code (⭐500) — SELECTED

- **URL**: https://github.com/Cranot/roam-code
- **Language**: Python (matches our stack)
- **License**: Apache 2.0
- **Storage**: SQLite (easy to extend with business rule tables)
- **Languages supported**: 28 (including Java ✓)
- **Commits**: 2,248 (very active)

**Killer features for our use case:**
- `preflight` — risk assessment before edits (closest existing concept to rule conflict detection)
- `ChangeEvidence` packets — tamper-evident change tracking (can extend to rule version tracking)
- `Compiler` — pre-fills graph data into LLM prompt before the model sees it (reduces token waste for rule extraction)
- Coupling analysis — "which files change together" (helps identify cascading rule conflicts)
- 244 MCP tools — can reuse the MCP infrastructure for rule graph queries
- SQLite schema — adding `business_rules` and `rule_edges` tables is straightforward

**Extensions needed:**
1. Add business rule extraction module (AST scan + LLM merge)
2. Add SQLite tables: `business_rules`, `rule_edges`, `rule_versions`
3. Add conflict detection engine
4. Add rule-graph MCP tools (alongside existing 244 tools)

### Graphify (⭐91k) — REJECTED

- **URL**: https://github.com/Graphify-Labs/graphify
- **Language**: Python
- **Storage**: JSON file (graph.json) — harder to extend with relational rule data
- **Languages supported**: 36 tree-sitter grammars (including Java)

**Why rejected:**
- Massive codebase (91k stars, complex internals) — high modification cost
- JSON storage model — adding relational rule tables requires fundamental schema changes
- No `preflight`/change-safety concept — the --conflicts feature is about merge risk, not business rule risk
- Core focus is being an AI assistant skill, not an extensible code analysis platform

**Still useful for:**
- Reference implementation of community detection (Leiden algorithm)
- Reference for `graphify query/path/explain` graph traversal patterns
- Benchmark methodology (LOCOMO, LongMemEval)

### SocratiCode (⭐3.1k) — REJECTED

- **URL**: https://github.com/giancarloerra/SocratiCode
- **Language**: TypeScript — stack mismatch
- **Commits**: 184 (young project)

**Why rejected:**
- TypeScript codebase — our stack is Python/Java
- Fewer commits than roam-code, less battle-tested
- No preflight/risk-assessment concept

### Understand-anything + diff-to-business-rules — NOT A BASE

- Already in our Hermes skills
- Knowledge graph generation works but is LLM-intensive
- No incremental update without git
- No SQL storage, no conflict detection
- Useful for domain/flow extraction but not as a code structure base

## Selection Criteria Weighting

1. **Extensibility** (highest weight): Can we add business rule tables/types without fighting the architecture?
2. **Change tracking**: Does the tool already track what changed between runs?
3. **Risk assessment DNA**: Is there any existing concept of "check before you change"?
4. **Language match**: Does the tech stack align with ours?
5. **Java support**: Must handle Spring Boot / Maven projects
6. **Maturity**: Enough commits to trust, not so many that modification is heavy

roam-code scored highest on criteria 1-4, which are the most important for our transformation.
