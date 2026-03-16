# M8.4 Terminal Light Controls Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add minimal operator control actions for terminal sessions on top of the M8.3 overview surface.

**Architecture:** Extend terminal session service + route with one force-close path, then wire overview page actions to existing close API and the new force-close API.

**Tech Stack:** FastAPI, Pydantic, React, TypeScript, TanStack Query, pytest, Ruff, ESLint, Vite

---

### Task 1: Add Force-Close Service Contract via TDD

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `services/terminal_sessions.py`

Steps:
1. Add failing test for force-close across owner boundary.
2. Run `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` (expect fail).
3. Implement `force_close_session_by_group(...)`.
4. Re-run focused test suite (expect pass).

### Task 2: Add Force-Close Route Contract via TDD

**Files:**
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `app/routes/terminals.py`

Steps:
1. Add failing route tests for `DELETE /terminals/{group_id}/sessions/force`.
2. Run `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (expect fail).
3. Implement route + error mapping reuse.
4. Re-run focused backend verification (expect pass).

### Task 3: Add Frontend Controls to Terminals Page

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`
- Modify: `web/src/index.css`

Steps:
1. Add red-stage call site for missing force-close client method and run `cd web && npm run build` (expect fail).
2. Implement `forceCloseCurrentTerminalSession(...)` client method.
3. Implement `Close` and `Force Close` actions with per-row loading + notice/error and query refetch.
4. Re-run `cd web && npm run lint` and `cd web && npm run build` (expect pass).

### Task 4: Verification and Handoff Update

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

Steps:
1. Run focused verification:
   - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`
2. Run full regression:
   - `.venv/bin/pytest -o addopts='' -q`
   - `.venv/bin/ruff check .`
   - `cd web && npm run lint`
   - `cd web && npm run build`
   - `git diff --check`
3. Update restart-oriented progress and checklist review.
4. Commit with milestone-focused message.
