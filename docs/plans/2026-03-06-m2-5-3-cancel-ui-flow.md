# M2.5.3 Cancel Button Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M2.5.3` by wiring the chat UI cancel button to the same WebSocket connection that starts runs, while teaching the backend WebSocket route to launch and cancel connection-local runs.

**Architecture:** Use one WebSocket connection per chat panel as both the message transport and the cancel control channel. Keep the runtime instance and active run bookkeeping inside `app/routes/websocket.py`, and keep frontend running state inside `web/src/stores/chat.ts` so `ChatPanel` can stay thin and deterministic.

**Tech Stack:** FastAPI WebSocket routes, asyncio background tasks, pytest, React, Zustand, TypeScript

---

### Task 1: Replace echo route tests with execution/cancel tests

**Files:**
- Modify: `tests/app/routes/test_websocket_routes.py`
- Reference: `app/routes/websocket.py`

**Step 1: Write the failing tests**

Add two tests:

1. `test_websocket_endpoint_starts_background_execution_for_text_message`
   - monkeypatch `app.routes.websocket.trigger_agent_execution`
   - send a normal text frame
   - assert the stubbed execution path receives the group folder/message and broadcasts a stream event instead of echoing the original text

2. `test_websocket_endpoint_cancels_active_run_from_same_socket`
   - monkeypatch the runtime factory used by the route
   - send one normal text frame to establish an active run
   - send a cancel JSON frame
   - assert `runtime.cancel(run_id)` is called

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q`

Expected: FAIL because the route still echoes text and ignores cancel control frames.

**Step 3: Write minimal implementation**

Change only the route code needed to:
- parse cancel control frames
- create one runtime instance per socket
- launch message execution in a background task
- keep track of the active run id
- cancel the active run when receiving the control frame
- clean up the active task on disconnect

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add app/routes/websocket.py tests/app/routes/test_websocket_routes.py
git commit -m "feat(websocket): add M2.5.3 send and cancel controls"
```

### Task 2: Add frontend running state and cancel button

**Files:**
- Modify: `web/src/stores/chat.ts`
- Modify: `web/src/components/chat/ChatPanel.tsx`

**Step 1: Make the intended UI behavior explicit**

Implement the following behavior:
- `run.started` marks the store as running and captures `activeRunId`
- `run.completed`, `run.failed`, and `run.timeout` clear the running state
- clicking cancel sends `{"type":"cancel","run_id":activeRunId}` over the existing socket
- send is disabled while a run is active
- cancel is disabled when there is no active run

**Step 2: Run frontend verification to expose issues**

Run:
- `cd web && npm run lint`
- `cd web && npm run build`

Expected: FAIL if any new store or component state is missing/incorrectly typed.

**Step 3: Write minimal implementation**

Keep the changes local to the existing store and `ChatPanel`. Do not introduce a new input component or a new HTTP API.

**Step 4: Run frontend verification again**

Run:
- `cd web && npm run lint`
- `cd web && npm run build`

Expected: PASS.

**Step 5: Commit**

```bash
git add web/src/stores/chat.ts web/src/components/chat/ChatPanel.tsx
git commit -m "feat(web): add running state and cancel button"
```

### Task 3: Run focused/full verification and update docs

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused verification**

Run:
- `.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q`

Expected: PASS.

**Step 2: Run broader regression**

Run:
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

Expected: PASS with no new failures.

**Step 3: Update docs**

Record:
- `M2.5.3` complete in `docs/TODO.md`
- verification evidence and next start point `M2.6.1` in `docs/progress.md`
- checklist and review notes in `tasks/todo.md`

**Step 4: Commit**

```bash
git add docs/TODO.md docs/progress.md tasks/todo.md
git commit -m "docs(progress): record M2.5.3 cancel UI flow"
```
