# M6.3.3 User Memory Cache Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M6.3.3` by adding a process-local read cache for user-global `AGENTS.md` memory reads without broadening the cache layer beyond this single service.

**Architecture:** Keep the cache entirely inside `MemoryService` as a private `dict[user_id, content]`. `get_user_memory()` becomes a read-through cache, `update_user_memory()` becomes a write-through cache update, and the rest of the memory service stays file-backed and uncached.

**Tech Stack:** Python 3.12, asyncio, pathlib, pytest

---

### Task 1: Lock cache behavior with failing tests

**Files:**
- Modify: `tests/services/test_memory_service.py`
- Reference: `services/memory.py`

**Step 1: Write the failing test**

Add focused tests that prove:
- repeated reads for a missing `AGENTS.md` path return `""` without checking `.exists()` twice
- repeated reads for an existing `AGENTS.md` file read the file once and then serve from cache
- `update_user_memory()` refreshes the cache so the next read returns the new content

Use monkeypatching around the service instance to count filesystem calls rather than relying on timing.

**Step 2: Run test to verify it fails**

Run:
- `.venv/bin/pytest tests/services/test_memory_service.py -q`

Expected: FAIL because `MemoryService` currently has no cache and re-checks the filesystem on every read.

### Task 2: Implement the minimal user-memory cache

**Files:**
- Modify: `services/memory.py`

**Step 1: Write minimal implementation**

Add:
- a private `_user_memory_cache: dict[str, str]`
- read-through behavior in `get_user_memory(user_id)`
- write-through cache synchronization in `update_user_memory(user_id, content)`

Keep:
- `append_daily_memory()` unchanged
- `search_memory()` unchanged
- exception behavior unchanged

**Step 2: Run test to verify it passes**

Run:
- `.venv/bin/pytest tests/services/test_memory_service.py -q`

Expected: PASS

### Task 3: Run milestone verification and update handoff

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest tests/services/test_memory_service.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

Expected: PASS

**Step 2: Update restart-oriented docs**

Record:
- `M6.3.3` completion summary
- exact verification evidence
- the single-process cache boundary
- next starting point after `M6.3.3`

### Task 4: Commit the milestone

**Files:**
- Commit all approved `M6.3.3` changes

**Step 1: Commit**

Prepare a focused commit such as:
- `perf(memory): complete M6.3.3 user memory cache`
