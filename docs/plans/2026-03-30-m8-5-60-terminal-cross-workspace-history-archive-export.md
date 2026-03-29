# M8.5.60 Terminal Cross-Workspace History Archive Export Implementation Plan

**Goal:** Add a cross-workspace downloadable JSON archive for all terminal-history snapshots from the top-level `/terminals` surface without changing existing overview, latest-history, or workspace-scoped export behavior.

**Architecture:** Add one additive `GET /terminals/history/archive` route that reuses canonical workspace discovery plus a small `TerminalSessionService` helper for grouped per-workspace snapshot lists, then thread that through the frontend overview surface using the existing blob-download action pattern.

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

- the new service helper returns grouped full snapshot lists per workspace
- `GET /terminals/history/archive` returns:
  - `200`
  - `application/json`
  - attachment filename ending with `.json`
  - JSON body containing grouped cross-workspace archive items
- auth and operator-role checks still apply
- empty-history case returns `404`
- OpenAPI exposes the new route

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because neither the grouped archive helper nor the bundle route exists yet

**Step 3: Write minimal implementation**

Implement the smallest backend delta:

- add one grouped archive helper
- add the bundle route that serializes those grouped snapshots with workspace metadata

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

### Task 2: Add Frontend Cross-Workspace Archive Wiring

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Add the failing frontend wiring**

Reference a cross-workspace history archive action from the overview surface before the API client helper exists.

**Step 2: Run build to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the client/helper signatures do not yet support cross-workspace archive export download

**Step 3: Write minimal implementation**

Implement:

- `downloadTerminalHistoryArchiveBundle(token)`
- one overview-level archive export helper
- one new overview action:
  - `Export History Archive JSON`

Keep unchanged:

- overview export
- latest-history bundle export
- detail export
- timeline/search current-page exports
- timeline/search archive exports

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

- `docs/progress.md` with `M8.5.60` scope and evidence
- `tasks/todo.md` review section
- `AGENTS.md` if the terminal summary should mention the new archive mode

**Step 4: Commit**

Use the standard split if the session lands both code and restart-doc updates:

```bash
git add services/terminal_sessions.py app/routes/terminals.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/plans/2026-03-30-m8-5-60-terminal-cross-workspace-history-archive-export-design.md docs/plans/2026-03-30-m8-5-60-terminal-cross-workspace-history-archive-export.md
git commit -m "feat(terminal): add M8.5.60 cross-workspace history archive export"
```

Then sync restart docs:

```bash
git add docs/progress.md tasks/todo.md AGENTS.md
git commit -m "docs(handoff): sync M8.5.60 cross-workspace history archive export context"
```
