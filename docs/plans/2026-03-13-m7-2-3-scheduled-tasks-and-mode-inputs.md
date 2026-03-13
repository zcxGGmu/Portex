# M7.2.3 Scheduled Tasks And Mode Inputs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Route scheduled tasks through the shared execution coordinator and let HTTP/task callers pass explicit `execution_mode` into the current execution policy.

**Architecture:** Keep `TaskScheduler` generic, make `TaskService` the bridge from scheduled tasks into `ExecutionRequest`, and add optional `execution_mode` only at caller boundaries that already own execution intent. Preserve the current default policy (`None -> openai_runtime`) and current scheduler success/error advancement semantics.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy models, async service orchestration, pytest

---

### Task 1: Lock The Caller Contracts With Failing Tests

**Files:**
- Modify: `tests/app/routes/test_message_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `tests/domain/models/test_models.py`
- Modify: `domain/schemas.py`
- Modify: `domain/models/task.py`

**Step 1: Write the failing test**

Add tests that prove:

- `/messages` accepts an optional `execution_mode` and forwards it into dispatch
- `/tasks` create/list payloads round-trip optional `execution_mode`
- `ScheduledTask` metadata exposes an `execution_mode` column
- OpenAPI schema descriptions include the new field where relevant

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/domain/models/test_models.py -q`

Expected: FAIL because `execution_mode` is not yet defined in the schemas/model.

**Step 3: Write minimal implementation**

Implement the smallest contract change:

- add `execution_mode` to `SendMessageRequest`
- add `execution_mode` to `CreateTaskRequest` / `TaskResponse`
- add `execution_mode` to `ScheduledTask`

Keep it optional and restricted to `"openai" | "host" | "container"`.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/domain/models/test_models.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/domain/models/test_models.py domain/schemas.py domain/models/task.py
git commit -m "feat(execution): add caller execution mode contract"
```

### Task 2: Lock Dispatch And Task-Service Execution Wiring With Failing Tests

**Files:**
- Modify: `tests/services/test_message_dispatch.py`
- Modify: `tests/services/test_task_service.py`
- Modify: `tests/services/test_scheduler.py`
- Modify: `services/message_dispatch.py`
- Modify: `services/task_service.py`

**Step 1: Write the failing test**

Add tests that prove:

- `MessageDispatchService.dispatch_inbound_message(..., execution_mode="host")` copies `"host"` into `ExecutionRequest.requested_mode`
- default scheduled-task execution submits `ExecutionRequest(source="scheduled")` through a coordinator
- task log status mapping is:
  - `completed -> success`
  - `timeout -> timeout`
  - `failed/cancelled -> error`

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py -q`

Expected: FAIL because dispatch/task-service do not yet propagate or use coordinator-backed execution.

**Step 3: Write minimal implementation**

Implement:

- optional `execution_mode` argument on `dispatch_inbound_message()`
- `requested_mode` propagation into `_build_execution_request()`
- coordinator-backed default task execution in `TaskService`
- one fixed scheduled-task user identity constant
- normalized task-log mapping for `completed` / `timeout` / `failed` / `cancelled`

Do not change `TaskScheduler` itself unless a test proves it is necessary.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py services/message_dispatch.py services/task_service.py
git commit -m "feat(execution): route scheduled tasks through coordinator"
```

### Task 3: Wire HTTP And Task Routes To The New Contract

**Files:**
- Modify: `app/routes/messages.py`
- Modify: `app/routes/tasks.py`
- Modify: `tests/app/routes/test_message_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `tests/integration/test_message_flow.py`

**Step 1: Write the failing test**

Extend route/integration coverage so it proves:

- `/messages` forwards request `execution_mode` into the dispatch service
- task creation persists and returns `execution_mode`
- existing IM integration keeps working with no explicit mode input

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/integration/test_message_flow.py -q`

Expected: FAIL because routes do not yet pass the new values through.

**Step 3: Write minimal implementation**

Implement:

- `/messages` passes `request.execution_mode` into `dispatch_inbound_message()`
- `/tasks` passes `request.execution_mode` into `task_service.create_task()`
- task response serialization includes `execution_mode`

Do not add IM route knobs in this task.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/integration/test_message_flow.py -q`

Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/messages.py app/routes/tasks.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/integration/test_message_flow.py
git commit -m "feat(execution): thread execution mode through http and tasks"
```

### Task 4: Verify, Refresh Handoff Docs, And Commit The Slice

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/integration/test_message_flow.py tests/domain/models/test_models.py -q
```

Expected: PASS

**Step 2: Run broader regression**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/integration/test_message_flow.py -q
.venv/bin/ruff check .
```

Expected: PASS

**Step 3: Update handoff docs**

Refresh:

- `docs/progress.md` with `M7.2.3` completion/evidence/next step
- `tasks/todo.md` review section and checklist state

**Step 4: Commit**

```bash
git add docs/progress.md tasks/todo.md
git commit -m "docs(handoff): record M7.2.3 execution-plane follow-up"
```

Plan complete and saved to `docs/plans/2026-03-13-m7-2-3-scheduled-tasks-and-mode-inputs.md`. Per the current user request, execution continues in this session on the subagent-driven path.
