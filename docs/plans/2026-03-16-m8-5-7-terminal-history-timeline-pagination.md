# M8.5.7 Terminal History Timeline/Pagination Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement per-workspace multi-snapshot terminal history timeline with pagination, while keeping `latest.json` and current-history route compatibility.

**Architecture:** Add archived snapshot persistence (additive), build paginated timeline read model in terminal session service, expose route/schema, then add minimal on-demand timeline UI in `/terminals`.

**Tech Stack:** Python/FastAPI, Pydantic, React/TypeScript, pytest, Ruff

---

### Task 1: Add Failing Tests For Timeline Contracts

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`

Steps:
1. Add service red tests for archived snapshots + pagination + fallback/dedupe behavior.
2. Add route red tests for `GET /terminals/{group_id}/sessions/history` success and not-found mapping.
3. Add OpenAPI red assertions for route/schemas.
4. Run focused tests and confirm red:
   - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`

### Task 2: Implement Backend Timeline Model + Route

**Files:**
- Modify: `services/terminal_sessions.py`
- Modify: `domain/schemas.py`
- Modify: `app/routes/terminals.py`

Steps:
1. Add additive archive persistence under `data/terminal-history/<workspace>/snapshots/` for terminal states.
2. Add timeline entry/page dataclasses and `list_history_timeline_by_group(limit, offset)`.
3. Add timeline response DTOs and route mapping in `/terminals/{group_id}/sessions/history`.
4. Re-run focused backend tests and confirm green.

### Task 3: Implement Minimal Frontend On-Demand Timeline View

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/pages/Terminals.tsx`

Steps:
1. Add timeline client types and fetch helper.
2. Add timeline query hook keyed by `groupId/limit/offset`.
3. Add per-workspace “View Timeline” interaction with next/prev pagination controls.
4. Run frontend lint/build and keep current overview polling/actions unchanged.

### Task 4: Verify, Handoff, Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`
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
