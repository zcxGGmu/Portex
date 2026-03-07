# M4.1.2 User Management API Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M4.1.2` by adding admin-only user listing and update APIs without breaking the current register/login/`/users/me` flow.

**Architecture:** Keep the current in-memory `AuthService` as the source of truth for this phase so the existing auth middleware and tests remain stable. Add a reusable `require_role()` dependency in `app/middleware/auth.py`, extend `services/auth.py` with deterministic list/update operations for `AuthUser`, and expose `/admin/users` + `/admin/users/{user_id}` from `app/routes/users.py` while preserving `/users/me`.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, dataclasses, pytest

---

### Task 1: Define admin API behavior with failing tests

**Files:**
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `tests/app/middleware/test_auth_middleware.py`
- Modify: `tests/services/test_auth_service.py`
- Reference: `app/routes/users.py`
- Reference: `app/middleware/auth.py`
- Reference: `services/auth.py`

**Step 1: Write failing tests**

Cover:
- `/admin/users` requiring authentication
- non-admin callers receiving `403`
- admin callers listing all users through a stable response shape
- admin callers updating role/status/profile/state fields
- updating a missing user returning `404`
- service-level coverage for deterministic list/update behavior

**Step 2: Run focused tests to verify RED**

Run: `.venv/bin/pytest -o addopts='' tests/services/test_auth_service.py tests/app/middleware/test_auth_middleware.py tests/app/routes/test_api_routes.py -q`

Expected: FAIL because role dependency, list/update service methods, and admin routes do not exist yet.

### Task 2: Implement role checks, service methods, and routes

**Files:**
- Modify: `app/middleware/auth.py`
- Modify: `services/auth.py`
- Modify: `domain/schemas.py`
- Modify: `app/routes/users.py`
- Modify: `app/main.py`

**Step 1: Add reusable role dependency**

Implement `require_role(role: str)` on top of `get_current_user()` so admin endpoints can share one authorization primitive.

**Step 2: Extend the in-memory auth service**

Add:
- deterministic `list_users()`
- partial `update_user()` over the admin-managed fields
- a small not-found error for missing `user_id`
- optional registration role override for admin-focused tests

Keep `AuthUser` immutable and use dataclass replacement semantics for updates.

**Step 3: Add admin schemas and routes**

Add:
- `AdminUserListResponse`
- `UpdateUserRequest`

Expose:
- `GET /admin/users`
- `PATCH /admin/users/{user_id}`

Keep `/users/me` unchanged for callers.

**Step 4: Run focused tests to verify GREEN**

Run: `.venv/bin/pytest -o addopts='' tests/services/test_auth_service.py tests/app/middleware/test_auth_middleware.py tests/app/routes/test_api_routes.py -q`

Expected: PASS.

### Task 3: Regressions, docs, and commit

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest -o addopts='' tests/services/test_auth_service.py tests/app/middleware/test_auth_middleware.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update docs**

Mark `M4.1.2` complete, record exact verification evidence, and advance the next start point to `M4.1.3`.

**Step 3: Commit**

Commit with a focused `feat(user): ...` message after the workspace is cleanly verified.
