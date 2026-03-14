# M7.3.6 Workspace Management API Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the minimal authenticated workspace-management API surface for shared workspace create/rename, conversation-slot list/create, and conservative workspace-level IM binding management.

**Architecture:** Keep `/groups` as the canonical web-workspace list, then layer new workspace, slot, and IM-binding APIs on top of the existing `registered_groups`, `group_members`, and `conversation_slots` tables. Reuse the current workspace access checks and execution semantics, but add explicit management helpers in the registry/slot layers instead of pushing orchestration into the routes.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy async services, pytest

---

### Task 1: Add The Failing Route And Service Tests

**Files:**
- Modify: `tests/services/test_group_registry.py`
- Modify: `tests/services/test_conversation_slot_service.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `tests/app/routes/test_message_routes.py`

**Step 1: Write the failing tests**

Add focused coverage for:

- creating a shared workspace seeds owner membership and main slot
- creating a shared workspace rejects reserved or invalid `group_id`
- renaming a shared workspace updates `name` but rejects home/main workspaces
- listing slots for an accessible workspace returns `main` first plus extra slots
- creating a slot through HTTP persists the requested metadata
- listing IM bindings returns endpoint rows with binding status
- binding an IM endpoint to one workspace is idempotent for the same workspace and conflicts with another
- unbinding clears the target only when it matches the workspace route

**Step 2: Run the focused tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py tests/services/test_conversation_slot_service.py tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py -q
```

Expected: FAIL because the new service methods, DTOs, and routes do not exist yet.

**Step 3: Commit the red test scaffold only if it is reviewable**

```bash
git add tests/services/test_group_registry.py tests/services/test_conversation_slot_service.py tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py
git commit -m "test(workspaces): add M7.3.6 management coverage"
```

If the repository policy or current session flow makes a red-test commit undesirable, keep the work staged locally and continue.

### Task 2: Implement Workspace And Binding Service Helpers

**Files:**
- Modify: `services/group_registry.py`
- Modify: `services/group_member_service.py`
- Modify: `services/conversation_slot_service.py`
- Modify: `domain/schemas.py`

**Step 1: Write the minimal service-facing contract updates**

Add DTOs and helpers for:

- `CreateWorkspaceRequest`
- `UpdateWorkspaceRequest`
- `WorkspaceSlotResponse` / `WorkspaceSlotListResponse`
- `CreateWorkspaceSlotRequest`
- `IMBindingResponse` / `IMBindingListResponse`

Service helpers should cover:

- create shared workspace
- rename shared workspace
- list IM endpoints with binding status
- bind endpoint to workspace
- unbind endpoint from workspace
- validate workspace IDs / slot IDs conservatively

**Step 2: Run the smallest failing test subset**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py tests/services/test_conversation_slot_service.py -q
```

Expected: FAIL on missing helper behavior until implementation is complete.

**Step 3: Write the minimal implementation**

Implement:

- explicit workspace creation instead of overloading `ensure_registered_group(...)`
- owner membership seeding via `GroupMemberService`
- narrow rename logic for non-home canonical web workspaces
- IM endpoint listing filtered to raw endpoint rows only
- bind/unbind conflict semantics
- slot ID validation that keeps `main` reserved

**Step 4: Run the service tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py tests/services/test_conversation_slot_service.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add services/group_registry.py services/group_member_service.py services/conversation_slot_service.py domain/schemas.py tests/services/test_group_registry.py tests/services/test_conversation_slot_service.py
git commit -m "feat(workspaces): add workspace management service helpers"
```

### Task 3: Implement The HTTP Routes And OpenAPI Surface

**Files:**
- Modify: `app/routes/groups.py`
- Modify: `app/openapi.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `tests/app/routes/test_message_routes.py`

**Step 1: Write or extend the failing HTTP route tests**

Cover:

- `POST /groups`
- `PATCH /groups/{group_id}`
- `GET /groups/{group_id}/slots`
- `POST /groups/{group_id}/slots`
- `GET /groups/{group_id}/bindings/im`
- `PUT /groups/{group_id}/bindings/im/{im_jid}`
- `DELETE /groups/{group_id}/bindings/im/{im_jid}`
- OpenAPI tags and route metadata

**Step 2: Run the route tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py -q
```

Expected: FAIL because the new routes and schemas are not yet wired in.

**Step 3: Write the minimal route implementation**

Implement route helpers that:

- resolve canonical workspace rows before nested actions
- reuse current access checks
- restrict IM binding routes to global `owner`
- keep `/groups` list semantics unchanged
- translate service `ValueError` and conflict states into `400` / `404` / `409`

**Step 4: Run the route tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/groups.py app/openapi.py tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py
git commit -m "feat(api): add workspace management routes"
```

### Task 4: Run Focused And Broader Verification

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run focused feature verification**

Run:

```bash
.venv/bin/pytest tests/services/test_group_registry.py tests/services/test_conversation_slot_service.py tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py -q
```

Expected: PASS

**Step 2: Run broader regression verification**

Run:

```bash
.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py tests/services/test_group_member_service.py tests/services/test_group_registry.py tests/services/test_conversation_slot_service.py tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py tests/services/test_message_service.py tests/services/test_message_dispatch.py tests/app/routes/test_api_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_execution_routes.py tests/app/routes/test_im_routes.py -q
```

Expected: PASS

**Step 3: Run lint and diff hygiene**

Run:

```bash
.venv/bin/ruff check .
git diff --check
```

Expected: PASS

**Step 4: Update restart docs**

Refresh `docs/progress.md` with:

- current phase = `M7.3.6`
- the exact verification commands that passed
- the next real entrypoint after this slice

**Step 5: Commit**

```bash
git add docs/progress.md
git commit -m "docs(progress): record M7.3.6 completion"
```

Plan complete and saved to `docs/plans/2026-03-14-m7-3-6-workspace-management.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
