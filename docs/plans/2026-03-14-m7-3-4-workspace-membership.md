# M7.3.4 Workspace Membership Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the current placeholder group-member slice into a DB-backed workspace membership model that controls shared-workspace visibility and access across groups, messages, and execution-status reads.

**Architecture:** Keep `registered_groups` as the canonical workspace and IM endpoint registry, but move `group_members` to a persistent `group_folder`-keyed source of truth. Add membership-aware access checks on top of the existing workspace topology so non-home `web:*` workspaces can be shared without changing `M7.3.3` IM ingress behavior or swallowing `M7.3.6` workspace-management APIs.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy async sessions, SQLite, pytest

---

### Task 1: Lock The Persistent Workspace-Membership Table Contract

**Files:**
- Modify: `domain/models/group_member.py`
- Modify: `tests/domain/models/test_models.py`
- Modify: `scripts/init_db.py`
- Modify: `tests/scripts/test_init_db.py`

**Step 1: Write the failing tests**

Add tests that prove:

- `GroupMember` uses `group_folder` instead of `group_jid`
- `GroupMember` includes nullable `added_by`
- `scripts/init_db.py` backfills legacy `group_members` tables that only have `group_jid`
- the upgraded SQLite table still preserves the existing shared metadata contract

```python
def test_group_member_model_uses_group_folder_identity() -> None:
    columns = GroupMember.__table__.columns.keys()
    assert "group_folder" in columns
    assert "group_jid" not in columns
    assert "added_by" in columns
```

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py -q
```

Expected: FAIL because `GroupMember` still exposes `group_jid` only and `init_db` does not heal legacy `group_members` tables.

**Step 3: Write the minimal implementation**

Implement:

- `group_folder` primary-key column on `GroupMember`
- `added_by` column on `GroupMember`
- `scripts/init_db.py` compatibility backfill for legacy `group_members`

Keep the migration path minimal and SQLite-friendly. Do not add a standalone migration framework.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add domain/models/group_member.py tests/domain/models/test_models.py scripts/init_db.py tests/scripts/test_init_db.py
git commit -m "feat(groups): persist workspace membership schema"
```

### Task 2: Replace The In-Memory Member Store With A DB-Backed Membership Service

**Files:**
- Modify: `services/group_member_service.py`
- Modify: `tests/services/test_group_member_service.py`
- Modify: `app/routes/groups.py`

**Step 1: Write the failing tests**

Add service tests that prove:

- members are persisted by `group_folder`
- owner/member roles round-trip through the DB
- re-adding a member preserves `joined_at`
- self-removal can be expressed without deleting the owner
- duplicate owner demotion/removal is rejected explicitly

```python
@pytest.mark.asyncio
async def test_add_member_persists_by_group_folder(db_session: AsyncSession) -> None:
    service = GroupMemberService(db=db_session)
    member = await service.add_member("project-alpha", "user-1")
    assert member.group_folder == "project-alpha"
```

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/services/test_group_member_service.py -q
```

Expected: FAIL because `GroupMemberService` is still an in-memory singleton with synchronous `group_id`-based methods.

**Step 3: Write the minimal implementation**

Implement:

- async `GroupMemberService(db: AsyncSession)`
- DB-backed CRUD by `group_folder`
- deterministic list ordering
- owner-protection helpers needed by route code
- a route dependency in `app/routes/groups.py` to construct the service from `get_db`

Keep the service narrow. Do not add search APIs or workspace creation here.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/services/test_group_member_service.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add services/group_member_service.py tests/services/test_group_member_service.py app/routes/groups.py
git commit -m "feat(groups): add db-backed workspace membership service"
```

### Task 3: Add Membership-Aware Workspace Access Helpers

**Files:**
- Modify: `services/group_registry.py`
- Modify: `tests/services/test_group_registry.py`
- Modify: `app/routes/groups.py`
- Modify: `app/routes/messages.py`
- Modify: `app/routes/executions.py`

**Step 1: Write the failing tests**

Add tests that prove:

- a non-home `web:*` workspace is visible to its owner
- a non-home `web:*` workspace is visible to an added member
- an unrelated user cannot access it
- a home workspace never becomes member-manageable
- IM endpoint rows inherit access only through their bound target workspace on read-side checks

