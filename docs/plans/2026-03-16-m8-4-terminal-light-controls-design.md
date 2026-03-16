# M8.4 Terminal Light Controls Design

## Goal

Add the first minimal control actions to the operator terminal overview so operators can resolve stale or blocked terminal sessions without leaving `/terminals`.

## Scope

- add minimal terminal control actions on `/terminals`
- support `close` for the current operator's own active session from overview
- support `force close` for active sessions through a dedicated backend API
- preserve current session lifecycle and websocket protocol boundaries

## Out Of Scope

- no terminal protocol/fidelity changes (no PTY/ANSI/history/resize redesign)
- no persistent terminal session registry
- no takeover or owner transfer semantics
- no audit-log persistence for control actions in this milestone
- no host/openai terminal mode expansion

## Current Gap

`M8.3` provides read-only overview and deep-linking, but operators still have to go to chat panel for control operations, and cannot resolve sessions owned by another user through a dedicated operator path.

## Recommended Architecture

### 1. Backend Force-Close Capability

Extend `TerminalSessionService` with a force-close method that:

- resolves current session by workspace folder
- closes the bridge and marks session state as `closed`
- bypasses owner identity checks (used only by operator route)

### 2. New Operator API Endpoint

Add route:

- `DELETE /terminals/{group_id}/sessions/force`

Behavior:

- auth required
- operator role required (`owner/admin`)
- workspace must be accessible under current workspace access gate
- closes any active session for that workspace
- returns same terminal-close response shape to keep frontend simple

### 3. Frontend Operator Controls

On `/terminals` page, add per-row actions:

- `Open in Chat` (existing)
- `Close` for current user's own active sessions when `chat_accessible=true`
- `Force Close` for any active session (operator-only)

After control action succeeds, refresh overview query and show inline notice.

## Error Handling

- route-level `404` when workspace or session not found
- route-level `409` for lifecycle conflicts
- frontend maps `ApiError.detail` to inline error text
- action buttons show loading state while request is in flight

## Testing Strategy

### Backend

- service test: force-close closes session owned by another user
- route tests: new endpoint auth/permission/success/error mapping
- OpenAPI test: new path summary + response codes

### Frontend

- red stage: wire controls against missing client method to force build fail
- green stage: add client method + page handlers + recover build
- keep existing lint/build checks

## Completion Signal

`M8.4` is complete when:

- `/terminals` can close own sessions and force-close active sessions
- backend exposes dedicated `DELETE /terminals/{group_id}/sessions/force`
- focused backend tests pass, frontend lint/build pass, full regression remains green
