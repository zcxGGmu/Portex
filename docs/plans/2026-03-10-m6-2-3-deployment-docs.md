# M6.2.3 Deployment Docs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M6.2.3` by adding a deployment guide for the current verified local process setup, while clearly labeling Docker Compose as an unverified draft.

**Architecture:** Treat documentation as three layers: `README.md` for project entry, FastAPI `/docs` for HTTP API reference, and a dedicated deployment guide for operators. Before publishing the deployment guide, fix the inaccurate invite `expires_at` API-doc wording so adjacent docs do not contradict current behavior.

**Tech Stack:** Markdown, FastAPI/Pydantic docs metadata, pytest

---

### Task 1: Lock the invite `expires_at` doc correction with a failing test

**Files:**
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `domain/schemas.py`
- Reference: `app/routes/users.py`

**Step 1: Write the failing test**

Add a focused assertion that the invite schema documents `expires_at` as a timezone-aware timestamp without promising UTC normalization.

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/app/routes/test_api_routes.py -q`

Expected: FAIL because the current schema description incorrectly promises UTC behavior.

### Task 2: Fix the documented database-init command with TDD

**Files:**
- Modify: `tests/scripts/test_init_db.py`
- Modify: `scripts/init_db.py`

**Step 1: Write the failing test**

Add a subprocess-level test that runs `scripts/init_db.py` from the repository root with the current Python interpreter and a temporary SQLite database URL.

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/scripts/test_init_db.py -q`

Expected: FAIL because the current script cannot import the repository packages when executed directly.

**Step 3: Write minimal implementation**

Adjust `scripts/init_db.py` to add the repository root to `sys.path` before importing project modules.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/scripts/test_init_db.py -q`

Expected: PASS

### Task 3: Apply the minimal API-doc wording fix

**Files:**
- Modify: `domain/schemas.py`

**Step 1: Write minimal implementation**

Adjust the `CreateInviteCodeRequest` and `InviteCodeResponse` `expires_at` field descriptions so they match the current behavior: timezone-aware datetime values are accepted and preserved; the public docs do not promise UTC normalization.

**Step 2: Run test to verify it passes**

Run: `.venv/bin/pytest tests/app/routes/test_api_routes.py -q`

Expected: PASS

### Task 4: Write the deployment guide and link it from the repository entrypoint

**Files:**
- Create: `docs/deployment.md`
- Modify: `README.md`

**Step 1: Write the deployment guide**

Add:
- verified local process deployment steps
- prerequisites and environment variables
- verification checklist
- data/persistence notes
- a clearly marked unverified Docker Compose draft
- current deployment boundaries

**Step 2: Update the README**

Add a concise link to the deployment guide in the docs section and refresh the current-status wording to match the new milestone state.

### Task 5: Run milestone verification and update handoff

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/scripts/test_init_db.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`
- `.venv/bin/python scripts/init_db.py`
- backend smoke check against `/health`
- frontend preview smoke check against `/`

Expected: PASS

**Step 2: Update restart-oriented docs**

Record:
- `M6.2.3` completion summary
- exact verification evidence
- current deployment boundaries, especially the unverified Docker draft
- next starting point after `M6.2.3`

### Task 6: Commit the milestone

**Files:**
- Commit all approved `M6.2.3` changes

**Step 1: Commit**

Prepare a focused commit such as:
- `docs(deploy): complete M6.2.3 deployment guide`
