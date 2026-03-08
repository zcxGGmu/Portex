# M4.2.2 Permission Dependency Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M4.2.2` by adding `require_permission(resource, action)` to the FastAPI auth middleware and wiring the existing admin user/invite routes to the static RBAC templates defined in `domain/permissions.py`.

**Architecture:** Keep the scope intentionally narrow. Authorization remains purely role-template based (`owner` / `admin` / `member`). Reuse `get_current_user()` and `domain.permissions.has_permission()`; do not introduce `user.permissions`, database authorization, or new RBAC resources.

**Tech Stack:** Python 3.11, FastAPI dependency injection, pytest

---

### Task 1: Write failing middleware permission tests

**Files:**
- Modify: `tests/app/middleware/test_auth_middleware.py`
- Reference: `app/middleware/auth.py`
- Reference: `domain/permissions.py`

**Step 1: Write failing tests**

Add coverage for:
- `require_permission("users", "read")` allowing `admin`
- `require_permission("users", "write")` allowing `owner`
- `require_permission("users", "read")` denying `member`
- `require_permission("users", "read")` denying unknown role

**Step 2: Run focused tests to verify RED**

Run: `.venv/bin/pytest -o addopts='' tests/app/middleware/test_auth_middleware.py -q`

Expected: FAIL because `require_permission` does not exist yet.

### Task 2: Implement middleware permission dependency

**Files:**
- Modify: `app/middleware/auth.py`
- Modify: `app/middleware/__init__.py`

**Step 1: Add dependency**

Implement `require_permission(resource: str, action: str)` beside `require_role()`.

Behavior:
- depends on `get_current_user()`
- evaluates `has_permission(current_user.role, resource, action)`
- raises `403` with `detail="permission denied"` when denied
- returns `current_user` when allowed

**Step 2: Export the dependency**

Update module exports so package-level imports can reuse `require_permission` consistently.

**Step 3: Run focused tests to verify GREEN**

Run: `.venv/bin/pytest -o addopts='' tests/app/middleware/test_auth_middleware.py -q`

Expected: PASS.

### Task 3: Write failing API tests for route wiring

**Files:**
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `app/routes/users.py`

**Step 1: Add targeted API tests**

Add coverage for:
- `owner` can access one migrated `/admin/*` route
- unknown role is forbidden from one migrated `/admin/*` route

Keep the existing `401`, `403`, and `admin` success tests intact.

**Step 2: Run focused tests to verify RED if route wiring is unchanged**

Run:
- `.venv/bin/pytest -o addopts='' tests/app/routes/test_api_routes.py -q`

Expected: owner coverage fails before route migration.

### Task 4: Migrate routes to permission checks

**Files:**
- Modify: `app/routes/users.py`

**Step 1: Replace role guards**

Update the current `/admin/users` and `/admin/invites` dependencies:
- `GET /admin/users` -> `require_permission("users", "read")`
- `PATCH /admin/users/{user_id}` -> `require_permission("users", "write")`
- `GET /admin/invites` -> `require_permission("users", "read")`
- `POST /admin/invites` -> `require_permission("users", "write")`

**Step 2: Re-run focused API tests**

Run:
- `.venv/bin/pytest -o addopts='' tests/app/routes/test_api_routes.py -q`

Expected: PASS.

### Task 5: Regression verification and docs

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest -o addopts='' tests/app/middleware/test_auth_middleware.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest -o addopts='' tests/domain/test_permissions.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update progress**

Record:
- `M4.2.2` complete
- exact verification evidence
- current starting point advanced to `M4.2.3`
- note that invite routes currently reuse the `users` resource as the minimal bridge until finer-grained RBAC exists
- preserve existing M3 risk notes and deferred custom-permission note

**Step 3: Commit**

Prepare a focused commit message such as `feat(auth): complete M4.2.2 permission dependency` after verification succeeds.
