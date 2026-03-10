# M6.3.2 Connection Pool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M6.3.2` by making the async SQLAlchemy engine use explicit, valid connection-pool settings for the current SQLite-first repository setup.

**Architecture:** Centralize engine construction in `infra/db/database.py` so pool behavior is derived from the database URL instead of being implicit or duplicated. Keep in-memory SQLite on `StaticPool`, make file-backed SQLite use an explicit queue pool (`pool_size=20`, `max_overflow=10`), and reuse the same helper anywhere the repository needs to build an override engine.

**Tech Stack:** SQLAlchemy 2.0, SQLite, pytest

---

### Task 1: Lock the pool contract with failing tests

**Files:**
- Modify: `tests/infra/db/test_database.py`
- Reference: `infra/db/database.py`

**Step 1: Write the failing test**

Add:
- a test asserting the default repository database engine uses `AsyncAdaptedQueuePool`
- assertions that the default pool size is `20` and `max_overflow` is `10`
- a test asserting explicit in-memory SQLite URLs use `StaticPool`, including `sqlite+aiosqlite://`, `:memory:`, and `file:...mode=memory`

**Step 2: Run test to verify it fails**

Run:
- `.venv/bin/pytest tests/infra/db/test_database.py -q`

Expected: FAIL because the current module does not expose an explicit engine builder or explicit pool sizing.

### Task 2: Implement the minimal engine builder

**Files:**
- Modify: `infra/db/database.py`
- Modify: `scripts/init_db.py`

**Step 1: Write minimal implementation**

Add:
- a helper that parses the database URL and detects in-memory SQLite
- a helper that builds an async engine with either:
  - `poolclass=StaticPool` for in-memory SQLite
  - `pool_size=20` and `max_overflow=10` for non-memory URLs
- update the module-level `engine` to use that helper
- reuse the helper in `scripts/init_db.py` when a temporary override engine is needed

**Step 2: Run test to verify it passes**

Run:
- `.venv/bin/pytest tests/infra/db/test_database.py -q`

Expected: PASS

### Task 3: Run milestone verification and update handoff

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest tests/infra/db/test_database.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

Expected: PASS

**Step 2: Update restart-oriented docs**

Record:
- `M6.3.2` completion summary
- exact verification evidence
- the SQLite-specific pool boundary
- next starting point after `M6.3.2`

### Task 4: Commit the milestone

**Files:**
- Commit all approved `M6.3.2` changes

**Step 1: Commit**

Prepare a focused commit such as:
- `perf(db): complete M6.3.2 connection pool`
