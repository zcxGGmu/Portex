# M8.5.64 Terminal Cross-Workspace History Archive Chat-Access Filter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an optional `chat_accessible` filter to the top-level cross-workspace terminal history archive export, plus a minimal `/terminals` archive-only control that lets operators export only chat-accessible or only non-chat-accessible workspaces.

**Architecture:** Keep snapshot-derived filtering in `TerminalSessionService` unchanged. Implement `chat_accessible` entirely in the grouped archive route by computing per-workspace access for the current user, narrowing the workspace set before loading grouped history snapshots, and echoing the filter in the top-level response metadata. Thread the same archive-only value through the frontend client and `/terminals` summary controls.

**Tech Stack:** FastAPI, Pydantic v2, React 19, TypeScript, Vite, pytest, Ruff, ESLint

---

### Task 1: Record The New Session Scope

**Files:**
- Modify: `tasks/todo.md`
- Create: `docs/plans/2026-04-12-m8-5-64-terminal-cross-workspace-history-archive-chat-access-filter-design.md`
- Create: `docs/plans/2026-04-12-m8-5-64-terminal-cross-workspace-history-archive-chat-access-filter.md`
- Reference: `docs/progress.md`

**Step 1: Add the new session checklist**

Add a new top section in `tasks/todo.md` for `M8.5.64` with:

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
git add tasks/todo.md docs/plans/2026-04-12-m8-5-64-terminal-cross-workspace-history-archive-chat-access-filter-design.md docs/plans/2026-04-12-m8-5-64-terminal-cross-workspace-history-archive-chat-access-filter.md
git commit -m "docs(plans): add M8.5.64 terminal history archive chat-access filter plan"
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

- `GET /terminals/history/archive` accepting `chat_accessible`
- `chat_accessible=true` filtering to accessible workspaces only
- `chat_accessible=false` filtering to inaccessible workspaces only
- response JSON including top-level `filters.chat_accessible`
- OpenAPI exposing `chat_accessible` on `/terminals/history/archive`

Keep the new tests narrow:

- reuse the current grouped archive route patterns
- do not duplicate existing snapshot-level filter coverage from `M8.5.62` and `M8.5.63`
- do not add service tests because this filter is intentionally route-owned and user-context-derived

**Step 2: Run the focused tests to verify RED**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because the grouped archive route and OpenAPI surface do not expose `chat_accessible` yet

### Task 3: Implement The Route, Client, And `/terminals` Control

**Files:**
- Modify: `app/routes/terminals.py`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Write minimal backend implementation**

Implement:

- optional `chat_accessible` query handling on `GET /terminals/history/archive`
- per-workspace access evaluation before grouped snapshot loading
- route-level workspace filtering when `chat_accessible` is provided
- `filters.chat_accessible` in the grouped archive response

Keep unchanged:

- route path
- grouped item payload shape
- filename
- `404` empty-result behavior
- snapshot-level filter semantics in `TerminalSessionService`

**Step 2: Create the failing frontend change**

Reference archive-filter `chatAccessible` from the top-level history archive export action before the client and page state are fully wired.

Example shape:

```tsx
request: () =>
  apiClient.downloadTerminalHistoryArchiveBundle(token, {
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

- `chatAccessible` in the top-level archive bundle options object in `web/src/api/client.ts`
- `chatAccessible` in the archive-only filter state in `web/src/pages/Terminals.tsx`
- one `Chat Access` dropdown with:
  - `All workspaces`
  - `Chat accessible only`
  - `No chat access`
- `Export History Archive JSON` using that value

Keep unchanged:

- overview export action
- latest histories export action
- archive-only status/owner/session/time controls from `M8.5.63`
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

- `docs/progress.md` with `M8.5.64` scope and verification evidence
- `tasks/todo.md` review section with exact route/UI/test notes
- `AGENTS.md` if the current terminal operator-surface summary should mention top-level `chat_accessible` filtering

**Step 4: Commit**

Run:

```bash
git add app/routes/terminals.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/progress.md tasks/todo.md AGENTS.md
git commit -m "feat(terminal): add M8.5.64 archive chat-access filter"
```

Expected:

- PASS
