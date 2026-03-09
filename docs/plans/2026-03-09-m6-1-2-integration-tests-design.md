# M6.1.2 Integration Tests Design

## Goal

Complete `M6.1.2` by establishing the minimal `tests/integration/` layout promised in `docs/TODO.md` and filling it with meaningful app-level integration tests for the HTTP API baseline and the current WebSocket run/cancel flow.

## Scope

- Add the expected integration entry points:
  - `tests/integration/test_api.py`
  - `tests/integration/test_websocket.py`
- Use `TestClient(app.main.app)` to exercise the real FastAPI app wiring
- Cover:
  - `/health`
  - a minimal auth flow (`register -> login -> /users/me`)
  - WebSocket send/start event flow
  - WebSocket cancel flow
- Reuse fake runtime / monkeypatch patterns already present in route tests
- Run focused integration verification plus full regression and lint

## Out of Scope

- Do not start `M6.1.3` CI/CD work
- Do not add `tests/e2e/test_chat.py`
- Do not introduce frontend/browser-driven tests
- Do not call a real model provider or external IM platform
- Do not expand product behavior beyond the smallest testability fixes if verification reveals a real gap

## Design Constraints

- Keep `tests/integration/` focused on app assembly and protocol boundaries, not fine-grained branch coverage already handled elsewhere
- Prefer deterministic, fake-runtime-backed WebSocket tests over fragile timing-heavy flows
- Reuse existing in-memory service reset patterns to avoid cross-test state leakage
- Preserve restart-friendly workflow: design doc, implementation plan, focused verification, regression, handoff update

## Options Considered

### Option A: API-only integration tests

- Add only `tests/integration/test_api.py`

Pros:
- Smallest implementation

Cons:
- Leaves the WebSocket integration entry absent
- Undershoots the TODO shape for `M6.1.2`

### Option B: WebSocket-only integration tests

- Add only `tests/integration/test_websocket.py`

Pros:
- Hits the most Portex-specific interaction surface

Cons:
- Leaves the API integration entry absent
- Misses the simplest HTTP baseline

### Option C: Minimal API + minimal WebSocket

- Add both `tests/integration/test_api.py` and `tests/integration/test_websocket.py`
- Keep each file intentionally small and deterministic

Pros:
- Matches `docs/TODO.md`
- Establishes both integration entry points without scope creep
- Produces a stronger milestone handoff than doing only one side

Cons:
- Slightly larger than a single-file slice

## Recommended Design

Choose **Option C**.

## Test Slice Design

### `tests/integration/test_api.py`

Cover:
- `GET /health`
- `POST /auth/register -> POST /auth/login -> GET /users/me`

Structure:
- Use the real app object from `app.main`
- Reset auth/group/task state between tests via fixtures
- Avoid deeper route matrix duplication already covered in `tests/app/routes/test_api_routes.py`

### `tests/integration/test_websocket.py`

Cover:
- connect to `/ws/{group_folder}` and receive a deterministic `run.started` event after sending text
- send a cancel payload and receive the expected cancelled `run.failed` event

Structure:
- Use `TestClient.websocket_connect`
- Monkeypatch `app.routes.websocket.trigger_agent_execution`, `create_runtime`, and `uuid4` as needed
- Keep assertions limited to the app/protocol boundary

## Expected Deliverables

- `tests/integration/` contains the two expected files from `docs/TODO.md`
- `.venv/bin/pytest -o addopts='' tests/integration/test_api.py tests/integration/test_websocket.py -q` passes
- full backend regression and `ruff` remain green
- `docs/progress.md` and `tasks/todo.md` advance `M6.1.2` and point to `M6.1.3`
