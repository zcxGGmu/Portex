# M8.5.9 Terminal History Output Search Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add per-workspace terminal output search with session-level snippets and detail-panel highlighting, while preserving existing timeline/detail/current-history compatibility.

**Architecture:** Reuse the existing merged terminal-history snapshot inventory in `TerminalSessionService` to add a dedicated search read model and route. Keep search separate from timeline metadata browsing, then wire `/terminals` with a focused search panel that opens the existing detail path and highlights the active query locally.

**Tech Stack:** Python, FastAPI, Pydantic, React, TypeScript, pytest, Ruff, npm build/lint

---

### Task 1: Add Failing Backend Search Tests

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `services/terminal_sessions.py`
- Reference: `app/routes/terminals.py`
- Reference: `domain/schemas.py`

**Step 1: Write the failing tests**

Add focused tests for:

- case-insensitive search over `in-memory`, `latest.json`, and archived snapshots
- snippet capping and `match_count`
- empty search result returning an empty page
- missing workspace history raising `TerminalSessionNotFoundError`
- route auth/access/success/empty/404 behavior for search
- OpenAPI path/schema/query-parameter exposure for the new search route

**Step 2: Run the focused backend tests to verify RED**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because the search service method, route, or DTOs do not exist yet

**Step 3: Write the minimal backend implementation**

Implement:

- `TerminalSessionService.search_history_by_group(...)`
- snippet extraction helpers with bounded results
- search response DTOs in `domain/schemas.py`
- `GET /terminals/{group_id}/sessions/history/search` in `app/routes/terminals.py`

**Step 4: Re-run the focused backend tests to verify GREEN**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS on the new search coverage

**Step 5: Commit**

```bash
git add tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py services/terminal_sessions.py domain/schemas.py app/routes/terminals.py
git commit -m "feat(terminal): add history output search backend"
```

### Task 2: Drive Frontend RED And Implement Search UI

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/pages/Terminals.tsx`
- Reference: `web/src/index.css`

**Step 1: Create the frontend RED condition**

Update `web/src/pages/Terminals.tsx` to reference the intended new search client/hook contract before implementing it:

- search query state
- search results panel
- result selection that reuses detail fetch
- detail output highlighting using the active search term

**Step 2: Run the frontend build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new typed client/hook contract is not implemented yet

**Step 3: Write the minimal frontend implementation**

Implement:

- search DTOs and fetch helper in `web/src/api/client.ts`
- search query hook in `web/src/hooks/useApi.ts`
- search panel, result list, and detail highlighting in `web/src/pages/Terminals.tsx`
- only add CSS in `web/src/index.css` if readability requires it

**Step 4: Re-run frontend checks to verify GREEN**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected:

- PASS for both lint and build

**Step 5: Commit**

```bash
git add web/src/api/client.ts web/src/hooks/useApi.ts web/src/pages/Terminals.tsx web/src/index.css
git commit -m "feat(web): add terminal history output search panel"
```

### Task 3: Run Full Verification And Sync Handoff Docs

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused terminal verification**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS for the terminal-focused regression suite

**Step 2: Run full repo verification**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- PASS on tests, lint, build, and diff hygiene

**Step 3: Update restart-oriented docs**

Record:

- `M8.5.9` scope and completion state
- fresh verification evidence
- immediate next step after search/highlighting

Keep `docs/progress.md` concise and restart-oriented.

**Step 4: Commit**

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync M8.5.9 terminal search context"
```
