# M8.3 Terminal Operator UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a dedicated read-only terminal operator surface with a `GET /terminals` API, a standalone `/terminals` page, and a minimal workspace-level chat deep link.

**Architecture:** Extend the existing terminal session service with a read-only listing helper, aggregate that data with canonical web workspace metadata in a new operator route, and render it in a dedicated frontend page. Keep terminal control flows inside the existing chat `TerminalPanel`, and only add the smallest `/chat?workspace=...` deep-link support needed for operator navigation.

**Tech Stack:** FastAPI, existing auth/group registry services, Pydantic, React 19, TypeScript, TanStack Query, React Router, pytest, ESLint, Vite build

---

### Task 1: Add Read-Side Service Coverage For Terminal Session Listing

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `services/terminal_sessions.py`

**Step 1: Write the failing test**

Add focused tests that:

```python
sessions = service.list_sessions()

assert [item.group_folder for item in sessions] == ["project-alpha", "project-beta"]
assert sessions[0].status == "attached"
assert sessions[1].status == "closed"
```

and verify the helper reflects current in-memory records after create/attach/detach/close transitions.

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`

Expected: FAIL because `TerminalSessionService` does not yet expose a session-listing helper.

**Step 3: Write minimal implementation**

Implement `TerminalSessionService.list_sessions()` as a pure read helper returning current `TerminalSessionRecord` snapshots without changing lifecycle behavior or persistence semantics.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`

Expected: PASS

### Task 2: Add Operator Route Contract For Terminal Overview

**Files:**
- Create: `tests/app/routes/test_terminal_monitor_routes.py`
- Modify: `app/routes/terminals.py`
- Modify: `domain/schemas.py`
- Modify: `tests/app/routes/test_api_routes.py`

**Step 1: Write the failing route tests**

Add route coverage for:

```python
response = api_client.get("/terminals", headers=headers)

assert response.status_code == 200
assert response.json()["items"][0]["group_id"] == "project-alpha"
assert response.json()["items"][0]["chat_accessible"] is True
assert response.json()["items"][0]["session"]["status"] == "attached"
```

Also cover:

- `401` for unauthenticated requests
- `403` for `member`
- workspaces with `session = null`
- active sessions sorted ahead of closed/no-session workspaces
- `chat_accessible` false when the operator cannot open that workspace via `/chat`

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`

Expected: FAIL because `GET /terminals` and its schemas do not exist yet.

**Step 3: Write minimal implementation**

Implement:

- new terminal overview DTOs in `domain/schemas.py`
- `GET /terminals` in `app/routes/terminals.py`
- operator-only access gate (`owner/admin`)
- workspace + session aggregation
- deterministic sorting and `chat_accessible` projection
- OpenAPI coverage updates

**Step 4: Run focused backend verification**

Run: `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`

Expected: PASS

### Task 3: Create The Frontend Red Stage For A Dedicated Terminals Page

**Files:**
- Modify: `web/src/App.tsx`
- Modify: `web/src/components/layout/AppLayout.tsx`

**Step 1: Wire the missing page intentionally**

Add:

- a protected `/terminals` route
- operator-only `Terminals` navigation entry
- an import of a not-yet-implemented `web/src/pages/Terminals.tsx`

**Step 2: Run the frontend build to verify it fails**

Run: `cd web && npm run build`

Expected: FAIL because the page and related client helpers are still missing.

### Task 4: Implement Terminal Operator Client And Page

**Files:**
- Create: `web/src/pages/Terminals.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/index.css`

**Step 1: Add typed API client support**

Add terminal overview types and client helpers, for example:

```ts
export interface TerminalWorkspaceSummary {
  group_id: string
  group_name: string
  chat_accessible: boolean
  session: TerminalSessionResponse | null
}
```

plus:

- `getTerminalOverview(token)`
- `useTerminalOverviewQuery()`

**Step 2: Implement the page**

Render:

- operator-only empty/loading/forbidden/unavailable states
- summary cards for active, detached, closed/exited, and no-session workspaces
- a workspace table/card list with session metadata
- `Open in Chat` only when `chat_accessible` is true

**Step 3: Run frontend lint/build to verify green**

Run: `cd web && npm run lint`

Expected: PASS

Run: `cd web && npm run build`

Expected: PASS

### Task 5: Add Minimal Chat Workspace Deep Link Support

**Files:**
- Modify: `web/src/components/chat/ChatPanel.tsx`

**Step 1: Write the smallest navigation behavior**

Teach `ChatPanel` to read `/chat?workspace=<group_id>` on initial load and, when that workspace exists in the already-visible group list:

- select it as the current workspace
- sync it into the existing local storage key

Do not add room deep links or change websocket/run behavior.

**Step 2: Verify the integration still builds**

Run: `cd web && npm run build`

Expected: PASS

### Task 6: Refresh Handoff, Run Regression, And Commit

**Files:**
- Modify: `docs/progress.md`

**Step 1: Refresh handoff context**

Record in `docs/progress.md`:

- `M8.3` scope
- new planning docs
- latest verification evidence
- the next direct execution step

**Step 2: Run focused verification**

Run: `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`

Expected: PASS

Run: `cd web && npm run lint`

Expected: PASS

Run: `cd web && npm run build`

Expected: PASS

**Step 3: Run full regression**

Run: `.venv/bin/pytest -o addopts='' -q`

Expected: PASS

Run: `.venv/bin/ruff check .`

Expected: PASS

Run: `git diff --check`

Expected: PASS

**Step 4: Commit**

```bash
git add docs/plans/2026-03-15-m8-3-terminal-operator-ux-design.md docs/plans/2026-03-15-m8-3-terminal-operator-ux.md docs/progress.md services/terminal_sessions.py domain/schemas.py app/routes/terminals.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py web/src/App.tsx web/src/components/layout/AppLayout.tsx web/src/api/client.ts web/src/hooks/useApi.ts web/src/pages/Terminals.tsx web/src/components/chat/ChatPanel.tsx web/src/index.css
git commit -m "feat(terminal): add M8.3 operator overview surface"
```
