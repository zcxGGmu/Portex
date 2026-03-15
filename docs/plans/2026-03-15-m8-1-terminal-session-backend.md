# M8.1 Terminal Session Backend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a backend-only terminal session service with dedicated REST/WS protocols for container-backed workspaces, without implementing any frontend terminal UI.

**Architecture:** Introduce a process-local `TerminalSessionService` plus an abstract terminal bridge. Add route-layer authorization and a dedicated WebSocket protocol that is separate from the current chat stream path. Keep v1 container-only and reject unsupported backends explicitly.

**Tech Stack:** FastAPI, asyncio, existing auth/group/execution services, container runtime metadata, pytest, WebSocket route tests

---

### Task 1: Add Red-Stage Tests For Terminal Session Service

**Files:**
- Create: `tests/services/test_terminal_sessions.py`

**Step 1: Write failing service tests**

- terminal create succeeds only for `docker_container`
- `openai_runtime` is rejected as unsupported
- `host_process` is rejected as policy-disabled
- conflicting owner receives error
- detached owner can reconnect before timeout

**Step 2: Run focused red verification**

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected: FAIL because terminal session service does not exist yet.

### Task 2: Implement Terminal Session Service And Bridge Abstractions

**Files:**
- Create: `services/terminal_sessions.py`
- Create: `services/terminal_bridge.py`
- Modify: `services/execution_runtime.py`
- Modify: `services/group_registry.py` (only if a small helper is needed for workspace access reuse)

**Step 1: Add data model and service**

- session state object
- create/read/close/reconnect operations
- reconnect timeout scheduling

**Step 2: Add bridge abstraction**

- define interface for input/output/resize/close
- add container-oriented production bridge stub/implementation boundary

**Step 3: Wire service singleton/dependency**

- expose service through existing runtime/dependency module patterns

### Task 3: Add Red-Stage Route And Protocol Tests

**Files:**
- Create: `tests/app/routes/test_terminal_routes.py`
- Create: `tests/app/routes/test_terminal_websocket_routes.py`

**Step 1: Write failing route tests**

- REST create/read/delete auth and conflict behavior
- websocket emits `terminal.ready`
- websocket rejects bad message types
- websocket forwards output events from fake bridge

**Step 2: Run focused red verification**

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py -q
```

Expected: FAIL because routes and protocol handlers do not exist yet.

### Task 4: Implement Terminal REST And WebSocket Routes

**Files:**
- Create: `app/routes/terminals.py`
- Modify: `app/main.py`
- Modify: `domain/schemas.py`
- Modify: `app/openapi.py`

**Step 1: Add REST API**

- `POST /terminals/{group_id}/sessions`
- `GET /terminals/{group_id}/sessions/current`
- `DELETE /terminals/{group_id}/sessions/current`

**Step 2: Add dedicated terminal WebSocket**

- independent route namespace
- protocol validation for `input/resize/close`
- service attach/detach hooks

**Step 3: Keep existing chat websocket untouched**

- no protocol mixing with `/ws/{group_folder}`

### Task 5: Verify Focused And Regression Coverage

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run focused verification**

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py -q
```

**Step 2: Run broader regression**

```bash
cd web && npm run lint
cd web && npm run build
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
git diff --check
```

**Step 3: Update handoff**

- record `M8.1` scope, verification evidence, and next milestone candidate

### Task 6: Commit Milestone

**Step 1: Commit**

```bash
git add docs/plans/2026-03-15-m8-1-terminal-session-backend-design.md docs/plans/2026-03-15-m8-1-terminal-session-backend.md docs/progress.md app/main.py app/openapi.py app/routes/terminals.py domain/schemas.py services/execution_runtime.py services/terminal_bridge.py services/terminal_sessions.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py
git commit -m "feat(terminal): add M8.1 terminal session backend"
```

Plan complete and saved to `docs/plans/2026-03-15-m8-1-terminal-session-backend.md`. Given you asked to continue in this session, I’m executing it directly now.
