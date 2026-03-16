# M8.5.1 Terminal Output Replay Design

## Goal

Improve terminal reconnect fidelity by replaying recent session output when the owner re-attaches a detached terminal session.

## Scope

- keep an in-memory rolling output history per terminal session
- replay buffered output events immediately after `attach_session()`
- keep current websocket protocol and session ownership semantics
- keep history bounded by configurable max-bytes to avoid unbounded memory growth

## Out Of Scope

- no persistent transcript storage on disk/database
- no ANSI/PTY rendering changes
- no terminal takeover, sharing, or ownership transfer changes
- no new operator API endpoints for transcript/history

## Current Gap

Today, if terminal websocket reconnects, the user only sees new output after reconnect; prior output in the same session is not recoverable unless it still exists in frontend local state.

## Architecture

### 1. Service-Side Rolling Output Buffer

Extend managed terminal session state with:

- `output_history_chunks: deque[str]`
- `output_history_bytes: int`

On each bridge `output` event:

1. append chunk to history
2. increase byte count (UTF-8 bytes)
3. evict oldest chunks while byte count exceeds `history_max_bytes`

### 2. Replay On Attach

During `attach_session()`:

- allocate fresh output queue as today
- enqueue buffered output chunks as `terminal.output` events (in original order)
- then continue with live stream events

This keeps route/websocket code changes minimal and avoids protocol breakage.

### 3. Frontend Transcript Handling

`TerminalPanel` currently keeps transcript by workspace in browser state. With server replay, reconnect would duplicate transcript if local text is kept.

Adjust behavior:

- clear active workspace transcript right before opening a new terminal websocket connection
- let replayed output repopulate transcript

This makes reconnect output deterministic and server-source-of-truth within current process lifetime.

## Risks And Mitigations

- **Risk:** memory growth if output is noisy.
  - **Mitigation:** strict max-bytes cap with eviction.
- **Risk:** reconnect UX duplication.
  - **Mitigation:** clear transcript before connect.
- **Risk:** race between replay and live output.
  - **Mitigation:** enqueue replay under attach lock before returning queue.

## Testing Strategy

### Backend

- add service test: output before detach is replayed on reattach
- add service test: small history cap evicts oldest output chunks

### Frontend

- keep existing terminal panel build/lint checks
- verify no TypeScript or lint regressions after transcript reset logic

## Completion Signal

`M8.5.1` is complete when:

- reconnecting to an existing session replays recent output
- replayed history is bounded by configured byte cap
- frontend reconnect path no longer duplicates transcript due local stale text
- focused tests, full regression, lint/build, and diff hygiene all pass
