# M8.5.3 Terminal History Read Surface Design

## Goal

Add a minimal read-only API surface to fetch the current terminal session's buffered output history for one workspace.

## Scope

- expose one terminal history read endpoint under existing terminal route family
- reuse existing in-memory bounded output history built in `M8.5.1`
- keep existing owner/admin role + workspace-access gate semantics
- include explicit history metadata (`output_bytes`, `history_max_bytes`, `truncated`) in response

## Out Of Scope

- no cross-process/session persistence to DB/disk
- no terminal protocol changes or websocket message shape changes
- no takeover/ownership policy changes
- no new frontend page in this slice

## Current Gap

`M8.5.1` buffers and replays output internally, but operators cannot fetch current buffered history through an HTTP read interface.

## Recommended Architecture

### 1. Service Read Snapshot

Extend `TerminalSessionService` with a read helper that returns one history snapshot by workspace:

- locate current session by `group_folder`
- join buffered output chunks in original order
- return session record + byte count + cap + truncation marker

### 2. New Route

Add route:

- `GET /terminals/{group_id}/sessions/current/history`

Behavior:

- auth required
- terminal role required (`owner/admin`)
- workspace must pass existing access gate
- `404` when workspace or current terminal session missing

### 3. Response Contract

Introduce one schema `TerminalSessionHistoryResponse`:

- `session: TerminalSessionResponse`
- `output: str`
- `output_bytes: int`
- `history_max_bytes: int`
- `truncated: bool`

## Risks And Mitigations

- **Risk:** read path races with output append.
  - **Mitigation:** read snapshot under service lock.
- **Risk:** output payload grows unexpectedly.
  - **Mitigation:** bounded by existing `history_max_bytes` cap.
- **Risk:** accidental permission drift.
  - **Mitigation:** reuse existing `_require_terminal_role` + `_require_accessible_workspace` gates.

## Testing Strategy

### Backend

- service test for history snapshot content/metadata and truncation marker
- route tests for auth/permission/success/not-found mapping
- OpenAPI contract test for new route path/summary/responses

### Frontend

- no frontend behavior changes in this milestone

## Completion Signal

`M8.5.3` is complete when:

- terminal history can be fetched via `GET /terminals/{group_id}/sessions/current/history`
- response includes session snapshot and bounded-history metadata
- focused and full backend verification stay green
