# M8.5.13 Terminal Search Filter Alignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align terminal-history search with existing timeline filters by adding optional `status`, `owner_user_id`, and `session_id_prefix` filtering end-to-end.

**Architecture:** Reuse the existing service-side snapshot filter helper before running output search, expose the same filters on the search route, then thread the current timeline filter state through the frontend search query so `/terminals` uses one consistent filter model.

**Tech Stack:** Python, FastAPI, Pydantic, React, TypeScript, pytest, Ruff, npm lint/build

---

### Task 1: Add Failing Backend Filtered-Search Tests

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `services/terminal_sessions.py`
- Reference: `app/routes/terminals.py`
- Reference: `domain/schemas.py`

**Step 1: Write failing tests**

Cover:

- service search filtered by `status`
- service search filtered by `owner_user_id`
- service search filtered by `session_id_prefix`
- route pass-through for the new search query parameters
- OpenAPI exposure for the new search query parameters

**Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because search does not accept or apply the three filters yet

**Step 3: Implement minimal backend support**

Implement:

- additive filter parameters in `TerminalSessionService.search_history_by_group(...)`
- filter reuse via `_filter_history_snapshots(...)`
- additive route query parameters in `app/routes/terminals.py`

**Step 4: Re-run backend tests to verify GREEN**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS on filtered-search backend coverage

### Task 2: Thread Filter State Through Frontend Search

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Create frontend RED condition**

Reference the intended filter-aligned search contracts first:

- search hook cache key includes `status`, `ownerUserId`, and `sessionIdPrefix`
- search request sends those optional params
- timeline filter changes reset search/detail state consistently

**Step 2: Run frontend build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the updated search options/types are not wired yet

**Step 3: Implement minimal frontend support**

Implement:

- additive search option types/API params in `web/src/api/client.ts`
- additive hook options/query key in `web/src/hooks/useApi.ts`
- pass current timeline filter state into search and reset stale search/detail state in `web/src/pages/Terminals.tsx`

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
- Modify: `AGENTS.md`

**Step 1: Run focused terminal regression**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS for the terminal-focused suite

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

- `M8.5.13` scope, verification evidence, and the next post-`M8.5.13` refinement suggestion

**Step 4: Commit milestone**

Commit message:

```bash
git commit -m "feat(terminal): complete M8.5.13 search filter alignment"
```
