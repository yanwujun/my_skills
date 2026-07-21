---
name: development-planning
description: "Plan-driven development workflow: writing implementation plans, executing experiments (spikes), planning mode, and delegating via subagents. Covers the full plan→spike→execute cycle."
version: 1.0.0
author: Hermes Agent (consolidated)
license: MIT
metadata:
  hermes:
    tags: [planning, spike, implementation, subagent, development-workflow]
    related_skills: [systematic-debugging, test-driven-development]
---

# Development Planning & Execution

Umbrella for the plan-driven development workflow: plan, spike, writing-plans, and subagent-driven-development.

## Sections

### Section A: Plan Mode (`.hermes/plans/`)

Write structured plans to `.hermes/plans/` for tracking complex multi-step tasks.

**Use when:** the task has 5+ steps, spans multiple files, involves design decisions, or the user explicitly asks for a plan first.

**Format:**
```markdown
# Plan: Descriptive title

## Overview
- **Goal:** what we're building
- **Files involved:** src/a.py, src/b.py
- **Estimated steps:** N

## Steps
1. **Step title** — description. Tool: terminal/read_file/patch/write_file
2. **Step title** — description.
```

**Save:** write to `.hermes/plans/<topic-slug>.md` using write_file.

**Rules:**
- Do NOT execute any step while in plan mode
- After writing, show the plan to the user for approval
- Only proceed when the user says "go ahead" or similar
- Mark steps as [x] completed as you execute
- Update the plan file on significant progress

---

### Section B: Spike (Experimental Validation)

Run throwaway experiments to validate an idea before committing to full implementation.

**Use when:** you need to test an approach, verify a hypothesis, explore an API, or benchmark an option.

**Process:**
1. Create a temp directory: `SPIKE_DIR=$(mktemp -d)`
2. Write a minimal experiment script
3. Run it and capture output
4. Report findings to the user
5. Clean up: `rm -rf "$SPIKE_DIR"`

**Key rule:** Do not commit spike code. Spikes are throwaway by nature. The output (findings, decisions, benchmarks) is the deliverable, not the code itself.

---

### Section C: Writing Implementation Plans

Create detailed, actionable implementation plans before writing code.

**Output:** A markdown plan with bite-sized tasks, file paths, and exact code snippets where helpful.

**Structure:**
```
# Implementation Plan: [Title]

## Prerequisites / Context
[What exists already, relevant constraints]

## Tasks (in order)
### Task 1: [Short name]
- **Files:** path/to/file.py:42-60
- **What:** description
- **Code sketch:** ```python ... ``` (optional)

### Task 2: [Short name]
...
```

**When to write a plan:**
- User asks "how should I implement X"
- Task spans 3+ files or involves architecture decisions
- Before using `subagent-driven-development` to execute

---

### Section D: Subagent-Driven Development

Execute a pre-written plan by delegating each task to a subagent via `delegate_task`.

**When to use:** The plan is written, approved, and each task is self-contained enough for a subagent.

**Workflow:**
1. Read the plan file from `.hermes/plans/`
2. For each task, spawn a subagent:
```python
delegate_task(
    goal="Task N: [task name]",
    context=f"Working in {project_dir}\nPlan context: ...",
    toolsets=["terminal", "file"],
)
```
3. Review each subagent's summary before proceeding to the next task
4. After all tasks complete, run verification
5. Mark plan steps as [x] complete

**Review rules:** Each subagent's output must be reviewed before advancing. Two-stage review:
- Stage 1: Subagent executes → returns summary
- Stage 2: Parent reviews output, then proceeds to next task
