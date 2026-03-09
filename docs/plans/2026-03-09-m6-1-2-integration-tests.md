# M6.1.2 Integration Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M6.1.2` by creating the expected `tests/integration/` layout and filling it with focused API and WebSocket integration tests against the real FastAPI app assembly.

**Architecture:** Keep this milestone scoped to integration-level behavior only. Reuse the real `app.main.app`, in-memory services, and fake runtime monkeypatching that already exists in route tests, but avoid duplicating the full per-route branch matrix from `tests/app/routes/`.

**Tech Stack:** Python 3.11, FastAPI `TestClient`, pytest, threading, monkeypatch

---

### Task 1: Add API integration tests

**Files:**
- Create: `tests/integration/test_api.py`
- Reference: `app/main.py`
- Reference: `app/routes/health.py`
- Reference: `app/routes/auth.py`
- Reference: `tests/app/routes/test_api_routes.py`

**Step 1: Write the failing test**

Add tests for:

```python
def test_health_check_endpoint(api_client: TestClient) -> None:
    ...

def test_register_login_and_get_current_user_flow(api_client: TestClient) -> None:
    ...
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest -o addopts='' tests/integration/test_api.py -q`
Expected: FAIL before the file exists.

**Step 3: Write minimal implementation**

No production code change unless verification reveals a real app-wiring gap. Reuse a fixture that resets the in-memory services and yields `TestClient(app)`.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest -o addopts='' tests/integration/test_api.py -q`
Expected: PASS

### Task 2: Add WebSocket integration tests

**Files:**
- Create: `tests/integration/test_websocket.py`
- Reference: `app/routes/websocket.py`
- Reference: `tests/app/routes/test_websocket_routes.py`

**Step 1: Write the failing test**

Add tests for:

```python
def test_websocket_endpoint_starts_background_execution_for_text_message(
    api_client: TestClient,
) -> None:
    ...

def test_websocket_endpoint_cancels_active_run_from_same_socket(
    api_client: TestClient,
) -> None:
    ...
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest -o addopts='' tests/integration/test_websocket.py -q`
Expected: FAIL before the file exists.

**Step 3: Write minimal implementation**

No production code change unless the integration boundary is actually broken. Prefer deterministic monkeypatching of:

```python
websocket_routes.trigger_agent_execution
websocket_routes.create_runtime
websocket_routes.uuid4
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest -o addopts='' tests/integration/test_websocket.py -q`
Expected: PASS

### Task 3: Run focused and regression verification

**Files:**
- No code changes required unless a real gap is found

**Step 1: Run focused integration suite**

Run: `.venv/bin/pytest -o addopts='' tests/integration/test_api.py tests/integration/test_websocket.py -q`
Expected: PASS

**Step 2: Run regression**

Run:
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`

Expected: PASS

### Task 4: Update handoff docs and commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Record `M6.1.2`**

Document:
- the new `tests/integration/` layout
- focused verification evidence
- next start point `M6.1.3`

**Step 2: Commit**

Prepare a focused commit such as:
- `test(integration): complete M6.1.2 integration test suite`
