# M8.5.56 Terminal History Archive Export Implementation Plan

**Goal:** Add an all-pages downloadable JSON archive for the current filtered terminal-history timeline on `/terminals` without changing existing current-page export, detail export, search, or relevance behavior.

**Architecture:** Add one additive `GET /terminals/{group_id}/sessions/history/archive` route that reuses the current timeline filter contract, back it with a small `TerminalSessionService` helper that returns the full filtered snapshot list using the existing merged snapshot/filter path, then thread that through the frontend timeline panel using the existing blob-download action pattern.

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

- the new service helper returns the expected full filtered snapshot list
- empty filtered result still raises `TerminalSessionNotFoundError`
- `GET /terminals/{group_id}/sessions/history/archive` returns:
  - `200`
  - `application/json`
  - attachment filename ending with `.json`
  - JSON body containing filter metadata plus all matching full detail items
- the route forwards `status`, `owner_user_id`, `session_id_prefix`, `snapshot_from`, and `snapshot_to`
- missing history still returns `404`
- invalid snapshot range still returns `400`
- OpenAPI exposes the new archive path with the timeline filter parameters

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because neither the full-list helper nor the archive route exists yet

**Step 3: Write minimal implementation**

Implement the smallest backend delta:

- add one full filtered snapshot-list helper
- add the archive route that serializes the helper result as a JSON attachment
- keep current-page export semantics unchanged

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

### Task 2: Add Frontend Archive Export Wiring

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Add the failing frontend wiring**

Reference an archive export action from the timeline panel before the API client helper exists.

**Step 2: Run build to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the client/helper signatures do not yet support archive export download

**Step 3: Write minimal implementation**

Implement:

- `downloadTerminalHistoryArchive(token, groupId, filters)`
- reuse the current timeline filter query builder
- one archive export helper in the page
- one new timeline action:
  - `Export Archive JSON`

Keep unchanged:

- current-page timeline export
- current-page search export
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

- `docs/progress.md` with `M8.5.56` scope and evidence
- `tasks/todo.md` review section
- `AGENTS.md` if the terminal summary should mention the new archive mode

**Step 4: Commit**

Use the standard split if the session lands both code and restart-doc updates:

```bash
git add services/terminal_sessions.py app/routes/terminals.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/plans/2026-03-29-m8-5-56-terminal-history-archive-export-design.md docs/plans/2026-03-29-m8-5-56-terminal-history-archive-export.md
git commit -m "feat(terminal): add M8.5.56 history archive export"
```

Then sync restart docs:

```bash
git add docs/progress.md tasks/todo.md AGENTS.md
git commit -m "docs(handoff): sync M8.5.56 history archive export context"
```
