# M2.6.1 Acceptance Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M2.6.1` by collecting concrete end-to-end acceptance evidence for the M2 login, chat, streaming, and cancel flow, and recording any environment limitations honestly.

**Architecture:** Drive the running application through real HTTP and WebSocket endpoints instead of relying only on unit tests. Because the local environment does not expose an `OPENAI_API_KEY`, use a temporary acceptance harness that patches the WebSocket route runtime factory to emit deterministic stream events, so the full backend/frontend protocol can still be exercised through live processes without changing repository code.

**Tech Stack:** FastAPI/Uvicorn, Vite dev server, curl, Python HTTP/WS scripts, temporary acceptance harness

---

### Task 1: Prepare the acceptance harness and environment

**Files:**
- Create: `/tmp/portex_m26_acceptance_app.py`
- Modify: `tasks/todo.md`
- Reference: `app/main.py`
- Reference: `app/routes/websocket.py`

**Step 1: Create a temporary acceptance harness**

Write a small Python script outside the repo that:
- imports `app.main.app`
- monkeypatches `app.routes.websocket.create_runtime`
- returns a fake runtime that can emit:
  - a normal stream path (`run.started` → `run.token.delta` → `run.completed`)
  - a cancelable long-running path

This avoids repo code churn while still giving live end-to-end evidence.

**Step 2: Start backend and frontend processes**

Run backend from the harness and frontend from Vite dev server, capturing logs to temp files.

Expected:
- backend answers `/health`
- frontend answers `/`

**Step 3: Commit**

No repository commit in this task; the harness is temporary.

### Task 2: Run the M2 acceptance flow

**Files:**
- Create: `/tmp/portex_m26_acceptance_check.py`
- Modify: `tasks/todo.md`

**Step 1: Exercise auth flow**

Use HTTP calls to:
- `POST /auth/register`
- `POST /auth/login`

Record status codes and token presence.

**Step 2: Exercise chat stream flow**

Use a WebSocket client to:
- connect to `/ws/group-demo`
- send a normal text message
- assert receipt of `run.started`, `run.token.delta`, and `run.completed`

**Step 3: Exercise cancel flow**

Use another WebSocket interaction to:
- send a long-running message
- wait for `run.started`
- send the cancel control frame
- assert receipt of the terminal cancelled status event

**Step 4: Capture environment limitation honestly**

Record that timeout was already covered by automated tests in `M2.5.2`, and that local live streaming acceptance uses a fake runtime because no `OPENAI_API_KEY` is set in the environment.

### Task 3: Run supporting regressions and update docs

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run regression checks**

Run:
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update docs**

Record:
- `M2.6.1` complete in `docs/TODO.md`
- exact acceptance evidence in `docs/progress.md`
- review notes in `tasks/todo.md`

**Step 3: Commit**

```bash
git add docs/TODO.md docs/progress.md tasks/todo.md
git commit -m "docs(progress): record M2.6.1 acceptance evidence"
```
