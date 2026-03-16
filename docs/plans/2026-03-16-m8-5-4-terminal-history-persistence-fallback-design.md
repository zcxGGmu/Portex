# M8.5.4 Terminal History Persistence Fallback Design

## Goal

Persist bounded terminal output history snapshots to disk and make history reads survive process restart via fallback loading.

## Scope

- persist latest history snapshot per workspace under `data/terminal-history/`
- reuse existing `GET /terminals/{group_id}/sessions/current/history` route
- make `TerminalSessionService.get_history_by_group()` fall back to persisted snapshot when no in-memory session exists
- keep current role/access checks and response shape unchanged

## Out Of Scope

- no active terminal session recovery/re-attach after restart
- no multi-session history timeline or pagination
- no frontend UI changes

## Current Gap

`M8.5.3` added history read API, but it only reads process memory; after service restart, history becomes unavailable.

## Architecture

### 1. File-Backed Snapshot Store

Add persistence in `TerminalSessionService`:

- configurable root: `data/terminal-history` (default)
- per-workspace file: `<root>/<group_folder>/latest.json`
- payload includes session record fields + output/history metadata

### 2. Persist On History Mutations

Persist snapshot when output history changes and when session reaches terminal states (`closed`/`exited`) so latest status is reflected.

### 3. Read Fallback

`get_history_by_group(group_folder)` flow:

1. return in-memory snapshot when current process has session
2. otherwise try loading `<root>/<group_folder>/latest.json`
3. if missing/invalid, raise existing `TerminalSessionNotFoundError`

## Risks And Mitigations

- **Risk:** filesystem path traversal.
  - **Mitigation:** validate all resolved paths against persistence root.
- **Risk:** partial write corruption.
  - **Mitigation:** atomic write via temp file + replace.
- **Risk:** stale persisted snapshot diverges from memory.
  - **Mitigation:** persist on output and terminal-state transitions.

## Testing Strategy

### Backend

- service test: after writing history, a fresh service instance (no sessions) can load persisted snapshot
- service test: missing persisted snapshot still returns not found
- keep existing route tests green (route contract unchanged)

### Frontend

- no changes

## Completion Signal

`M8.5.4` is complete when:

- history snapshot is persisted to disk for terminal sessions
- `get_history_by_group()` returns persisted snapshot after process restart simulation
- focused terminal tests and full regression remain green
