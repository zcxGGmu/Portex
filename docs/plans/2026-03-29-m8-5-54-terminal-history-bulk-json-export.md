# M8.5.54 Terminal History Bulk JSON Export Implementation Plan

**Goal:** Add a bounded downloadable JSON export for the current filtered terminal-history page on `/terminals`, containing multiple full snapshot detail records without changing existing history detail/search/relevance behavior.

**Architecture:** Add one additive `GET /terminals/{group_id}/sessions/history/export` route that reuses the current timeline filter/pagination contract, back it with a small `TerminalSessionService` bulk-detail page helper built on the existing merged snapshot/filter path, then thread that through the frontend timeline panel using the existing blob-download action pattern.

**Tech Stack:** FastAPI, Pydantic v2, Starlette responses, React 19, TypeScript, Vite, pytest, Ruff, ESLint

---

### Task 1: Add Failing Service, Route, And OpenAPI Coverage

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `services/terminal_sessions.py`
- Reference: `app/routes/terminals.py`

**Step 1: Write the failing tests**

Add focused coverage that proves:

- the new service helper returns the expected bounded filtered page of snapshot details
- empty filtered result still raises `TerminalSessionNotFoundError`
- `GET /terminals/{group_id}/sessions/history/export` returns:
  - `200`
  - `application/json`
  - attachment filename ending with `.json`
  - JSON body containing pagination/filter metadata plus multiple full detail items
- the route forwards `limit`, `offset`, `status`, `owner_user_id`, `session_id_prefix`, `snapshot_from`, and `snapshot_to`
- missing history still returns `404`
- invalid snapshot range still returns `400`
- OpenAPI exposes the new export path with the timeline filter parameters

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because neither the bulk-detail helper nor the export route exists yet

**Step 3: Write minimal implementation**

Implement the smallest backend delta:

- add one bounded bulk-detail service helper
- add the export route that serializes the helper result as a JSON attachment
- keep filter semantics aligned with the existing timeline route

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

### Task 2: Add Frontend Bulk Export Wiring

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Add the failing frontend wiring**

Reference a current-page history export action from the timeline panel before the API client helper exists.

**Step 2: Run build to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the client/helper signatures do not yet support history export download

**Step 3: Write minimal implementation**

Implement:

- `downloadTerminalHistoryExport(token, groupId, options)`
- shared query parameter building for timeline fetch and export
- one current-page export helper in the page
- one new timeline action:
  - `Export Current Page JSON`

Keep unchanged:

- detail download actions
- search/detail state transitions
- match navigation
- current timeline/search fetch behavior

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
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
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

- `docs/progress.md` with `M8.5.54` scope and evidence
- `tasks/todo.md` review section
- `AGENTS.md` if the terminal summary should mention the new export mode

**Step 4: Commit**

Use the standard split if the session lands both code and restart-doc updates:

```bash
git add services/terminal_sessions.py app/routes/terminals.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/plans/2026-03-29-m8-5-54-terminal-history-bulk-json-export-design.md docs/plans/2026-03-29-m8-5-54-terminal-history-bulk-json-export.md
git commit -m "feat(terminal): add M8.5.54 history bulk export"
```

Then sync restart docs:

```bash
git add docs/progress.md tasks/todo.md AGENTS.md
git commit -m "docs(handoff): sync M8.5.54 history bulk export context"
```
