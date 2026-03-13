# M7.2.6 Status Recovery Signaling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expose coordinator-owned execution status and minimal recovery signals via a stable authenticated run-query API.

**Architecture:** Extend `ExecutionCoordinator` with run snapshots that are updated across lifecycle transitions and session-retry recovery branches, then add a read-only HTTP route (`GET /executions/{run_id}`) that returns a schema-normalized snapshot.

**Tech Stack:** Python 3.11, asyncio, FastAPI, pydantic, pytest

---

### Task 1: Lock snapshot and API contracts with failing tests

**Files:**
- Modify: `tests/services/test_execution_coordinator.py`
- Add: `tests/app/routes/test_execution_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`

**Step 1: Write failing tests**

Add tests covering:

- coordinator snapshot transitions (`queued` -> `running` -> `completed`)
- coordinator recovery flags when session-resume retry path is used
- `GET /executions/{run_id}` success (authenticated) and unknown run `404`
- OpenAPI tag/path/schema checks for the new route

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: FAIL because snapshot contract and execution status route do not exist yet.

### Task 2: Implement coordinator snapshot + read API

**Files:**
- Modify: `services/execution_coordinator.py`
- Modify: `domain/schemas.py`
- Add: `app/routes/executions.py`
- Modify: `app/main.py`
- Modify: `app/routes/__init__.py`
- Modify: `app/openapi.py`
- Modify: `services/execution_runtime.py` (if helper exposure is needed)

**Step 1: Minimal implementation**

Implement:

- run snapshot dataclass + storage in coordinator
- snapshot update hooks at submit/start/recovery/terminal
- snapshot read method returning safe copies
- authenticated execution status route returning normalized DTO
- OpenAPI tag wiring for the new route

**Step 2: Run focused tests**

Run:

```bash
.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: PASS

### Task 3: Verify slice and refresh handoff docs

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Focused verification**

Run:

```bash
.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_websocket.py -q
```

Expected: PASS

**Step 2: Broader regression**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py tests/infra/exec/test_process.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected: PASS

**Step 3: Refresh handoff docs**

Update:

- `docs/progress.md` with M7.2.6 completion evidence and next step (`M7.2.7`)
- `tasks/todo.md` checklist and review summary

**Step 4: Commit**

```bash
git add docs/progress.md tasks/todo.md
git commit -m "feat(execution): complete M7.2.6 status recovery signaling"
```
