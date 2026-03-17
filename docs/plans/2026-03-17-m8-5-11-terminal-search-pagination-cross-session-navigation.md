# M8.5.11 Terminal Search Pagination/Cross-Session Match Navigation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add workspace terminal-output search with paginated results and cross-session previous/next match navigation on `/terminals`.

**Architecture:** Build an additive backend search read model/route on top of the existing merged terminal-history snapshots, then wire frontend search state and detail navigation so match traversal can move across sessions and across search pages while preserving current terminal contracts.

**Tech Stack:** Python, FastAPI, Pydantic, React, TypeScript, pytest, Ruff, npm lint/build

---

### Task 1: Add Failing Backend Search Tests

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `services/terminal_sessions.py`
- Reference: `app/routes/terminals.py`
- Reference: `domain/schemas.py`

**Step 1: Write failing tests**

Cover:

- service search across merged snapshots with case-insensitive matching
- service pagination ordering and `total`/`has_more`
- service empty-match page for existing workspace history
- service `TerminalSessionNotFoundError` for missing workspace history
- route success/empty/404 mapping for `/history/search`
- OpenAPI route and schema coverage for search DTOs

**Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because search service/route/schema contracts do not exist yet

**Step 3: Implement minimal backend support**

Implement:

- search dataclasses and helper logic in `TerminalSessionService`
- search response schemas in `domain/schemas.py`
- `GET /terminals/{group_id}/sessions/history/search` in `app/routes/terminals.py`

**Step 4: Re-run backend tests to verify GREEN**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS on newly added search coverage

### Task 2: Drive Frontend RED And Implement Search + Cross-Session Navigation

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Create frontend RED condition**

Reference intended search contracts in `/terminals` first:

- query state + search-result pagination state
- search-result table and detail selection
- match-navigation boundary behavior across sessions

**Step 2: Run frontend build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL due missing search client/hook/types

**Step 3: Implement minimal frontend support**

Implement:

- search DTO + API helper in `web/src/api/client.ts`
- search query hook in `web/src/hooks/useApi.ts`
- search panel, result pagination, and cross-session match navigation behavior in `web/src/pages/Terminals.tsx`

**Step 4: Re-run frontend checks to verify GREEN**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected:

- PASS for lint and build

### Task 3: Verification And Handoff Sync

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused terminal regression**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS for terminal-focused suite

**Step 2: Run full repository verification**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- PASS on tests, lint/build, and diff hygiene

**Step 3: Update restart-oriented docs**

Record:

- `M8.5.11` scope, verification evidence, and immediate next step

