# M4.1.3 Invite Code System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M4.1.3` by adding a minimal invite-code system that works with the current in-memory auth stack: admins can create and inspect invite codes, and registration can optionally consume a valid invite to assign a non-default role.

**Architecture:** Add the canonical `InviteCode` SQLAlchemy model under `domain/models/`, but keep the runtime behavior in `services/auth.py` for now so registration remains compatible with the current in-memory `AuthService`. Expose admin invite management APIs from `app/routes/users.py`, and extend `POST /auth/register` to accept an optional `invite_code`. Each invite is single-use (`used_by` / `used_at`), may expire, and is only consumed after username uniqueness succeeds.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, SQLAlchemy ORM, pytest

---

### Task 1: Define invite behavior with failing tests

**Files:**
- Modify: `tests/domain/models/test_models.py`
- Modify: `tests/services/test_auth_service.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `domain/models/invite_code.py`
- Reference: `services/auth.py`
- Reference: `app/routes/auth.py`
- Reference: `app/routes/users.py`

**Step 1: Write failing tests**

Cover:
- `InviteCode` model fields and metadata export
- admin create/list invite endpoints
- non-admin / unauthenticated invite admin routes returning `403` / `401`
- successful registration with a valid invite inheriting invite role
- invalid / used / expired invite registration returning `400`
- invite consumption updating `used_by` / `used_at`

**Step 2: Run focused tests to verify RED**

Run: `.venv/bin/pytest -o addopts='' tests/domain/models/test_models.py tests/services/test_auth_service.py tests/app/routes/test_api_routes.py -q`

Expected: FAIL because invite model, invite service methods, and invite routes/register integration do not exist yet.

### Task 2: Implement model, service, and routes

**Files:**
- Create: `domain/models/invite_code.py`
- Modify: `domain/models/__init__.py`
- Modify: `domain/schemas.py`
- Modify: `services/auth.py`
- Modify: `app/routes/auth.py`
- Modify: `app/routes/users.py`

**Step 1: Add canonical model and schemas**

Add the `InviteCode` ORM model plus request/response schemas for admin invite management.

**Step 2: Extend in-memory auth service**

Add invite creation/listing/lookup/consumption helpers and integrate optional `invite_code` handling into `register_user()`.

Rules:
- invite code may define the new user's role
- expired or already-used codes are rejected
- duplicate usernames do not consume the invite

**Step 3: Add admin invite routes and register integration**

Expose:
- `GET /admin/invites`
- `POST /admin/invites`

Extend:
- `POST /auth/register`

Keep open registration behavior when no invite code is supplied, because registration mode toggles are not part of `M4.1.3`.

**Step 4: Run focused tests to verify GREEN**

Run: `.venv/bin/pytest -o addopts='' tests/domain/models/test_models.py tests/services/test_auth_service.py tests/app/routes/test_api_routes.py -q`

Expected: PASS.

### Task 3: Regressions, docs, and commit

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest -o addopts='' tests/domain/models/test_models.py tests/services/test_auth_service.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update docs**

Mark `M4.1.3` complete, record exact verification evidence, and advance the next start point to `M4.2.1`.

**Step 3: Commit**

Commit with a focused `feat(user): ...` message after the workspace is cleanly verified.
