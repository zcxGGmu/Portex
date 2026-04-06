# M8.5.62 Terminal Cross-Workspace History Archive Filters Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add owner, session-prefix, and time-range filters to the top-level cross-workspace terminal history archive export, plus a minimal `/terminals` UI that lets operators use those filters before downloading the archive.

**Architecture:** Extend the existing top-level archive route and service helper to accept the same owner/session/time filters already supported by workspace-scoped history surfaces, then thread those filters through the `/terminals` page using a small archive-only state slice. Keep overview/latest-history exports unchanged and add a `filters` echo block to the grouped archive response so downloaded artifacts remain self-describing.

**Tech Stack:** FastAPI, Pydantic v2, React 19, TypeScript, Vite, pytest, Ruff, ESLint

---

### Task 1: Record The New Session Scope

**Files:**
- Modify: `tasks/todo.md`
- Create: `docs/plans/2026-04-06-m8-5-62-terminal-cross-workspace-history-archive-filters-design.md`
- Create: `docs/plans/2026-04-06-m8-5-62-terminal-cross-workspace-history-archive-filters.md`
- Reference: `docs/progress.md`

**Step 1: Add the new session checklist**

Add a new top section in `tasks/todo.md` for `M8.5.62` with:

- checked items for restart-doc review and design/plan doc creation
- unchecked items for RED coverage, implementation, verification, docs sync, and commit

**Step 2: Sanity-check the planning docs**

Run:

```bash
git diff --check
```

Expected:

- PASS with no whitespace issues

**Step 3: Commit the planning docs**

Run:

```bash
git add tasks/todo.md docs/plans/2026-04-06-m8-5-62-terminal-cross-workspace-history-archive-filters-design.md docs/plans/2026-04-06-m8-5-62-terminal-cross-workspace-history-archive-filters.md
git commit -m "docs(plans): add M8.5.62 terminal history archive filters plan"
```

Expected:

- PASS

### Task 2: Add Failing Service, Route, And OpenAPI Coverage

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `services/terminal_sessions.py`
- Reference: `app/routes/terminals.py`

**Step 1: Write the failing tests**

Add focused coverage for:

- filtered `list_history_snapshot_archives_by_groups(...)`
- `GET /terminals/history/archive` forwarding:
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`
- response JSON including top-level `filters`
- invalid time bounds returning `400`
- OpenAPI exposing the new query parameters on `/terminals/history/archive`

**Step 2: Run the focused tests to verify RED**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because the service helper signature, route params, and OpenAPI surface are not updated yet

**Step 3: Write minimal backend implementation**

Implement:

- filter arguments on `list_history_snapshot_archives_by_groups(...)`
- filtered top-level archive route params and response metadata

Keep unchanged:

- route path
- grouped item payload shape
- `404` empty-result behavior
- filename

**Step 4: Run the focused tests to verify GREEN**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

### Task 3: Add Minimal `/terminals` Archive Filter UI

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Create the failing frontend change**

Reference archive-filter options from the top-level history archive export action before the API client and page state are fully wired.

Example shape:

```tsx
request: () =>
  apiClient.downloadTerminalHistoryArchiveBundle(token, {
    ownerUserId: archiveFilters.ownerUserId || undefined,
    sessionIdPrefix: archiveFilters.sessionIdPrefix || undefined,
    snapshotFrom: localDateTimeToUtcIso(archiveFilters.snapshotFromLocal),
    snapshotTo: localDateTimeToUtcIso(archiveFilters.snapshotToLocal),
  })
```

**Step 2: Run build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new client options and/or local archive filter state are not implemented yet

**Step 3: Write minimal frontend implementation**

Implement:

- top-level archive filter options in `web/src/api/client.ts`
- top-level archive filter state in `web/src/pages/Terminals.tsx`
- small UI inputs for:
  - `Owner User ID`
  - `Session ID Prefix`
  - `Snapshot From`
  - `Snapshot To`
- `Export History Archive JSON` using only those filter options

Keep unchanged:

- overview export action
- latest histories export action
- page-level download helper/action-state model

**Step 4: Run lint and build to verify GREEN**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected:

- PASS

### Task 4: Run Regression Checks, Sync Restart Docs, And Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Optional: `AGENTS.md`

**Step 1: Run focused regression**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

**Step 2: Run hygiene checks**

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

- `docs/progress.md` with `M8.5.62` scope and verification evidence
- `tasks/todo.md` review section with exact route/UI/test notes
- `AGENTS.md` if the terminal operator-surface summary should mention filtered top-level archive export

**Step 4: Commit**

Run:

```bash
git add services/terminal_sessions.py app/routes/terminals.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/progress.md tasks/todo.md AGENTS.md
git commit -m "feat(terminal): add M8.5.62 cross-workspace history archive filters"
```

Expected:

- PASS
