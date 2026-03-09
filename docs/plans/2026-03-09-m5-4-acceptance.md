# M5.4 Acceptance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M5.4` by verifying `M5.1`–`M5.3` against the TODO acceptance checklist, fixing only small gaps if discovered, and updating the restart handoff to begin `M6`.

**Architecture:** Treat this as an acceptance and evidence pass, not a feature sprint. Reuse the existing IM, schema, and routing tests as the source of truth, organize them into an acceptance matrix, apply minimal fixes only if verification finds real issues, and keep all deferred boundaries visible in the docs.

**Tech Stack:** Python 3.11, pytest, ruff, existing IM/schema/service tests

---

### Task 1: Build the M5 acceptance matrix

**Files:**
- Modify: `docs/progress.md`
- Reference: `docs/TODO.md`

**Step 1: Map requirements to evidence**

Create a concise acceptance matrix covering:
- Feishu channel
- Telegram channel
- unified message conversion
- minimal message routing
- current IM integration evidence

Use existing tests and commands only.

### Task 2: Run fresh acceptance verification

**Files:**
- No code changes required unless verification reveals gaps

**Step 1: Run focused acceptance commands**

Run:
- `.venv/bin/pytest -o addopts='' tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py tests/services/test_message_router.py -q`

**Step 2: Run full regression**

Run:
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`

### Task 3: Fix only minimal acceptance gaps if needed

**Files:**
- Modify only the smallest affected files if a real regression is found

**Step 1: Triage**

If all checks pass, do not add extra code.

If a small issue appears:
- write or adjust the failing test first if needed
- apply the smallest fix
- re-run the affected verification

### Task 4: Update handoff docs for M6

**Files:**
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
- Modify: `tasks/todo.md`

**Step 1: Mark M5 complete**

Record:
- `M5.4` complete
- `M5` complete overall
- exact command evidence
- deferred boundaries that remain out of scope
- next starting point becomes `M6.1.1`

### Task 5: Commit acceptance result

**Files:**
- Commit all approved `M5.4` acceptance updates

**Step 1: Commit**

Prepare a focused commit such as:
- `docs(acceptance): complete M5.4 milestone verification`
