# M7.2.7 Focused Execution-Plane Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add focused tests that lock queue ordering, executor selection, follow-up/session behavior, cancellation edges, timeout transport payload, and recovery signaling semantics.

**Architecture:** Extend the existing execution-plane test slices (`coordinator` and `websocket routes`) with high-signal behavior tests. Keep production changes minimal and only to fix defects exposed by red tests.

**Tech Stack:** Python 3.11+, pytest, pytest-asyncio, FastAPI TestClient

---

### Task 1: Add failing coordinator behavior tests

**Files:**
- Modify: `tests/services/test_execution_coordinator.py`

**Step 1: Write failing tests**

Add tests for:

- same-group head failure still allows next queued run to execute
- mixed-source same-group requests are serialized
- explicit `requested_mode` is reflected in snapshot backend
- cancel returns `False` for unknown run and terminal run
- recovery retry failure snapshot flags
- `fresh_session=True` bypasses recovery retry signaling

**Step 2: Run focused coordinator tests (expect red initially, then green)**

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py
```

### Task 2: Add failing websocket timeout payload test

**Files:**
- Modify: `tests/app/routes/test_websocket_routes.py`

**Step 1: Write failing timeout transport test**

Add test that forces coordinator timeout result and asserts WebSocket emits:

- `event_type == "run.timeout"`
- payload includes `status == "timeout"`
- payload includes `timeout_ms`

**Step 2: Run websocket route tests (expect red initially, then green)**

```bash
.venv/bin/pytest -o addopts='' tests/app/routes/test_websocket_routes.py
```

### Task 3: Fix only test-exposed gaps

**Files:**
- Modify only if required by red tests:
  - `services/execution_coordinator.py`
  - `app/routes/websocket.py`
  - related schemas/helpers only when strictly necessary

**Step 1: Implement minimal fixes**

Apply the smallest behavior-preserving changes to satisfy the new tests.

**Step 2: Re-run focused suites**

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/app/routes/test_websocket_routes.py
```

### Task 4: Verify, document, and commit

**Files:**
- Modify: `tasks/todo.md`
- Modify: `docs/progress.md`

**Step 1: Behavior-focused regression**

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_websocket.py
```

**Step 2: Broader execution-plane regression**

```bash
.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py tests/infra/exec/test_process.py -q
```

**Step 3: Repository regression and hygiene**

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

**Step 4: Refresh handoff docs**

- mark `M7.2.7` complete in `tasks/todo.md`
- append `M7.2.7` review/evidence
- update `docs/progress.md` current phase, verification evidence, and next starting point

**Step 5: Commit**

```bash
git add .
git commit -m "test(execution): complete M7.2.7 focused parity coverage"
```
