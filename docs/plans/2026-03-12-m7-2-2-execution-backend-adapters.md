# M7.2.2 Execution Backend Adapters Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M7.2.2` by adding unified execution backends for the current runtime, host process, and container runner slices, then rewire WebSocket and IM/HTTP dispatch through the coordinator.

**Architecture:** Introduce a thin `services/execution_backends.py` layer that converts request-scoped execution calls into normalized coordinator results. Reuse the existing coordinator/policy core and route default app entrypoints through a cached coordinator singleton, while explicitly deferring scheduled-task submission.

**Tech Stack:** Python 3.11, asyncio, FastAPI, OpenAI Agents SDK runtime adapter, Docker CLI plus existing Docker helpers, pytest, pytest-asyncio

---

### Task 1: Lock the backend adapter contract with failing tests

**Files:**
- Add: `tests/services/test_execution_backends.py`
- Modify: `tests/infra/exec/test_process.py`
- Reference: `services/agent_trigger.py`
- Reference: `container/agent-runner/src/types.py`

**Step 1: Write the failing test**

Add tests for:

- `OpenAIRuntimeBackend.execute()` mapping `RunResult` to `ExecutionResult`
- `OpenAIRuntimeBackend.cancel()` delegating to the active runtime
- `HostProcessBackend.execute()` parsing raw JSON and framed runner output
- `ContainerBackend.execute()` building `docker run -i --rm` arguments and parsing framed output

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_backends.py tests/infra/exec/test_process.py -q
```

Expected: FAIL because the backend adapter module and any new cancel helpers do not exist yet.

### Task 2: Implement the backend adapter module

**Files:**
- Add: `services/execution_backends.py`
- Modify: `services/execution_coordinator.py`
- Modify: `services/agent_trigger.py`
- Modify: `infra/exec/process.py`
- Test: `tests/services/test_execution_backends.py`
- Test: `tests/infra/exec/test_process.py`

**Step 1: Write minimal implementation**

Implement:

- request-metadata passthrough in `ExecutionRequest`
- runner-output parsing helpers
- openai, host, and container execution backends
- process cancellation support needed by the host backend

**Step 2: Run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_backends.py tests/infra/exec/test_process.py -q
```

Expected: PASS

### Task 3: Rewire default app entrypoints through the coordinator

**Files:**
- Add: `services/execution_runtime.py`
- Modify: `services/message_dispatch.py`
- Modify: `app/routes/websocket.py`
- Modify: `app/routes/im.py`
- Modify: `tests/app/routes/test_websocket_routes.py`
- Modify: `tests/app/routes/test_message_routes.py`
- Modify: `tests/app/routes/test_im_routes.py`
- Modify: `tests/integration/test_websocket.py`
- Modify: `tests/integration/test_message_flow.py`

**Step 1: Write the failing test**

Add or update tests proving:

- WebSocket submits through the coordinator getter and cancels through the coordinator
- default IM/HTTP dispatch waits on coordinator results rather than the direct runtime helper
- existing outbound reply behavior remains unchanged

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_websocket_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py tests/integration/test_websocket.py tests/integration/test_message_flow.py -q
```

Expected: FAIL because the current routes and dispatch service still bypass the coordinator.

**Step 3: Write minimal implementation**

Implement:

- cached default coordinator wiring
- coordinator-backed message dispatch
- coordinator-backed WebSocket submission and cancellation

**Step 4: Re-run focused tests**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_websocket_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py tests/integration/test_websocket.py tests/integration/test_message_flow.py -q
```

Expected: PASS

### Task 4: Refresh handoff docs and verify the slice

**Files:**
- Modify: `tasks/todo.md`
- Modify: `docs/progress.md`
- Optional: `AGENTS.md`

**Step 1: Update progress**

Record:

- `M7.2.2` complete
- WebSocket and IM/HTTP now route through the coordinator
- scheduled-task execution-plane wiring remains next

**Step 2: Run milestone verification**

Run:

```bash
git diff --check
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/app/routes/test_websocket_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py tests/integration/test_websocket.py tests/integration/test_message_flow.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
```

Expected: PASS
