# M8.5.58 Terminal Overview Export Implementation Plan

**Goal:** Add a downloadable JSON export for the top-level `/terminals` overview without changing existing workspace-scoped terminal export or relevance behavior.

**Architecture:** Add one additive `GET /terminals/export` route that reuses the current overview read path and serializes the existing `TerminalWorkspaceListResponse` payload as a JSON attachment, then thread that through the frontend `/terminals` overview surface using the existing blob-download action pattern.

**Tech Stack:** FastAPI, Pydantic v2, Starlette responses, React 19, TypeScript, Vite, pytest, Ruff, ESLint

---

### Task 1: Add Failing Route And OpenAPI Coverage

**Files:**
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `app/routes/terminals.py`

**Step 1: Write the failing tests**

Add focused coverage that proves:

- `GET /terminals/export` returns:
  - `200`
  - `application/json`
  - attachment filename ending with `.json`
  - JSON body matching the existing overview payload shape
- auth and operator-role checks still apply
- OpenAPI exposes the new export path

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because the overview export route does not exist yet

**Step 3: Write minimal implementation**

Implement the smallest backend delta:

- add a static overview export route
- reuse the existing overview payload construction
- return a JSON attachment with a sanitized filename

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

### Task 2: Add Frontend Overview Export Wiring

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Add the failing frontend wiring**

Reference an overview export action from the top-level `/terminals` surface before the API client helper exists.

**Step 2: Run build to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the client/helper signatures do not yet support overview export download

**Step 3: Write minimal implementation**

Implement:

- `downloadTerminalOverview(token)`
- one overview export helper in the page
- one new overview action:
  - `Export Overview JSON`

Keep unchanged:

- timeline exports
- search exports
- detail downloads
- timeline/search/detail state transitions

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

- `docs/progress.md` with `M8.5.58` scope and evidence
- `tasks/todo.md` review section
- `AGENTS.md` if the terminal summary should mention the new overview export mode

**Step 4: Commit**

Use the standard split if the session lands both code and restart-doc updates:

```bash
git add app/routes/terminals.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/plans/2026-03-29-m8-5-58-terminal-overview-export-design.md docs/plans/2026-03-29-m8-5-58-terminal-overview-export.md
git commit -m "feat(terminal): add M8.5.58 overview export"
```

Then sync restart docs:

```bash
git add docs/progress.md tasks/todo.md AGENTS.md
git commit -m "docs(handoff): sync M8.5.58 overview export context"
```
