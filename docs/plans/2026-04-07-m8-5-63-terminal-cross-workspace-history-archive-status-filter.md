# M8.5.63 Terminal Cross-Workspace History Archive Status Filter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the missing `status` filter to the top-level cross-workspace terminal history archive export, plus a minimal `/terminals` archive-only status control that uses the same five lifecycle states as the existing workspace-scoped history surfaces.

**Architecture:** Extend the existing grouped archive route and service helper to accept a single additional `status` filter while preserving the current owner/session/time filter path from `M8.5.62`. Thread that value through the top-level archive-only frontend state and API client, reusing the existing status options list and leaving overview/latest-history exports unchanged.

**Tech Stack:** FastAPI, Pydantic v2, React 19, TypeScript, Vite, pytest, Ruff, ESLint

---

### Task 1: Record The New Session Scope

**Files:**
- Modify: `tasks/todo.md`
- Create: `docs/plans/2026-04-07-m8-5-63-terminal-cross-workspace-history-archive-status-filter-design.md`
- Create: `docs/plans/2026-04-07-m8-5-63-terminal-cross-workspace-history-archive-status-filter.md`
- Reference: `docs/progress.md`

**Step 1: Add the new session checklist**

Add a new top section in `tasks/todo.md` for `M8.5.63` with:

- checked items for restart-doc review, scope confirmation, and design/plan creation
- unchecked items for RED coverage, backend implementation, frontend implementation, verification, docs sync, and commit

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
git add tasks/todo.md docs/plans/2026-04-07-m8-5-63-terminal-cross-workspace-history-archive-status-filter-design.md docs/plans/2026-04-07-m8-5-63-terminal-cross-workspace-history-archive-status-filter.md
git commit -m "docs(plans): add M8.5.63 terminal history archive status filter plan"
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

- grouped archive filtering by `status`
- `GET /terminals/history/archive` forwarding `status`
- response JSON including top-level `filters.status`
- OpenAPI exposing `status` on `/terminals/history/archive`

Keep the new tests narrow:

- reuse the current grouped archive fixtures/patterns
- do not duplicate owner/session/time cases already covered by `M8.5.62`

**Step 2: Run the focused tests to verify RED**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because the grouped archive helper signature, route params, and OpenAPI surface do not expose `status` yet

**Step 3: Write minimal backend implementation**

Implement:

- `status` support on `list_history_snapshot_archives_by_groups(...)`
- `status` forwarding on the top-level grouped archive route
- `filters.status` in the grouped archive response

Keep unchanged:

- route path
- grouped item payload shape
- filename
- `404` empty-result behavior
- owner/session/time filter semantics from `M8.5.62`

**Step 4: Run the focused tests to verify GREEN**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

### Task 3: Add Minimal `/terminals` Archive Status UI

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Create the failing frontend change**

Reference archive-filter `status` from the top-level history archive export action before the client and page state are fully wired.

Example shape:

```tsx
request: () =>
  apiClient.downloadTerminalHistoryArchiveBundle(token, {
    status: archiveFilters.status || undefined,
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

- FAIL because the new archive filter state field and/or API client option are not implemented yet

**Step 3: Write minimal frontend implementation**

Implement:

- `status` in the top-level archive bundle options object in `web/src/api/client.ts`
- `status` in the archive-only filter state in `web/src/pages/Terminals.tsx`
- one `All statuses` dropdown using the existing `TERMINAL_HISTORY_STATUS_OPTIONS`
- `Export History Archive JSON` using that value

Keep unchanged:

- overview export action
- latest histories export action
- archive-only owner/session/time controls from `M8.5.62`
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
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
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

- `docs/progress.md` with `M8.5.63` scope and verification evidence
- `tasks/todo.md` review section with exact route/UI/test notes
- `AGENTS.md` if the current terminal operator-surface summary should mention top-level `status` filtering

**Step 4: Commit**

Run:

```bash
git add services/terminal_sessions.py app/routes/terminals.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/progress.md tasks/todo.md AGENTS.md
git commit -m "feat(terminal): add M8.5.63 cross-workspace history archive status filter"
```

Expected:

- PASS
