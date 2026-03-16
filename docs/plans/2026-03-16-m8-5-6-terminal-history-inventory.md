# M8.5.6 Persistence-Aware Terminal History Inventory Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add persisted-history-aware inventory signals into existing terminal overview so operators can inspect latest history state across workspaces.

**Architecture:** Add service-level history summary inventory helper, extend overview schema and `/terminals` route response, then render the new metadata in `web/src/pages/Terminals.tsx`.

**Tech Stack:** Python/FastAPI, Pydantic, React/TypeScript, pytest, Ruff

---

### Task 1: Add Failing Tests For Inventory Contract

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_monitor_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`

Steps:
1. Add service red test for merged history inventory (in-memory + persisted-only).
2. Add `/terminals` route red test assertions for new `history` field population.
3. Add OpenAPI red assertions for `TerminalWorkspaceSummaryResponse.history`.
4. Run focused tests and confirm red:
   - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`

### Task 2: Implement Backend Inventory Read Model

**Files:**
- Modify: `services/terminal_sessions.py`
- Modify: `domain/schemas.py`
- Modify: `app/routes/terminals.py`

Steps:
1. Add history summary dataclass and inventory list helper in `TerminalSessionService`.
2. Extend terminal overview response schema with additive `history` field.
3. Populate overview history summaries in `GET /terminals`.
4. Re-run focused backend tests and confirm green.

### Task 3: Implement Frontend Overview Rendering

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

Steps:
1. Extend frontend terminal overview types to include history summary.
2. Render history metadata columns in `/terminals` workspace table.
3. Run frontend lint/build and keep existing actions behavior unchanged.

### Task 4: Verify, Handoff, Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

Steps:
1. Run focused verification:
   - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
2. Run full verification:
   - `.venv/bin/pytest -o addopts='' -q`
   - `.venv/bin/ruff check .`
   - `cd web && npm run lint`
   - `cd web && npm run build`
   - `git diff --check`
3. Update restart-oriented docs/review notes.
4. Commit milestone changes with detailed message.
