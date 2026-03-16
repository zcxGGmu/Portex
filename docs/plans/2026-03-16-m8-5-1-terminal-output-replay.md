# M8.5.1 Terminal Output Replay Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add bounded in-memory terminal output replay on reconnect for existing sessions.

**Architecture:** Keep a rolling output buffer in `TerminalSessionService`, replay it during attach, and align frontend transcript behavior to consume replay deterministically.

**Tech Stack:** Python (FastAPI/service layer), React + TypeScript, pytest, Ruff, ESLint, Vite

---

### Task 1: Add Failing Service Tests For Replay And Bounded History

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`

Steps:
1. Add test that emits output, detaches, reattaches, and expects replayed `terminal.output` in queue.
2. Add test that sets tiny history limit and verifies oldest chunks are evicted.
3. Run `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` expecting red.

### Task 2: Implement Bounded History And Replay

**Files:**
- Modify: `services/terminal_sessions.py`

Steps:
1. Extend managed session state with output history buffer + byte counter.
2. Add `history_max_bytes` constructor parameter with safe default.
3. Record output chunks in `_handle_bridge_event` and evict oldest when over cap.
4. Replay buffered output events in `attach_session` before live stream continuation.
5. Re-run `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` expecting green.

### Task 3: Align Frontend Reconnect Transcript Behavior

**Files:**
- Modify: `web/src/components/chat/TerminalPanel.tsx`

Steps:
1. Clear active workspace transcript right before opening new websocket connection.
2. Keep all existing start/connect/close controls unchanged.
3. Run `cd web && npm run lint` and `cd web && npm run build`.

### Task 4: Verify, Handoff, Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

Steps:
1. Run focused verification:
   - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
2. Run full verification:
   - `.venv/bin/pytest -o addopts='' -q`
   - `.venv/bin/ruff check .`
   - `cd web && npm run lint`
   - `cd web && npm run build`
   - `git diff --check`
3. Update progress and todo review with evidence.
4. Commit with milestone-scoped message.
