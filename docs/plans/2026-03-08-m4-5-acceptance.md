# M4.5 Acceptance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M4.5` by verifying `M4.1`–`M4.4` end-to-end against the TODO acceptance checklist, fixing only small gaps if discovered, and updating the restart handoff to begin `M5`.

**Architecture:** Treat this as an acceptance and evidence pass, not a feature sprint. Reuse the existing test suite as the source of truth, organize it into an acceptance matrix, apply minimal fixes only if verification finds real issues, and keep all deferred boundaries visible in the docs.

**Tech Stack:** Python 3.11, pytest, ruff, npm lint/build, existing service/runner tests

---

### Task 1: Build the M4 acceptance matrix

**Files:**
- Modify: `docs/progress.md`
- Reference: `docs/TODO.md`

**Step 1: Map requirements to evidence**

Create a concise acceptance matrix covering:
- user system
- RBAC / group members
- task system
- memory system
- multi-user isolation evidence

Use existing tests and commands only.

### Task 2: Run fresh acceptance verification

**Files:**
- No code changes required unless verification reveals gaps

**Step 1: Run focused acceptance commands**

Run:
- `.venv/bin/pytest -o addopts='' tests/services/test_auth_service.py tests/app/routes/test_api_routes.py tests/domain/test_permissions.py tests/services/test_group_member_service.py tests/services/test_scheduler.py tests/services/test_task_service.py tests/services/test_task_log_service.py tests/services/test_memory_service.py tests/container/agent_runner -q`

**Step 2: Run full regression**

Run:
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

### Task 3: Fix only minimal acceptance gaps if needed

**Files:**
- Modify only the smallest affected files if a real regression is found

**Step 1: Triage**

If all checks pass, do not add extra code.

If a small issue appears:
- write/adjust the failing test first if needed
- apply the smallest fix
- re-run the affected verification

### Task 4: Update handoff docs for M5

**Files:**
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`

**Step 1: Mark M4 complete**

Record:
- `M4.5` complete
- `M4` complete overall
- exact command evidence
- deferred boundaries that remain out of scope
- next starting point becomes `M5.1.1`

### Task 5: Commit acceptance result

**Files:**
- Commit all approved `M4.5` acceptance updates

**Step 1: Commit**

Prepare a focused commit such as:
- `docs(acceptance): complete M4.5 milestone verification`
