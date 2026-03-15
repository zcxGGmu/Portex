# M8.2 Terminal UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a browser-usable Web terminal panel on the chat page by reusing the `M8.1` backend and adding only the minimum browser-compatible WebSocket auth shim.

**Architecture:** Keep the terminal backend/session model intact. Add one small backend compatibility patch so browser WebSocket clients can authenticate, then layer typed frontend terminal client helpers plus a dedicated `TerminalPanel` component into the existing chat shell.

**Tech Stack:** FastAPI, existing auth service, React 19, TypeScript, TanStack Query, existing frontend API/WS helpers, pytest, ESLint, Vite build

---

### Task 1: Add Red-Stage Coverage For Browser-Compatible Terminal WebSocket Auth

**Files:**
- Modify: `tests/app/routes/test_terminal_websocket_routes.py`
- Modify: `app/routes/terminals.py`

**Step 1: Write the failing test**

- add a test that opens `/ws/terminals/{session_id}?access_token=...`
- assert the terminal WebSocket authenticates and emits `terminal.ready`

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/app/routes/test_terminal_websocket_routes.py -q`

Expected: FAIL because the route currently authenticates only via `Authorization` header.

**Step 3: Write minimal implementation**

- extend terminal WebSocket auth parsing to accept query-string `access_token`
- keep existing bearer-header auth path unchanged

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/app/routes/test_terminal_websocket_routes.py -q`

Expected: PASS

### Task 2: Create Frontend Red Stage For Terminal UI Wiring

**Files:**
- Modify: `web/src/components/chat/ChatPanel.tsx`

**Step 1: Write the failing integration wiring**

- import a not-yet-implemented `TerminalPanel`
- render it below the existing chat panel with active workspace/user context

**Step 2: Run build to verify it fails**

Run: `cd web && npm run build`

Expected: FAIL because the terminal component and client helpers do not exist yet.

### Task 3: Implement Frontend Terminal Client Surface

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/api/ws.ts`
- Modify: `web/src/hooks/useApi.ts`

**Step 1: Add typed REST helpers**

- `getCurrentTerminalSession(token, groupId)` returning `TerminalSessionResponse | null`
- `createTerminalSession(token, groupId)`
- `closeCurrentTerminalSession(token, groupId)`

**Step 2: Add terminal WebSocket helper**

- resolve `/ws/terminals/{session_id}?access_token=...`
- keep existing chat WebSocket helpers unchanged

### Task 4: Implement Chat Terminal Panel

**Files:**
- Create: `web/src/components/chat/TerminalPanel.tsx`
- Modify: `web/src/components/chat/ChatPanel.tsx`
- Modify: `web/src/index.css`

**Step 1: Add minimal terminal state model**

- owner/admin gating
- current-session fetch per workspace
- session create/connect/close actions
- local transcript keyed by workspace
- disconnected vs connected UI states

**Step 2: Wire terminal protocol**

- handle `terminal.ready`
- append `terminal.output`
- handle `terminal.exit`
- surface `terminal.error`
- send `terminal.input` and `terminal.close`

**Step 3: Add conservative terminal styling**

- scrollable transcript panel
- compact terminal metadata/status row
- line input form and action buttons
- explicit note that v1 is plain-text and container-only

### Task 5: Verify Frontend Green And Focused Coverage

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run focused verification**

Run: `.venv/bin/pytest tests/app/routes/test_terminal_websocket_routes.py -q`

Expected: PASS

**Step 2: Run frontend verification**

Run: `cd web && npm run lint`

Expected: PASS

Run: `cd web && npm run build`

Expected: PASS

### Task 6: Run Full Regression And Commit Milestone

**Step 1: Run regression**

Run: `.venv/bin/pytest -o addopts='' -q`

Expected: PASS

Run: `.venv/bin/ruff check .`

Expected: PASS

Run: `git diff --check`

Expected: PASS

**Step 2: Refresh handoff**

- record `M8.2` scope, browser-auth shim, and verification evidence in `docs/progress.md`

**Step 3: Commit**

```bash
git add docs/plans/2026-03-15-m8-2-terminal-ui-design.md docs/plans/2026-03-15-m8-2-terminal-ui.md docs/progress.md app/routes/terminals.py tests/app/routes/test_terminal_websocket_routes.py web/src/api/client.ts web/src/api/ws.ts web/src/hooks/useApi.ts web/src/components/chat/ChatPanel.tsx web/src/components/chat/TerminalPanel.tsx web/src/index.css
git commit -m "feat(web): complete M8.2 terminal ui"
```
