# M8.5.5 Terminal Active Session Persistence And Recovery Design

## Goal

Recover active terminal session state across process restart so `current`/ownership semantics survive restart, while keeping existing HTTP/WebSocket contracts unchanged.

## Scope

- recover persisted active session snapshots (`created` / `attached` / `detached`) into in-memory registry on service startup
- normalize recovered active sessions to `detached` with no reconnect deadline
- lazily re-create/start terminal bridge when a recovered session is attached
- persist session snapshot on active lifecycle mutations (`created`, `attached`, `detached`) in addition to existing output/terminal-state persistence
- keep existing routes, schemas, and websocket protocol unchanged

## Out Of Scope

- no guarantee that the exact pre-restart shell process continues
- no new API/WS message types
- no multi-session persisted inventory or timeline UI
- no ownership policy or permission boundary changes

## Current Gap

`M8.5.4` preserves history snapshots, but active session state is not restored into runtime registry after restart. Result: `GET /sessions/current` loses active continuity and conflict semantics reset unexpectedly.

## Recommended Architecture

### 1. Startup Recovery From Persisted Snapshot

On `TerminalSessionService` init:

- scan persisted `latest.json` under `data/terminal-history/<workspace>/`
- load snapshots with active statuses only (`created` / `attached` / `detached`)
- rehydrate in-memory session maps using recovered record + buffered output history
- normalize status to `detached`, clear reconnect deadline, and keep original `session_id`/owner/workspace metadata

### 2. Lazy Bridge Recovery On Attach

For recovered sessions:

- `bridge` starts as absent
- on first `attach_session()`, create bridge with original identifiers and start it before continuing interactive use
- if bridge start fails, mark session `closed`, persist snapshot, and return failure so client can create a fresh session

### 3. Active-Lifecycle Persistence

Persist snapshot on:

- session creation
- attach
- detach

This keeps restart-time active metadata current even without new output events.

## Risks And Mitigations

- **Risk:** stale active snapshot blocks new owner forever.
  - **Mitigation:** recovered attach failure transitions session to `closed`, enabling fresh create.
- **Risk:** startup recovery loads corrupted files.
  - **Mitigation:** reuse strict persisted snapshot parsing and ignore invalid payloads.
- **Risk:** recovered history breaks bounded-memory contract.
  - **Mitigation:** rehydrate through existing bounded history append path.

## Testing Strategy

### Backend Service

- recover active session without requiring new output
- attach recovered session starts a fresh bridge and replays persisted output
- recovered active session still enforces owner conflict
- attach failure closes recovered session and allows fresh session create

### Routes

- `GET /terminals/{group_id}/sessions/current` works against recovered active session
- `POST /terminals/{group_id}/sessions` still returns `409` when recovered active session belongs to another owner

### Frontend

- no frontend changes in this slice

## Completion Signal

`M8.5.5` is complete when:

- restart can recover active session metadata for a workspace
- recovered sessions are attachable by owner with lazy bridge restart
- conflict/route semantics remain stable
- focused + full regression verification stay green
