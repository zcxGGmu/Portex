# M8.5.5 Terminal Active Session Persistence And Recovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Recover active terminal session state after process restart while preserving current API and websocket contracts.

**Architecture:** Rehydrate active session records from persisted snapshot files at service startup, keep recovered sessions detached until owner attach, lazily restart bridge on attach, and persist snapshots on active lifecycle transitions.

**Tech Stack:** Python/FastAPI service layer, pytest, Ruff

---

### Task 1: Add Failing Recovery Tests

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`

Steps:
1. Add service red tests for restart recovery of active sessions, owner attach on recovered session, cross-owner conflict continuity, and attach-failure fallback to closed.
2. Add route red tests for `GET /sessions/current` on recovered state and `POST /sessions` conflict against recovered active owner.
3. Run focused tests and confirm red:
   - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py -q`

### Task 2: Implement Active Session Recovery

**Files:**
- Modify: `services/terminal_sessions.py`

Steps:
1. Extend managed session model to support recovered sessions without live bridge.
2. Rehydrate active snapshots into in-memory maps during service initialization.
3. Persist snapshot on create/attach/detach transitions.
4. Implement lazy bridge creation/start during `attach_session()` for recovered sessions.
5. Handle recovered attach failure by transitioning session to `closed` and persisting fallback state.
6. Re-run focused tests and confirm green:
   - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`

### Task 3: Verify, Handoff, Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

Steps:
1. Run full verification:
   - `.venv/bin/pytest -o addopts='' -q`
   - `.venv/bin/ruff check .`
   - `cd web && npm run lint`
   - `cd web && npm run build`
   - `git diff --check`
2. Update restart-oriented progress/handoff notes for `M8.5.5`.
3. Complete checklist + review notes in `tasks/todo.md`.
4. Commit milestone with detailed message.
