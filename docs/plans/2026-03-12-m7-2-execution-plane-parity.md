# M7.2 Execution Plane Parity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first real execution plane for Portex by adding a per-group coordinator, backend selection, minimal session continuity, and unified submission semantics for Web/IM/tasks.

**Architecture:** Introduce an in-process `ExecutionCoordinator` with one queue per `group_folder`, plus a small `ExecutionPolicy` and request-scoped `ExecutionBackend` adapters. Rewire WebSocket, IM/HTTP dispatch, and scheduled tasks to submit `ExecutionRequest` objects to this coordinator while preserving current workspace-model and operator-surface boundaries for later milestones.

**Tech Stack:** Python 3.11, asyncio, FastAPI, OpenAI Agents SDK adapter layer, SQLAlchemy async, pytest, pytest-asyncio

---

### Task 1: Lock the execution-plane contracts with failing tests

**Files:**
- Add: `tests/services/test_execution_coordinator.py`
- Add: `tests/services/test_execution_policy.py`
- Reference: `services/group_queue.py`
- Reference: `services/agent_trigger.py`

**Step 1: Write the failing tests**

Add tests covering:

- per-group FIFO ordering
- different-group independence
- session reuse for follow-up requests
- status transitions `queued -> running -> completed`
- cancellation and timeout transitions
- basic execution-policy backend choice

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py -q
```

Expected: FAIL because the coordinator/policy modules do not exist yet.

### Task 2: Implement the coordinator and policy core

**Files:**
- Add: `services/execution_coordinator.py`
- Add: `services/execution_policy.py`
- Modify: `services/group_queue.py`
- Modify: `domain/schemas.py` if typed request/result DTOs belong there
- Test: `tests/services/test_execution_coordinator.py`
- Test: `tests/services/test_execution_policy.py`

**Step 1: Write minimal implementation**

Implement:

- execution request/result/status contracts
- per-group queueing and active-run tracking
- minimal session continuity state
- deterministic execution-policy selection
- a compatibility boundary in `services/group_queue.py` so the old placeholder no longer lies about behavior

**Step 2: Run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py -q
```

Expected: PASS

### Task 3: Add request-scoped execution backend adapters

**Files:**
- Add: `services/execution_backends.py`
- Modify: `services/agent_trigger.py`
- Modify: `infra/exec/process.py`
- Modify: `infra/exec/container_manager.py`
- Add: `tests/services/test_execution_backends.py`
- Modify: `tests/infra/runtime/test_openai.py`
- Modify: `tests/infra/exec/test_docker.py`
- Modify: `tests/infra/exec/test_process.py` or add if missing

**Step 1: Write the failing tests**

Add tests covering:

- in-process backend wrapping `run_agent_execution()`
- host-process backend producing a structured `ExecutionResult`
- container backend producing a structured `ExecutionResult`
- backend cancellation hook behavior

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_backends.py tests/infra/runtime/test_openai.py tests/infra/exec/test_docker.py -q
```

Expected: FAIL because the unified adapter boundary does not exist yet.

**Step 3: Write minimal implementation**

Add a thin adapter layer without redesigning the runner protocol.

**Step 4: Re-run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_backends.py tests/infra/runtime/test_openai.py tests/infra/exec/test_docker.py -q
```

Expected: PASS

### Task 4: Rewire WebSocket and IM/HTTP dispatch through the coordinator

**Files:**
- Modify: `app/routes/websocket.py`
- Modify: `app/routes/messages.py`
- Modify: `app/routes/im.py`
- Modify: `services/message_dispatch.py`
- Add: `tests/app/routes/test_websocket_routes.py` updates if needed
- Modify: `tests/app/routes/test_message_routes.py`
- Modify: `tests/app/routes/test_im_routes.py`
- Modify: `tests/integration/test_websocket.py`
- Modify: `tests/integration/test_message_flow.py`

**Step 1: Write the failing tests**

Add or extend tests proving:

- WebSocket submission now goes through the coordinator contract
- IM/HTTP dispatch still works but no longer invokes runtime directly
- cancellation uses the coordinator path

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py tests/integration/test_websocket.py tests/integration/test_message_flow.py -q
```

Expected: FAIL because routes are still wired to direct execution paths.

**Step 3: Write minimal implementation**

Rewire entrypoints to submit `ExecutionRequest` objects and consume coordinator results/status.

**Step 4: Re-run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py tests/integration/test_websocket.py tests/integration/test_message_flow.py -q
```

Expected: PASS

### Task 5: Route scheduled tasks through the coordinator

**Files:**
- Modify: `services/task_service.py`
- Modify: `services/scheduler.py`
- Modify: `app/routes/tasks.py` only if task responses/log wording needs adjustment
- Add: `tests/services/test_task_execution_plane.py`
- Modify: `tests/services/test_scheduler.py`
- Modify: `tests/services/test_task_service.py`

**Step 1: Write the failing tests**

Add tests proving:

- due scheduled tasks submit execution requests to the coordinator
- queued/running/completed/failed results can be reflected in task logs
- deleting or cancelling an actively running scheduled task behaves safely

**Step 2: Run tests to verify they fail**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_scheduler.py tests/services/test_task_service.py tests/services/test_task_execution_plane.py -q
```

Expected: FAIL because scheduled tasks still execute a direct executor callable.

**Step 3: Write minimal implementation**

Adapt task execution to the coordinator without redesigning task CRUD or workspace models.

**Step 4: Re-run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_scheduler.py tests/services/test_task_service.py tests/services/test_task_execution_plane.py -q
```

Expected: PASS

### Task 6: Refresh handoff docs and run milestone verification

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Optional: `README.md`
- Optional: `README.zh-CN.md`
- Optional: `AGENTS.md`

**Step 1: Update progress**

Record:

- what part of `M7.2` is complete
- what is still deferred to `M7.3`
- fresh verification evidence

**Step 2: Run milestone verification**

Run:

```bash
git diff --check
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py tests/integration/test_websocket.py tests/integration/test_message_flow.py tests/services/test_scheduler.py tests/services/test_task_service.py tests/services/test_task_execution_plane.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
```

Expected: PASS
