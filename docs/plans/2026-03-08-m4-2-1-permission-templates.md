# M4.2.1 Permission Templates Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M4.2.1` by defining deterministic role-based permission templates for `owner` / `admin` / `member`, with minimal helper functions that the next step (`M4.2.2`) can reuse directly.

**Architecture:** Keep this step intentionally small: add a new `domain/permissions.py` module that owns the static permission contract and exposes pure helper functions. Do not use `user.permissions` custom overrides yet, and do not introduce DB-backed authorization. Unknown roles, resources, or actions should deny by default.

**Tech Stack:** Python 3.11, pure Python data structures, pytest

---

### Task 1: Define permission behavior with failing tests

**Files:**
- Create: `tests/domain/test_permissions.py`
- Reference: `domain/permissions.py`

**Step 1: Write failing tests**

Cover:
- `PERMISSION_TEMPLATES` containing `owner`, `admin`, `member`
- expected permissions for representative resource/action pairs
- `get_permissions_for_role()` returning empty mappings for unknown roles
- `has_permission()` allowing known template actions and denying unknown role/resource/action inputs

**Step 2: Run focused tests to verify RED**

Run: `.venv/bin/pytest -o addopts='' tests/domain/test_permissions.py -q`

Expected: FAIL because `domain/permissions.py` does not exist yet.

### Task 2: Implement the permission template module

**Files:**
- Create: `domain/permissions.py`

**Step 1: Add static templates**

Define `PERMISSION_TEMPLATES` exactly for:
- `owner`
- `admin`
- `member`

**Step 2: Add pure helper functions**

Implement:
- `get_permissions_for_role(role: str) -> dict[str, tuple[str, ...]]`
- `has_permission(role: str, resource: str, action: str) -> bool`

Ensure callers cannot mutate the canonical templates through returned values.

**Step 3: Run focused tests to verify GREEN**

Run: `.venv/bin/pytest -o addopts='' tests/domain/test_permissions.py -q`

Expected: PASS.

### Task 3: Regressions, docs, and commit

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest -o addopts='' tests/domain/test_permissions.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update docs**

Mark `M4.2.1` complete, record exact verification evidence, and advance the next start point to `M4.2.2`.

**Step 3: Commit**

Commit with a focused `feat(auth): ...` message after the workspace is cleanly verified.
