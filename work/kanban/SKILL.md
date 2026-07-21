---
name: kanban
description: "Complete Kanban multi-agent workflow: orchestrator decomposition playbook, worker lifecycle & pitfalls, and Codex integration lane for bounded implementation tasks."
version: 1.0.0
author: Hermes Agent (consolidated)
license: MIT
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, workflow, codex, delegation]
    related_skills: []
---

# Kanban Multi-Agent Workflow

Umbrella skill covering the full Hermes Kanban system: orchestrator decomposition, worker lifecycle, and optional Codex implementation lane.

## Sections

- [Section 1: Orchestrator Playbook](#section-1-orchestrator-playbook) — decompose goals, discover profiles, create task graph, link dependencies
- [Section 2: Worker Lifecycle & Pitfalls](#section-2-worker-lifecycle--pitfalls) — workspace handling, status handoff, retry diagnostics, anti-patterns
- [Section 3: Codex Integration Lane](#section-3-codex-integration-lane) — isolated Codex implementation with Hermes reconciliation and safety gates

---

## Section 1: Orchestrator Playbook

### When to use the board

Create Kanban tasks when: multiple specialists needed, work should survive crashes, user may interject, parallel subtasks, review iteration, or audit trail matters. Otherwise use `delegate_task` or answer directly.

### Step 0: Discover profiles

```bash
hermes profile list
```

No default specialist roster exists. Must discover actual profiles before creating cards or the dispatcher silently drops unknown assignees.

### Step 1: Understand goal → sketch task graph

1. Extract independent lanes from request (look for "and", "also", "finally")
2. Map each lane to an existing profile
3. Create independent lanes as parallel cards with no parent links
4. Create synthesis/review/integration cards with `parents` links

Words like "also" and "finally" do NOT automatically imply dependency. Only link when one card literally needs another's output.

### Step 2: Create tasks with parent links

```python
t1 = kanban_create(title="research: ...", assignee="<profile>", tenant=...)
t2 = kanban_create(title="implement: ...", parents=[t1])
```

Create parent cards first, capture IDs, pass them as `parents` in children.

### Step 3: Complete & report

```python
kanban_complete(summary="decomposed into T1-T3", metadata={"task_graph": {...}})
```

### Anti-temptation rules

- Do NOT execute work yourself — route to specialists
- Do NOT invent profile names that don't exist
- Do NOT bundle independent lanes into one card
- Do NOT create child cards before parent cards exist (race window)
- Use `kanban_link(parent_id, child_id)` — parent first

### Goal-mode cards

```python
kanban_create(title="long task", assignee="worker", goal_mode=True, goal_max_turns=15)
```

Worker keeps running in same session with full context until done, blocked, or budget exhausted.

### Recovering stuck workers

When a worker crashes or hallucinates: Reclaim, Reassign to different profile, or change profile model. All available via dashboard or `hermes kanban reclaim/reassign`.

---

## Section 2: Worker Lifecycle & Pitfalls

The lifecycle (6 steps: orient → work → heartbeat → block/complete) is auto-injected into every worker's system prompt via `KANBAN_GUIDANCE`. This section covers deep detail.

### Workspace handling

| Kind | Behavior |
|------|----------|
| `scratch` | Fresh tmp dir, GC'd on archive |
| `dir:<path>` | Shared persistent — other runs read what you write |
| `worktree` | Git worktree — commit work here |

### Tenant isolation

If `$HERMES_TENANT` is set, prefix memory entries with tenant to avoid context leaks.

### Good summary shapes

**Coding:**
```python
kanban_complete(summary="rate limiter shipped — token bucket, 14 tests pass",
    metadata={"changed_files": [...], "tests_passed": 14})
```

**Research:**
```python
kanban_complete(summary="3 libraries reviewed; vLLM wins on throughput",
    metadata={"recommendation": "vLLM", "benchmarks": {...}})
```

**Review:**
```python
kanban_block(reason="review-required: needs eyes on the fallback choice")
kanban_comment(body="review-required handoff: " + json.dumps({...}))
```

### Heartbeats

Good: `"epoch 12/50, loss 0.31"`. Bad: `"still working"`. Skip for tasks under ~2 minutes.

### Block reasons that get answered

One sentence naming the specific decision needed. Leave context in comments:
```python
kanban_comment(body="Full context: ...")
kanban_block(reason="Rate limit key choice: IP or user_id?")
```

### Retry diagnostics

- `timed_out` — chunk or shorten work
- `crashed` — reduce memory
- `spawn_failed` — credential/config issue, block for human
- `reclaimed` — operator archived; check status before continuing

### Do NOT

- Call `delegate_task` as substitute for `kanban_create`
- Call `clarify` — use `kanban_block` instead
- Modify files outside `$HERMES_KANBAN_WORKSPACE`
- Complete tasks you didn't finish — block instead

### Claiming cards you created

Pass created ids in `created_cards` on `kanban_complete`. Phantom ids block completion.

### Pitfalls

- Task state can change between dispatch and startup — always `kanban_show` first
- Workspace may have stale artifacts — read comment thread
- `kanban_*` tools work across all backends; `hermes kanban` CLI does not

---

## Section 3: Codex Integration Lane

Use Codex CLI as an isolated implementation lane while Hermes keeps ownership of lifecycle, reconciliation, testing, and handoff.

### When to use

All must be true: coding/refactor task with clear acceptance criteria, bounded diff evaluable by Hermes, isolated git worktree available, Hermes can run relevant tests.

### Ownership rules

1. Hermes owns Kanban lifecycle — Codex never calls board tools
2. Hermes owns final acceptance — untrusted until reviewed
3. Hermes owns test execution — Codex test runs advisory only
4. Hermes owns safety — reject safety-boundary changes even if tests pass
5. Hermes owns cleanup — kill stuck processes, remove worktrees

### Worktree isolation

```bash
TASK_ID="${HERMES_KANBAN_TASK:-t_manual}"
SAFE_TASK="$(printf '%s' "$TASK_ID" | tr -cd '[:alnum:]_-')"
BRANCH="codex/${SAFE_TASK}/$(date -u +%Y%m%d%H%M%S)"
WORKTREE="/tmp/${SAFE_TASK}-codex-lane"
git worktree add -b "$BRANCH" "$WORKTREE" "$BASE"
```

### Mode: codex exec

```python
terminal(command="codex exec --full-auto '$(cat /tmp/codex_prompt.md)'",
    workdir=WORKTREE, background=True, pty=True, notify_on_complete=True)
```

### Prompt must include

- task_id, title, full acceptance criteria
- Repo/worktree/branch paths and allowed scope
- "Hermes owns Kanban lifecycle; Codex is input lane only"
- Required output: summary, files changed, tests run, known risks
- Prohibited: secrets access, board mutation, unrelated refactors
- PMB safety constraints (if applicable): no live orders, no market orders, no risk-gate weakening

### Reconciliation checklist

- [ ] Review `git diff --stat` — only expected files changed
- [ ] No secrets/credentials/unrelated artifacts
- [ ] Safety constraints preserved
- [ ] Hermes ran canonical tests independently
- [ ] Accepted commits applied to Hermes workspace

### Acceptance outcomes

`accepted`, `partial`, `rejected`, `timed_out` — with concrete reason.

### Metadata schema

```json
{"codex_lane": {"used": true, "mode": "exec", "result": "accepted", "tests_run": [...], "worktree": "/path"}}
```

**Templates:** `templates/pmb-codex-lane-prompt.md` — full Codex prompt template with PMB safety constraints.
