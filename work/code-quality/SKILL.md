---
name: code-quality
description: "Code quality verification suite: pre-commit review pipeline with security scanning and auto-fix, test-driven development (RED-GREEN-REFACTOR) enforcement, and deep security audit of large codebases."
version: 1.0.0
author: Hermes Agent (consolidated)
license: MIT
metadata:
  hermes:
    tags: [code-quality, testing, security, audit, tdd, verification, pre-commit]
    related_skills: [development-planning, debugging-tools]
---

# Code Quality Verification Suite

Three complementary quality verification workflows for different stages of development.

## Sections

### Section A: Pre-Commit Verification (requesting-code-review)

Automated verification pipeline before code lands: static scans, baseline-aware quality gates, independent reviewer subagent, and auto-fix loop.

**Core principle:** No agent should verify its own work. Fresh context finds what you miss.

**When to use:** After implementing, before `git commit` or `git push`.

**Workflow:**
1. Get diff:
   - Git: `git diff --cached` (or `git diff`, `git diff HEAD~1`)
   - SVN: `svn diff` (working copy changes) or `svn diff -c REV` (specific revision). The user's P2040 project uses SVN — when `/review-svn` is invoked, always use SVN commands, not git.
2. Static security scan: grep added lines for secrets, SQL injection, shell injection, eval/exec
3. Baseline tests + linting: run tests BEFORE your changes (stash → run → pop), then run again with your changes. Only NEW failures block.
4. Self-review checklist
5. Independent reviewer subagent (delegate_task with ONLY the diff — no shared context)
6. Evaluate results: all passed → commit. Failures → auto-fix loop (max 2 cycles)
7. Commit with `[verified]` prefix

**Security scan patterns:** API keys, passwords, secrets, shell=True, eval(), exec(), pickle.loads(), SQL injection (`execute(f"...")`).

**Fail-closed:** If reviewer returns non-JSON or can't parse diff → fail.

**References:** `references/code-quality/actual-audit-case-bargainservice.md`

### Section B: Test-Driven Development

Write the test first. Watch it fail. Write minimal code to pass.

**The Iron Law:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.

**RED-GREEN-REFACTOR cycle:**
1. **RED:** Write one minimal failing test → verify it fails (`pytest test_file::test_name -v`)
2. **GREEN:** Write minimal code to pass → verify it passes
3. **REFACTOR:** Clean up while keeping tests green

**Key rules:**
- If you didn't watch the test fail, you don't know if it tests the right thing
- Delete code written before tests — start over
- GREEN allows cheating (hardcode, copy-paste) — fix in REFACTOR
- Test behavior, not implementation

**When subagent-driven, pass in context:** "Follow TDD: write failing test first, verify failure, write minimal passing code, verify pass, refactor."

### Section C: Deep Security Audit (codebase-security-audit)

Deep security review of LARGE EXISTING codebases (not diffs). Focuses on concurrency, TOCTOU, encryption, authorization, and business logic flaws. Produces structured severity-graded reports in Chinese.

**When to use:** Full module audit before deployment, after finding one bug (systematically search for more).

**Priority order for reading:**
1. Write operations (save/update/delete/cancel) — where corruption happens
2. Money/price operations — encryption, comparison, totals
3. State machine transitions — state checks before changes
4. Bulk operations — batch operations without proper isolation
5. Async/background operations — @Async, threadPool callbacks

**Checklist by severity:**
- 🔴 HIGH: TOCTOU races, missing row-level locks, non-atomic delete-then-reinsert, missing authz on writes, price manipulation without re-validation
- 🟡 MEDIUM: Encryption without fallback, commented-out validation, missing cache invalidation, no optimistic locking
- 🔵 LOW: Null-safety on .get(0), duplicate field assignments, inconsistent errors

**Output:** Save report to `doc/<Module>-安全审计报告.md` in Chinese with severity grading, source line references, and fix recommendations.

**References:** `references/code-quality/actual-audit-case-bargainservice.md`