```python
@pytest.mark.asyncio
async def test_can_access_workspace_for_member(db_session: AsyncSession) -> None:
    registry = GroupRegistryService(db=db_session)
    members = GroupMemberService(db=db_session)
    await registry.ensure_registered_group(jid="web:project-alpha", name="Project Alpha", folder="project-alpha", created_by="owner-1")
    await members.add_member("project-alpha", "user-2", role="member")
    assert await registry.user_can_access_workspace(user_id="user-2", folder="project-alpha") is True
```

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py -q
```

Expected: FAIL because `GroupRegistryService` currently only reads `registered_groups` and has no membership-aware access helpers.

**Step 3: Write the minimal implementation**

Implement:

- canonical workspace lookup helpers in `GroupRegistryService`
- membership-aware predicates such as:
  - workspace visibility
  - workspace access
  - member-management eligibility
- keep raw IM endpoint rows hidden from `/groups`

Prefer reusing one small access-check path instead of re-encoding the logic in each route.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add services/group_registry.py tests/services/test_group_registry.py app/routes/groups.py app/routes/messages.py app/routes/executions.py
git commit -m "feat(groups): add workspace membership access rules"
```

### Task 4: Rewire Group Listing And Member Management To Canonical Workspaces

**Files:**
- Modify: `app/routes/groups.py`
- Modify: `tests/app/routes/test_api_routes.py`

**Step 1: Write the failing tests**

Add route tests that prove:

- `/groups` shows shared non-home workspaces to members
- `/groups` still hides other users' home workspaces
- `/groups` still hides raw `telegram:*` / `feishu:*` rows
- `/groups/{group_id}/members` returns `400` for home workspaces
- owner can add/remove members on non-home workspaces
- a non-owner member can leave the workspace
- non-members receive `404`

```python
def test_groups_list_includes_shared_workspace_for_member(api_client: TestClient) -> None:
    response = api_client.get("/groups", headers=member_headers)
    assert {"group_id": "project-alpha", "name": "Project Alpha"} in response.json()["groups"]
```

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_api_routes.py -q
```

Expected: FAIL because `/groups` visibility and `/groups/{group_id}/members` still depend on the old in-memory `group_member_service` boundary.

**Step 3: Write the minimal implementation**

Implement:

- canonical workspace resolution for member routes
- home-workspace rejection for member management
- owner-only add/remove behavior
- self-leave for non-owner members
- `/groups` visibility based on owner/member access

Do not add member search or workspace CRUD endpoints in this task.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_api_routes.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/groups.py tests/app/routes/test_api_routes.py
git commit -m "feat(groups): wire workspace membership into group routes"
```

### Task 5: Enforce Membership On Message Dispatch And Execution Status Reads

**Files:**
- Modify: `app/routes/messages.py`
- Modify: `tests/app/routes/test_message_routes.py`
- Modify: `app/routes/executions.py`
- Modify: `tests/app/routes/test_execution_routes.py`

**Step 1: Write the failing tests**

Add route tests that prove:

- a shared-workspace member can `POST /messages` into the canonical workspace folder
- an unrelated user gets `404` for that same workspace
- a shared-workspace member can read `GET /executions/{run_id}` for runs from that workspace
- an unrelated user still gets `404`

```python
def test_post_messages_allows_workspace_member(api_client: TestClient) -> None:
    response = api_client.post("/messages", json={"group_id": "project-alpha", "content": "hello"}, headers=member_headers)
    assert response.status_code == 200
```

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_message_routes.py tests/app/routes/test_execution_routes.py -q
```

Expected: FAIL because `/messages` and `/executions/{run_id}` do not yet enforce workspace membership.

**Step 3: Write the minimal implementation**

Implement:

- workspace access checks inside `app/routes/messages.py`
- membership-aware snapshot read checks in `app/routes/executions.py`

Keep the current fallback behavior for non-registry `group_id` targets. Do not change WebSocket access control in this task.

**Step 4: Run the focused tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_message_routes.py tests/app/routes/test_execution_routes.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/messages.py tests/app/routes/test_message_routes.py app/routes/executions.py tests/app/routes/test_execution_routes.py
git commit -m "feat(messages): enforce workspace membership access"
```

### Task 6: Run Full Verification And Refresh Handoff Docs

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/services/test_group_member_service.py tests/services/test_group_registry.py tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_execution_routes.py -q
```

Expected: PASS

**Step 2: Run broader regression**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
git diff --check
```

Expected: PASS

**Step 3: Update handoff docs**

Refresh:

- `docs/progress.md` with `M7.3.4` completion, verification evidence, residual WebSocket access-control risk, and `M7.3.5` as the next start point
- `tasks/todo.md` to mark `M7.3.4` complete

Call out explicitly that:

- workspace membership is now persisted by `group_folder`
- home workspaces remain private
- shared members can access workspace listing, HTTP dispatch, and execution status
- authenticated WebSocket access control is still deferred

**Step 4: Commit**

```bash
git add docs/progress.md tasks/todo.md
git commit -m "docs(handoff): record M7.3.4 workspace membership status"
```
