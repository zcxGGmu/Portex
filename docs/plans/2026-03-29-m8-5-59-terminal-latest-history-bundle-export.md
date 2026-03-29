# M8.5.59 Terminal Latest History Bundle Export Implementation Plan

**Goal:** Add a cross-workspace downloadable JSON bundle for the latest terminal-history snapshot of each workspace on `/terminals` without changing existing overview export, workspace-scoped history export, or relevance behavior.

**Architecture:** Add one additive `GET /terminals/history/export` route that reuses top-level canonical workspace discovery plus a small `TerminalSessionService` helper for latest merged snapshots across workspaces, then thread that through the frontend overview surface using the existing blob-download action pattern.

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

- the new service helper returns one latest merged snapshot per workspace
- `GET /terminals/history/export` returns:
  - `200`
  - `application/json`
  - attachment filename ending with `.json`
  - JSON body containing cross-workspace latest history bundle items
- auth and operator-role checks still apply
- empty-history case returns `404`
- OpenAPI exposes the new route

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because neither the latest-history helper nor the bundle route exists yet

**Step 3: Write minimal implementation**

Implement the smallest backend delta:

- add one latest-snapshot-per-workspace helper
- add the bundle route that serializes those snapshots with workspace metadata

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

### Task 2: Add Frontend Latest-History Bundle Wiring

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Add the failing frontend wiring**

Reference a latest-history bundle export action from the overview surface before the API client helper exists.

**Step 2: Run build to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the client/helper signatures do not yet support latest-history bundle export download

**Step 3: Write minimal implementation**

Implement:

- `downloadTerminalLatestHistories(token)`
- one overview-level bundle export helper
- one new overview action:
  - `Export Latest Histories JSON`

Keep unchanged:

- overview export
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

- `docs/progress.md` with `M8.5.59` scope and evidence
- `tasks/todo.md` review section
- `AGENTS.md` if the terminal summary should mention the new bundle mode

**Step 4: Commit**

Use the standard split if the session lands both code and restart-doc updates:

```bash
git add services/terminal_sessions.py app/routes/terminals.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/plans/2026-03-29-m8-5-59-terminal-latest-history-bundle-export-design.md docs/plans/2026-03-29-m8-5-59-terminal-latest-history-bundle-export.md
git commit -m "feat(terminal): add M8.5.59 latest history bundle export"
```

Then sync restart docs:

```bash
git add docs/progress.md tasks/todo.md AGENTS.md
git commit -m "docs(handoff): sync M8.5.59 latest history bundle export context"
```
