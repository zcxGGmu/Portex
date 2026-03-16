# M8.5.6 Persistence-Aware Terminal History Inventory Design

## Goal

Expose persisted terminal-history inventory in the existing operator overview so operators can see workspace history presence and metadata even when no active in-memory session exists.

## Scope

- augment `GET /terminals` response with per-workspace history summary metadata
- merge in-memory current session history and persisted snapshot fallback into one overview read model
- keep existing terminal create/current/history/close websocket contracts unchanged
- update `/terminals` page to render history summary columns

## Out Of Scope

- no new standalone history-inventory route
- no pagination/timeline of historical snapshots (still latest snapshot only)
- no transcript preview/output text in overview payload
- no terminal ownership/policy changes

## Current Gap

`M8.5.5` already persists and recovers active session state, but `/terminals` overview only reads current in-memory session list. Operators cannot quickly inventory persisted history status across workspaces from one page.

## Recommended Architecture

### 1. Service-Level History Inventory Summary

Add a read helper in `TerminalSessionService`:

- build in-memory history summaries from current managed sessions
- merge persisted snapshots from `data/terminal-history/<workspace>/latest.json` for workspaces not currently in memory
- return compact metadata only (session snapshot + bytes/cap/truncated), no full output payload

### 2. Schema + Route Extension

Extend terminal overview DTO:

- add `history` field to each `TerminalWorkspaceSummaryResponse`
- `history` contains session snapshot + summary metadata
- `list_terminal_overview` maps workspace folder to history summary from new service helper

This is additive to existing `/terminals` response and keeps current route path/guards unchanged.

### 3. Frontend Overview Rendering

Update `/terminals` page:

- display history availability/bytes/truncation and history-session status columns
- keep existing chat deep-link and close/force-close actions unchanged

## Risks And Mitigations

- **Risk:** overview payload grows too large if output text is included.
  - **Mitigation:** summary includes metadata only; output remains accessible via existing history endpoint.
- **Risk:** route fake services in tests break due new method.
  - **Mitigation:** update route tests/fakes and add explicit coverage for history field behavior.
- **Risk:** stale persisted snapshot confusion.
  - **Mitigation:** expose snapshot session status/owner/created timestamp so operator can judge freshness.

## Testing Strategy

### Backend

- service test: inventory merges in-memory and persisted-only summaries
- route test: `/terminals` includes history summary for active and persisted-only workspace records
- OpenAPI test: `TerminalWorkspaceSummaryResponse` includes `history` field

### Frontend

- `web` lint/build validation after terminals page updates

## Completion Signal

`M8.5.6` is complete when:

- `/terminals` returns per-workspace history summary metadata with persisted fallback
- `/terminals` page renders history inventory fields
- focused terminal tests and full regression remain green
