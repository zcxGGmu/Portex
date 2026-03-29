# M8.5.57 Terminal History Search Archive Export Implementation Plan

**Goal:** Add an all-pages downloadable JSON archive for the current terminal-history search result set on `/terminals` without changing existing current-page search export, timeline archive, detail export, or relevance behavior.

**Architecture:** Add one additive `GET /terminals/{group_id}/sessions/history/search/archive` route that reuses the current search parameter contract and existing search service semantics, serialize the full filtered search result set as a JSON attachment, then thread that through the frontend search panel using the existing blob-download action pattern.

**Tech Stack:** FastAPI, Pydantic v2, Starlette responses, React 19, TypeScript, Vite, pytest, Ruff, ESLint

---

### Task 1: Add Failing Route And OpenAPI Coverage

**Files:**
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `app/routes/terminals.py`

**Step 1: Write the failing tests**

Add focused coverage that proves:

- `GET /terminals/{group_id}/sessions/history/search/archive` returns:
  - `200`
  - `application/json`
  - attachment filename ending with `.json`
  - JSON body containing query/sort/filter metadata plus all matching search-result items
- the route forwards `q`, `sort`, `status`, `owner_user_id`, `session_id_prefix`, `snapshot_from`, and `snapshot_to`
- missing history still returns `404`
- invalid snapshot range still returns `400`
- OpenAPI exposes the new archive path with the search parameters

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because the search archive route does not exist yet

**Step 3: Write minimal implementation**

Implement the smallest backend delta:

- add a static search archive route
- reuse the existing search service path
- return a JSON attachment with a sanitized filename

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

### Task 2: Add Frontend Search Archive Wiring

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Add the failing frontend wiring**

Reference a search archive export action from the search panel before the API client helper exists.

**Step 2: Run build to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the client/helper signatures do not yet support search archive export download

**Step 3: Write minimal implementation**

Implement:

- `downloadTerminalHistorySearchArchive(token, groupId, options)`
- reuse the current search query builder
- one archive export helper in the page
- one new search action:
  - `Export Search Archive JSON`

Keep unchanged:

- current-page search export
- timeline current-page export
- timeline archive export
- detail download actions
- search/detail state transitions

**Step 4: Run build to verify it passes**

Run:

```bash
cd web && npm run build
```

Expected:

- PASS

### Task 3: Run Focused Verification And Sync Restart Notes

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Optional: `AGENTS.md`

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

**Step 2: Run hygiene and frontend verification**

Run:

```bash
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- PASS

**Step 3: Update restart-oriented docs**

Refresh:

- `docs/progress.md` with `M8.5.57` scope and evidence
- `tasks/todo.md` review section
- `AGENTS.md` if the terminal summary should mention the new search archive mode

**Step 4: Commit**

Use the standard split if the session lands both code and restart-doc updates:

```bash
git add app/routes/terminals.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/plans/2026-03-29-m8-5-57-terminal-history-search-archive-export-design.md docs/plans/2026-03-29-m8-5-57-terminal-history-search-archive-export.md
git commit -m "feat(terminal): add M8.5.57 history search archive export"
```

Then sync restart docs:

```bash
git add docs/progress.md tasks/todo.md AGENTS.md
git commit -m "docs(handoff): sync M8.5.57 history search archive export context"
```
