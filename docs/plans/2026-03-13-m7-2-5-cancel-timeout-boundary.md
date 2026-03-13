# M7.2.5 Cancel Timeout Boundary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden the real queue + executor boundary so cancellation and timeout outcomes remain truthful for host/container execution even after the original backend coroutine is cancelled.

**Architecture:** Keep the coordinator as the user-visible owner of `cancelled` and `timeout`, but move cleanup reachability into backend-owned active-run handles. Normalize host timeout to `timeout`, retain cleanup handles until the real executor is gone, and preserve current WebSocket/task outward semantics.

**Tech Stack:** Python 3.11, asyncio, subprocess/Docker execution wrappers, FastAPI routes, pytest

---

### Task 1: Lock The Cancel/Timeout Boundary With Failing Tests

**Files:**
- Modify: `tests/services/test_execution_backends.py`
- Modify: `tests/services/test_execution_coordinator.py`
- Modify: `tests/infra/exec/test_process.py`
- Reference: `services/execution_backends.py`
- Reference: `services/execution_coordinator.py`
- Reference: `infra/exec/process.py`

**Step 1: Write the failing tests**

Add tests that prove:

- host/container active-run handles remain cancelable after outer coroutine cancellation
- coordinator timeout on host/container still results in backend cleanup and normalized `timeout`
- host executor timeout is mapped to `timeout`, not generic `failed`

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_execution_backends.py tests/services/test_execution_coordinator.py tests/infra/exec/test_process.py -q
```

Expected: FAIL because current backends lose cleanup reachability and host timeout still leaks as a generic execution error.

**Step 3: Write minimal implementation**

Implement:

- cleanup-aware active-run handles for host/container backends
- host timeout normalization
- any small `ProcessExecutor` contract change needed to support that behavior

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_execution_backends.py tests/services/test_execution_coordinator.py tests/infra/exec/test_process.py -q
```

Expected: PASS

### Task 2: Lock Transport And Task Semantics Against Regression

**Files:**
- Modify: `tests/integration/test_websocket.py`
- Modify: `tests/app/routes/test_websocket_routes.py`
- Modify: `tests/services/test_task_service.py`
- Modify: `app/routes/websocket.py` only if required by the tests
- Modify: `services/task_service.py` only if required by the tests

**Step 1: Write the failing tests**

Add or extend tests that prove:

- WebSocket cancel and timeout still emit the same external terminal semantics after backend cleanup changes
- scheduled-task timeout/cancel mapping remains `timeout` / `error`

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/integration/test_websocket.py tests/app/routes/test_websocket_routes.py tests/services/test_task_service.py -q
```

Expected: FAIL if transport/task behavior drifted during the backend cleanup refactor.

**Step 3: Write minimal implementation**

Adjust route/service code only if the new backend cleanup behavior requires a small integration fix. Do not redesign the outward payloads or add new APIs here.

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/integration/test_websocket.py tests/app/routes/test_websocket_routes.py tests/services/test_task_service.py -q
```

Expected: PASS

### Task 3: Run Verification, Refresh Handoff Docs, And Commit The Slice

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/services/test_execution_backends.py tests/services/test_execution_coordinator.py tests/infra/exec/test_process.py tests/integration/test_websocket.py tests/app/routes/test_websocket_routes.py tests/services/test_task_service.py -q
```

Expected: PASS

**Step 2: Run broader regression**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py tests/infra/exec/test_process.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected: PASS

**Step 3: Update handoff docs**

Refresh:

- `docs/progress.md` with `M7.2.5` completion/evidence/next step
- `tasks/todo.md` checklist/review state

Call out explicitly that:

- cancel/timeout cleanup is now truthful across the queue/executor boundary
- richer external status/recovery signaling is still deferred to `M7.2.6`

**Step 4: Commit**

```bash
git add docs/progress.md tasks/todo.md
git commit -m "docs(handoff): record M7.2.5 cancel timeout boundary"
```

Plan complete and saved to `docs/plans/2026-03-13-m7-2-5-cancel-timeout-boundary.md`. Per the current user request, execution continues in this session on the subagent-driven path.
