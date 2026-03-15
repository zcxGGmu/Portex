# M8.2 Terminal UI Design

## Goal

Add the first browser-usable terminal surface for Portex by shipping a Web terminal panel that reuses the existing `M8.1` terminal session backend.

## Scope

- add a terminal panel to the current Web chat surface
- reuse `POST/GET/DELETE /terminals/{group_id}/sessions...`
- reuse `/ws/terminals/{session_id}` for terminal I/O
- add one browser-compatible terminal WebSocket authentication path
- support owner/admin create, connect, reconnect, input, and close flows
- show current session metadata, local transcript, and connection state

## Out Of Scope

- no `xterm.js` dependency
- no ANSI escape parsing or full PTY emulation
- no terminal history replay from backend
- no host or OpenAI terminal support
- no forced session takeover or shared ownership
- no file transfer, clipboard sync, or keyboard shortcut matrix
- no DB persistence or durable audit storage for terminal sessions

## Current Gap

`M8.1` delivered the backend session lifecycle, REST contract, and dedicated terminal WebSocket namespace, but Portex still has no browser surface for it.

There is one additional practical gap between `M8.1` and a browser UI: the current terminal WebSocket route authenticates only via `Authorization` header, while browser `WebSocket` clients cannot send arbitrary authorization headers. Without a small compatibility shim, the new UI cannot attach to real sessions.

## Options Considered

### Option A: Add a chat-embedded terminal panel and keep backend changes minimal (recommended)

Pros:

- delivers visible terminal capability now
- stays aligned with the earlier “terminal panel” direction
- keeps the backend contract mostly intact
- limits new work to one small browser-auth compatibility patch plus frontend integration

Cons:

- terminal fidelity remains intentionally basic
- transcript is still local-only and non-persistent

Recommendation: choose this option.

### Option B: Build a separate `/terminal` page first

Pros:

- cleaner layout isolation
- more room for a future richer terminal workspace

Cons:

- duplicates workspace context that already exists in `/chat`
- weakens parity with the previously discussed chat-adjacent terminal panel

Reject.

### Option C: Improve backend fidelity first, then add UI later

Pros:

- stronger protocol baseline before UI work

Cons:

- still leaves users without any terminal surface
- expands scope into resize propagation, persistence, or audit redesign

Reject for `M8.2`.

## Recommended Architecture

### 1. Browser-Compatible WebSocket Auth

Keep existing bearer-header auth for test and non-browser clients, but add an explicit fallback for browser clients:

- accept `access_token` from the terminal WebSocket query string
- continue using the same token decoder and user lookup path
- do not change terminal ownership or permission semantics

This is the minimum backend delta needed to make the existing terminal WebSocket route usable from the browser.

### 2. Frontend API And WebSocket Client Surface

Extend the current frontend client layer with typed terminal helpers:

- `getCurrentTerminalSession(token, groupId)` returning `TerminalSessionResponse | null`
- `createTerminalSession(token, groupId)`
- `closeCurrentTerminalSession(token, groupId)`
- `createTerminalWebSocket(sessionId, accessToken)`

The UI should not call `fetch` or `new WebSocket(...)` ad hoc inside unrelated chat code.

### 3. UI Placement

Add a dedicated `TerminalPanel` component inside the chat page, rendered as a sibling panel below the existing chat composer panel.

Reasons:

- the center column provides enough width for readable shell output
- terminal stays attached to the active workspace context already managed by `ChatPanel`
- side cards remain focused on metadata and operator shortcuts

### 4. UI State Model

The panel should present a conservative state machine:

- `unavailable`: no workspace selected or current role is not `owner/admin`
- `idle`: no terminal session exists for the active workspace
- `busy`: a session exists but is owned by another user
- `disconnected`: a session exists for the current user but no WebSocket is attached
- `connecting`
- `connected`
- `exited` / `closed`

The component should load current session state whenever the active workspace changes and keep transcript state isolated per workspace to avoid cross-workspace bleed.

### 5. Interaction Flow

Recommended happy path:

1. user selects a workspace in chat
2. terminal panel loads current session state
3. if no session exists, user clicks `Start Terminal`
4. frontend calls `POST /terminals/{group_id}/sessions`
5. frontend opens `/ws/terminals/{session_id}?access_token=...`
6. on `terminal.ready`, panel moves to connected state
7. user submits line input through the panel
8. server emits `terminal.output`, `terminal.exit`, or `terminal.error`

Reconnect path:

- if the socket closes unexpectedly, keep the session metadata
- surface a reconnect action while the backend reconnect window is still in effect
- do not implement automatic takeover or hidden retries in this milestone

Close path:

- when WebSocket is connected, send `terminal.close`
- when only detached session metadata exists, call `DELETE /terminals/{group_id}/sessions/current`

### 6. Output Rendering

Use a scrollable plain-text transcript surface:

- append `terminal.output` chunks exactly as received
- preserve whitespace with `white-space: pre-wrap`
- keep transcript local to the browser session
- offer a local `Clear Output` action without touching backend session state

This is intentionally not a full terminal emulator. The UI should describe that limitation explicitly.

### 7. Error Handling

Route and UI behavior should stay explicit:

- `403`: show owner/admin-only message
- `404` on current-session read: treat as “no session”
- `409`: show active owner conflict
- `422`: show unsupported backend/policy message
- unexpected WebSocket close: show disconnected state and reconnect guidance
- `terminal.error`: render as inline terminal error state, not as silent log noise

## Testing Strategy

### Backend

- add a focused route test proving the terminal WebSocket accepts browser-compatible token transport
- keep existing header-based terminal WebSocket tests green

### Frontend

- use the established repo pattern for frontend red-green evidence:
  - first introduce a failing build via new terminal-panel wiring that references unimplemented terminal UI/client helpers
  - then implement the missing pieces and restore `npm run build`
- verify terminal client typing and component integration via `npm run lint` and `npm run build`

### Regression

- run the focused terminal WebSocket backend suite
- run full backend pytest
- run frontend lint and production build
- run Ruff and `git diff --check`

## Completion Signal

`M8.2` is complete when:

- browser clients can authenticate to terminal WebSocket connections
- `/chat` contains a usable terminal panel for owner/admin users
- terminal create/connect/reconnect/close flows work against the existing backend
- current v1 limitations are explicit in the UI
- focused verification and full regression both pass
