# M4.4.2 Daily Memory Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M4.4.2` by adding a minimal daily memory append API to the existing file-backed memory service.

**Architecture:** Keep memory file-backed and service-only. Reuse the injected data root, add an injectable “today” provider for deterministic tests, and append daily memory into `data/memory/{group_folder}/YYYY-MM-DD.md`.

**Tech Stack:** Python 3.11, pathlib, asyncio, datetime, pytest

---

### Task 1: Write failing daily-memory tests

**Files:**
- Modify: `tests/services/test_memory_service.py`

**Step 1: Add failing tests**

Cover:
- `append_daily_memory()` creates the expected dated file
- repeated appends preserve prior content order
- different groups remain isolated
- user-global `AGENTS.md` path is unaffected by daily memory writes

**Step 2: Run focused tests to verify RED**

Run:
- `.venv/bin/pytest -o addopts='' tests/services/test_memory_service.py -q`

Expected: FAIL because daily append support does not exist yet.

### Task 2: Implement minimal daily memory support

**Files:**
- Modify: `services/memory.py`

**Step 1: Add today provider and path helper**

Implement a helper for `data/memory/{group_folder}/YYYY-MM-DD.md`.

**Step 2: Add append method**

Implement `append_daily_memory(group_folder, content)` to create the directory and append newline-delimited content.

**Step 3: Re-run focused tests to verify GREEN**

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
- `M4.4.2` complete
- daily memory path contract
- current starting point advances to `M4.4.3`

**Step 3: Commit**

Prepare a focused commit such as:
- `feat(memory): complete M4.4.2 daily memory`
