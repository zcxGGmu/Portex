# M8.1 Terminal Session Backend Design

## Goal

Introduce a first real terminal milestone for Portex by implementing a backend-only terminal session service and protocol, without shipping any frontend terminal UI.

## Scope

- add a backend-owned terminal session lifecycle service
- add authenticated terminal session APIs for create/read/delete
- add a dedicated terminal WebSocket protocol for input/output/resize/close
- support terminal attach only for `docker_container` workspaces
- enforce workspace access, role, ownership, and reconnect rules
- add focused backend/service/route tests

## Out Of Scope

- no terminal panel UI
- no `xterm.js` or browser terminal rendering
- no `openai_runtime` terminal support
- no `host_process` terminal support
- no terminal session DB persistence
- no multi-user shared terminal ownership
- no file transfer, clipboard sync, or terminal history replay features

## Current Gap

`M7.5.5` explicitly deferred terminal parity until Portex had dedicated backend/session/protocol boundaries. That decision is still correct: the current `/ws/{group_folder}` route is message-stream oriented, and the current execution plane only models prompt/response runs.

Portex currently lacks:

- terminal session ownership model
- terminal-specific REST API
- terminal-specific WebSocket namespace
- execution-backend gating for terminal support
- container attach bridge for interactive shell I/O

## Options Considered

### Option A: Backend-only terminal session milestone, container-only v1 (recommended)

Pros:

- satisfies the actual missing prerequisite identified in `M7.5.5`
- keeps the first terminal cut bounded and testable
- avoids prematurely freezing a frontend protocol through a UI implementation
- avoids host-mode safety expansion

Cons:

- users still will not see a terminal UI after this milestone

Recommendation: choose this option.

### Option B: Backend session service plus thin placeholder frontend

Pros:

- gives immediate visible progress in Web

Cons:

- encourages premature coupling between unstable protocol and UI
- still does not provide a meaningfully usable terminal experience

Reject.

### Option C: Full terminal feature with backend + frontend in one milestone

Pros:

- closes the visible gap in one step

Cons:

- mixes protocol, permission, ownership, backend attach, and UI concerns at once
- too much regression surface for a first terminal milestone

Reject.

## Recommended Architecture

### 1. Session Model

Add an in-memory `TerminalSessionService` that owns a registry keyed by workspace folder and session id.

Each session tracks at least:

- `session_id`
- `group_id` / `group_folder`
- `owner_user_id`
- `backend`
- `container_name`
- `status`
- `created_at`
- `last_attached_at`
- `reconnect_deadline`

Status progression for v1:

- `created`
- `attached`
- `detached`
- `closed`
- `exited`

Sessions are process-local only. Server restart invalidates active terminals.

### 2. Backend Gating

Terminal v1 only supports workspaces whose execution backend resolves to `docker_container`.

Rules:

- `docker_container`: supported
- `openai_runtime`: reject as unsupported
- `host_process`: reject as disabled by current policy

This keeps terminal enablement explicit and aligned with the earlier boundary decision.

### 3. Ownership And Permission Rules

- terminal APIs require authenticated user context
- caller must pass workspace access checks
- only `owner` / `admin` may create or control terminal sessions
- one active session per workspace
- the owning user may reconnect to their own detached session
- another authorized user receives conflict instead of forced takeover

This is intentionally conservative for v1.

### 4. Transport Split

Do not reuse `/ws/{group_folder}`.

Add:

- REST routes under `/terminals/{group_id}/sessions`
- dedicated WebSocket route under `/ws/terminals/{session_id}`

The terminal WebSocket namespace carries only terminal messages:

Client -> server:

- `terminal.input`
- `terminal.resize`
- `terminal.close`

Server -> client:

- `terminal.ready`
- `terminal.output`
- `terminal.exit`
- `terminal.error`

### 5. Container Bridge

Use a dedicated bridge abstraction owned by the terminal service.

For production, v1 bridge behavior is:

- resolve target container name for the workspace
- start a long-lived `docker exec` interactive shell bridge
- read output asynchronously
- write input and resize signals through the bridge
- terminate the bridge when the session closes or the reconnect window expires

Implementation should be structured behind an interface so tests can use fakes without requiring real Docker I/O.

### 6. Reconnect Model

When the client disconnects:

- session enters `detached`
- bridge remains alive for a short reconnect window
- recommended default: 30 seconds

If the owner reconnects before deadline:

- session returns to `attached`

If deadline expires:

- bridge is closed
- session transitions to `closed`

This makes terminal sessions resilient to transient browser/network drops without introducing persistence complexity.

## API Contract

### REST

- `POST /terminals/{group_id}/sessions`
  - create or reuse the owner's terminal session for that workspace
- `GET /terminals/{group_id}/sessions/current`
  - read current terminal session status
- `DELETE /terminals/{group_id}/sessions/current`
  - explicitly close current session

### Error Semantics

- `400`: malformed request payload
- `403`: authenticated but role is not allowed
- `404`: workspace missing or inaccessible
- `409`: conflicting active session owned by another user
- `422`: backend unsupported or current policy disabled

WebSocket protocol errors should surface as `terminal.error` events instead of silently closing the socket.

## Audit Boundary

Record at least these events:

- session created
- session connected
- session disconnected
- session closed
- session exited
- session error

If full persistent audit integration is too heavy for the first slice, keep the event model explicit in the service and route layer so persistence can be added later without redesigning semantics.

## Testing Strategy

### Service Tests

- backend gating
- workspace access/role enforcement hooks
- session conflict behavior
- owner reconnect behavior
- reconnect-timeout auto close

### Route Tests

- REST `403/404/409/422`
- WebSocket message validation
- terminal protocol event emission
- close/error paths

### Non-Goals For Verification

- no real Docker e2e dependency in test suite
- use fake terminal bridges / fake async processes

## Completion Signal

`M8.1` is complete when:

- backend-only terminal session lifecycle exists
- dedicated REST and WebSocket terminal contracts exist
- terminal support is gated to `docker_container` workspaces
- owner/admin + workspace access rules are enforced
- reconnect window semantics work
- focused tests and project regression pass
