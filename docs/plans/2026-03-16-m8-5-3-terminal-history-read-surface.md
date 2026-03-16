# M8.5.3 Terminal History Read Surface Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expose a minimal read-only API to retrieve the current terminal session's buffered output history.

**Architecture:** Add a locked read snapshot helper in `TerminalSessionService`, expose it through a new terminal route, and document contract via schema + OpenAPI tests.

**Tech Stack:** Python/FastAPI, Pydantic, pytest, Ruff

---

### Task 1: Add Failing Tests For History Read Contract

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`

Steps:
1. Add service test for history snapshot metadata and truncation behavior.
2. Add route tests for auth required and owner success/not-found mapping on history endpoint.
3. Add OpenAPI assertions for new history route.
4. Run focused tests and confirm red.

### Task 2: Implement Service + Schema + Route

**Files:**
- Modify: `services/terminal_sessions.py`
- Modify: `domain/schemas.py`
- Modify: `app/routes/terminals.py`

Steps:
1. Add service-level history snapshot model + read method by workspace.
2. Add `TerminalSessionHistoryResponse` DTO and export it.
3. Add `GET /terminals/{group_id}/sessions/current/history` using existing terminal/access gates.
4. Re-run focused tests and confirm green.

### Task 3: Verify, Handoff, Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

Steps:
1. Run focused verification:
   - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
2. Run full verification:
   - `.venv/bin/pytest -o addopts='' -q`
   - `.venv/bin/ruff check .`
   - `cd web && npm run lint`
   - `cd web && npm run build`
   - `git diff --check`
3. Update `docs/progress.md` and `tasks/todo.md` review notes.
4. Commit milestone changes.
