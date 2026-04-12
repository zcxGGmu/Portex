# M8.5.65 Terminal Cross-Workspace History Archive Group-Prefix Filter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an optional `group_id_prefix` filter to the top-level cross-workspace terminal history archive export, plus a minimal `/terminals` archive-only control that lets operators export only one workspace-prefix slice of the grouped archive.

**Architecture:** Keep snapshot-derived filtering in `TerminalSessionService` unchanged. Implement `group_id_prefix` entirely in the grouped archive route by filtering canonical web workspaces before grouped snapshot loading, and echo the value in the top-level response metadata. Thread the same archive-only value through the frontend client and `/terminals` summary controls.

**Tech Stack:** FastAPI, Pydantic v2, React 19, TypeScript, Vite, pytest, Ruff, ESLint

---

### Task 1: Record The New Session Scope

**Files:**
- Modify: `tasks/todo.md`
- Create: `docs/plans/2026-04-12-m8-5-65-terminal-cross-workspace-history-archive-group-prefix-filter-design.md`
- Create: `docs/plans/2026-04-12-m8-5-65-terminal-cross-workspace-history-archive-group-prefix-filter.md`
- Reference: `docs/progress.md`

**Step 1: Add the new session checklist**

Add a new top section in `tasks/todo.md` for `M8.5.65` with:

- checked items for restart-doc review, scope confirmation, filter-choice validation, and design/plan creation
- unchecked items for RED coverage, route implementation, frontend implementation, verification, docs sync, and commit

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
git add tasks/todo.md docs/plans/2026-04-12-m8-5-65-terminal-cross-workspace-history-archive-group-prefix-filter-design.md docs/plans/2026-04-12-m8-5-65-terminal-cross-workspace-history-archive-group-prefix-filter.md
git commit -m "docs(plans): add M8.5.65 terminal history archive group-prefix filter plan"
```

Expected:

- PASS

### Task 2: Add Failing Route And OpenAPI Coverage

**Files:**
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `app/routes/terminals.py`

**Step 1: Write the failing tests**

Add focused coverage for:

- `GET /terminals/history/archive` accepting `group_id_prefix`
- narrowing candidate workspaces before grouped archive loading
- response JSON including top-level `filters.group_id_prefix`
- OpenAPI exposing `group_id_prefix` on `/terminals/history/archive`

Keep the new tests narrow:

- reuse the current grouped archive route patterns
- do not duplicate snapshot-level filter coverage from `M8.5.62` / `M8.5.63`
- do not add service tests because this filter is intentionally route-owned and workspace-derived

**Step 2: Run the focused tests to verify RED**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because the grouped archive route and OpenAPI surface do not expose `group_id_prefix` yet

### Task 3: Implement The Route, Client, And `/terminals` Control

**Files:**
- Modify: `app/routes/terminals.py`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Write minimal backend implementation**

Implement:

- optional `group_id_prefix` query handling on `GET /terminals/history/archive`
- route-level workspace filtering by `group_id.startswith(prefix)` before grouped snapshot loading
- `filters.group_id_prefix` in the grouped archive response

Keep unchanged:

- route path
- grouped item payload shape
- filename
- `404` empty-result behavior
- snapshot-level filter semantics in `TerminalSessionService`

**Step 2: Create the failing frontend change**

Reference archive-filter `groupIdPrefix` from the top-level history archive export action before the client and page state are fully wired.

Example shape:

```tsx
request: () =>
  apiClient.downloadTerminalHistoryArchiveBundle(token, {
    groupIdPrefix: archiveFilters.groupIdPrefix || undefined,
    chatAccessible:
      archiveFilters.chatAccessible === ''
        ? undefined
        : archiveFilters.chatAccessible === 'true',
    status: archiveFilters.status || undefined,
    ownerUserId: archiveFilters.ownerUserId || undefined,
    sessionIdPrefix: archiveFilters.sessionIdPrefix || undefined,
    snapshotFrom: localDateTimeToUtcIso(archiveFilters.snapshotFromLocal),
    snapshotTo: localDateTimeToUtcIso(archiveFilters.snapshotToLocal),
  })
```

**Step 3: Run build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new archive filter state field and/or API client option are not implemented yet

**Step 4: Write minimal frontend implementation**

Implement:

- `groupIdPrefix` in the top-level archive bundle options object in `web/src/api/client.ts`
- `groupIdPrefix` in the archive-only filter state in `web/src/pages/Terminals.tsx`
- one `Workspace Prefix` text input
- `Export History Archive JSON` using that value

Keep unchanged:

- overview export action
- latest histories export action
- archive-only `chat_accessible` / `status` / owner / session / time controls
- page-level download helper/action-state model

**Step 5: Run focused tests, lint, and build to verify GREEN**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
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

- `docs/progress.md` with `M8.5.65` scope and verification evidence
- `tasks/todo.md` review section with exact route/UI/test notes
- `AGENTS.md` if the current terminal operator-surface summary should mention top-level `group_id_prefix` filtering

**Step 4: Commit**

Run:

```bash
git add app/routes/terminals.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/progress.md tasks/todo.md AGENTS.md
git commit -m "feat(terminal): add M8.5.65 archive group-prefix filter"
```

Expected:

- PASS
