# M8.5.16 Terminal Search Sort Controls Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add explicit `Relevance` / `Newest` / `Oldest` search-result sort controls to `/terminals` while preserving current terminal-history compatibility, pagination semantics, and RBAC boundaries.

**Architecture:** Extend the existing terminal history search route/service with an additive `sort` query parameter that defaults to `relevance`, then thread that option through the frontend API client, React Query hook, and `/terminals` page state. Keep timeline behavior unchanged and let pagination/navigation continue to operate on one globally sorted backend result set.

**Tech Stack:** FastAPI, Pydantic, Python dataclasses, React 19, TypeScript, Vite, React Query, pytest, Ruff, ESLint

---

### Task 1: Add Failing Backend Tests For Search Sort Modes

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `services/terminal_sessions.py`
- Reference: `app/routes/terminals.py`

**Step 1: Write the failing test**

Add focused tests that assert:

- service search defaults to `relevance`
- service search supports `newest`
- service search supports `oldest`
- search pagination slices the selected sorted result set
- search route forwards `sort`
- search route rejects invalid `sort`
- OpenAPI exposes `sort` on the search route

Example target shapes:

```python
page = await service.search_history_by_group("project-alpha", query="error", sort="newest")
assert [item.record.session_id for item in page.items] == ["terminal-new", "terminal-mid", "terminal-old"]
```

```python
response = api_client.get("/terminals/project-alpha/sessions/history/search?q=error&sort=oldest")
assert response.status_code == 200
```

```python
response = api_client.get("/terminals/project-alpha/sessions/history/search?q=error&sort=invalid")
assert response.status_code == 422
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because the service/route/OpenAPI contract does not support `sort` yet

**Step 3: Write minimal implementation**

Implement the smallest backend changes needed:

- add a narrow search sort type/validation path
- thread `sort` through the terminal search route
- update OpenAPI exposure automatically through the route signature
- keep response DTOs unchanged

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS for the focused backend sort coverage

**Step 5: Commit**

```bash
git add tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py services/terminal_sessions.py app/routes/terminals.py
git commit -m "feat(terminal): add M8.5.16 search sort controls"
```

### Task 2: Add Frontend RED For Search Sort State

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Write the failing contract**

Extend the frontend call sites so the search path references a not-yet-implemented sort option:

- add `sort` to the terminal history search options type in the client/hook usage
- add page state for the selected sort with default `relevance`
- add a select control in the `/terminals` search form

The build should fail first because the types/request wiring are incomplete.

**Step 2: Run test to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because `sort` is referenced before the client/hook types and request params are fully implemented

**Step 3: Write minimal implementation**

Implement the frontend wiring:

- add `sort?: 'relevance' | 'newest' | 'oldest'` to the client/hook option types
- include `sort` in the search request query params
- include `sort` in the React Query key
- add search sort state in `web/src/pages/Terminals.tsx`
- render the search sort selector with `Relevance`, `Newest`, and `Oldest`
- when sort changes:
  - reset `searchOffset`
  - clear `pendingSearchPageMove`
  - clear `detailSessionId`
  - clear `pendingMatchTarget`
- make `clearSearch()` restore sort to `relevance`

Keep these unchanged:

- timeline filters
- time-range presets
- detail route contract
- snippet deep-link behavior

**Step 4: Run test to verify it passes**

Run:

```bash
cd web && npm run build
```

Expected:

- PASS with the search sort selector compiling against the updated client/hook types

### Task 3: Run Verification And Sync Restart Docs

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
cd web && npm run lint
cd web && npm run build
.venv/bin/ruff check .
git diff --check
```

Expected:

- PASS with no focused terminal regressions, frontend issues, lint issues, or diff hygiene issues

**Step 2: Run full verification**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
```

Expected:

- PASS on the full backend suite

**Step 3: Update handoff docs**

Record in `docs/progress.md`, `AGENTS.md`, and the active `tasks/todo.md` session section:

- `M8.5.16` scope and behavior
- latest verification evidence
- next suggested post-`M8.5.16` refinement

**Step 4: Commit**

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync M8.5.16 search sort context"
```
