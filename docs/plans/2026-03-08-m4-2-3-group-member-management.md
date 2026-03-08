# M4.2.3 Group Member Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M4.2.3` by adding a formal `GroupMember` contract, an in-memory member-management service, and the minimal `/groups/{group_id}/members` API needed to manage `owner` / `admin` / `member` roles.

**Architecture:** Keep the persistence contract and runtime behavior intentionally split. The SQLAlchemy model defines the future DB shape, while the current runtime uses a lightweight in-memory service that fits the existing in-memory `AuthService`. Reuse `require_permission("groups", "...")` and add route-level member/owner checks without expanding the wider RBAC model.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy ORM models, pytest

---

### Task 1: Write failing model and schema tests

**Files:**
- Modify: `tests/domain/models/test_models.py`
- Reference: `domain/models/__init__.py`
- Reference: `domain/schemas.py`

**Step 1: Write failing tests**

Add assertions for:
- `GroupMember.__tablename__ == "group_members"`
- shared metadata includes `group_members`
- `group_jid`, `user_id`, `role`, `joined_at` columns exist
- `role` is non-nullable
- `joined_at` is non-nullable and has a default

**Step 2: Run focused tests to verify RED**

Run: `.venv/bin/pytest -o addopts='' tests/domain/models/test_models.py -q`

Expected: FAIL because `GroupMember` is not defined/exported yet.

### Task 2: Implement the formal group member contract

**Files:**
- Create: `domain/models/group_member.py`
- Modify: `domain/models/__init__.py`
- Modify: `domain/schemas.py`

**Step 1: Add model**

Implement `GroupMember` with:
- `__tablename__ = "group_members"`
- composite primary key: `group_jid`, `user_id`
- `role` string field
- `joined_at` datetime field with `datetime.utcnow` default

**Step 2: Add schemas**

Add:
- `CreateGroupMemberRequest`
- `GroupMemberResponse`
- `GroupMemberListResponse`

Expose `group_id` in the API schema while mapping from the model/service `group_jid` value.

**Step 3: Re-run focused tests to verify GREEN**

Run: `.venv/bin/pytest -o addopts='' tests/domain/models/test_models.py -q`

Expected: PASS.

### Task 3: Write failing service tests

**Files:**
- Create: `tests/services/test_group_member_service.py`
- Reference: `services/group_member_service.py`

**Step 1: Write failing tests**

Add coverage for:
- adding a member with default role
- updating an existing member role while preserving `joined_at`
- listing members in deterministic order
- rejecting invalid role values
- removing existing and missing members
- resolving `get_member_role()`

**Step 2: Run focused tests to verify RED**

Run: `.venv/bin/pytest -o addopts='' tests/services/test_group_member_service.py -q`

Expected: FAIL because the service module does not exist yet.

### Task 4: Implement the in-memory group member service

**Files:**
- Create: `services/group_member_service.py`

**Step 1: Add service**

Implement an in-memory singleton service with:
- `list_members(group_id)`
- `add_member(group_id, user_id, role="member")`
- `remove_member(group_id, user_id)`
- `get_member(group_id, user_id)`
- `get_member_role(group_id, user_id)`
- `reset()`

Rules:
- valid roles are `owner`, `admin`, `member`
- re-adding an existing member updates role but keeps original `joined_at`
- list output is sorted by `user_id`

**Step 2: Re-run focused tests to verify GREEN**

Run: `.venv/bin/pytest -o addopts='' tests/services/test_group_member_service.py -q`

Expected: PASS.

### Task 5: Write failing API tests for member routes

**Files:**
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `app/routes/groups.py`

**Step 1: Add failing API coverage**

Add tests for:
- unauthenticated member endpoints return `401`
- a group member can list members
- a non-member cannot list members
- an owner can add a member
- an owner can remove a member
- a group admin/member cannot add or remove members
- invalid role payload returns `400`
- removing a missing member returns `404`

Use the existing in-memory `auth_service` for users and the new group member service for membership setup.

**Step 2: Run focused tests to verify RED**

Run: `.venv/bin/pytest -o addopts='' tests/app/routes/test_api_routes.py -q`

Expected: FAIL because the routes are not wired yet.

### Task 6: Implement minimal group member API

**Files:**
- Modify: `app/routes/groups.py`

**Step 1: Add route dependencies and helpers**

Implement helpers that:
- verify current user is a group member for reads
- verify current user is the group owner for writes
- map service records to API responses

**Step 2: Add routes**

Implement:
- `GET /groups/{group_id}/members`
- `POST /groups/{group_id}/members`
- `DELETE /groups/{group_id}/members/{user_id}`

Behavior:
- reuse `require_permission("groups", "read"/"write")`
- return `403` for non-member / non-owner access
- return `400` for invalid role or owner self-removal
- return `404` for missing member removal

**Step 3: Re-run focused API tests to verify GREEN**

Run: `.venv/bin/pytest -o addopts='' tests/app/routes/test_api_routes.py -q`

Expected: PASS.

### Task 7: Regression verification, docs, and commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest -o addopts='' tests/domain/models/test_models.py tests/services/test_group_member_service.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update docs**

Record:
- `M4.2.3` complete
- exact verification evidence
- current starting point advanced to the next TODO item
- the service is intentionally in-memory pending broader DB-backed group/user migration
- preserve the existing M3/M4 deferred-risk notes

**Step 3: Commit**

Prepare a focused commit such as:
- `feat(groups): complete M4.2.3 group member management`
