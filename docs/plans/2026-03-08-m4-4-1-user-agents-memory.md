# M4.4.1 User `AGENTS.md` Memory Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M4.4.1` by replacing the placeholder memory service with a file-backed user-global memory manager that stores `AGENTS.md` per user.

**Architecture:** Keep the implementation service-only. Persist memory files under `data/memory/user-global/{user_id}/AGENTS.md`, allow the base data directory to be injected for tests, and defer daily memory, search, APIs, and runner integration.

**Tech Stack:** Python 3.11, pathlib, asyncio, pytest

---

### Task 1: Write failing memory service tests

**Files:**
- Create: `tests/services/test_memory_service.py`

**Step 1: Add failing tests**

Cover:
- missing user file returns empty string
- update creates the expected `AGENTS.md` path
- update then get returns stored content
- update overwrites prior content
- different users remain isolated

**Step 2: Run focused tests to verify RED**

Run:
- `.venv/bin/pytest -o addopts='' tests/services/test_memory_service.py -q`

Expected: FAIL because the placeholder service does not implement the async file-backed API.

### Task 2: Implement minimal file-backed memory service

**Files:**
- Modify: `services/memory.py`

**Step 1: Replace placeholder storage**

Implement:
- injected `data_dir`
- path helper for `data/memory/user-global/{user_id}/AGENTS.md`
- async read returning `""` when missing
- async overwrite write creating parent directories

**Step 2: Re-run focused tests to verify GREEN**

Run:
- `.venv/bin/pytest -o addopts='' tests/services/test_memory_service.py -q`

Expected: PASS.

### Task 3: Regression verification, docs, and commit

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest -o addopts='' tests/services/test_memory_service.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update docs**

Record:
- `M4.4.1` complete
- user-global memory now uses `AGENTS.md`
- current starting point advances to `M4.4.2`

**Step 3: Commit**

Prepare a focused commit such as:
- `feat(memory): complete M4.4.1 user agents memory`
