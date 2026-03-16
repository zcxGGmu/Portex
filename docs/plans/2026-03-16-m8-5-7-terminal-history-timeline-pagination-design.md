# M8.5.7 Terminal History Timeline/Pagination Design

## Goal

Add a per-workspace terminal history timeline with pagination so operators can inspect multiple persisted session snapshots instead of only the latest snapshot.

## Scope

- add multi-snapshot persistence inventory under each workspace history root
- add paginated timeline read helper in `TerminalSessionService`
- add `GET /terminals/{group_id}/sessions/history` with `limit/offset`
- keep `/terminals` overview lightweight and additive
- add minimal `/terminals` page on-demand timeline view

## Out Of Scope

- no change to existing `/terminals/{group_id}/sessions/current/history` payload/behavior
- no breaking migration of `latest.json` storage contract
- no ownership/policy/rbac boundary changes
- no transcript search/filter/full-text indexing

## Current Gap

`M8.5.6` exposes only one history summary per workspace (current in-memory or persisted `latest.json`). There is no way to browse older session snapshots, and operators cannot page through workspace terminal history over time.

## Recommended Architecture

### 1. Backward-Compatible Multi-Snapshot Persistence

Keep writing `latest.json` exactly as the current compatibility anchor, and add immutable archived snapshots under:

- `data/terminal-history/<workspace>/snapshots/<session_id>.json`

When session status reaches terminal states (`closed`/`exited`), write/update the archived snapshot for that session. This provides multi-snapshot inventory without changing the existing latest fallback path.

### 2. Service-Level Timeline Read Model

Add a paginated service method:

- `list_history_timeline_by_group(group_folder, *, limit, offset)`

Behavior:

- merge in-memory current snapshot (if any), archived snapshots, and `latest.json`
- dedupe by `snapshot_id` / session id
- stable sort by `snapshot_at` desc then session id
- return page metadata: `limit`, `offset`, `has_more`, `items`
- if no entries exist, raise `TerminalSessionNotFoundError`

### 3. Route + Schema Extension

Add additive timeline DTOs and route:

- `GET /terminals/{group_id}/sessions/history?limit=20&offset=0`

The route reuses existing terminal role gate + workspace access gate + terminal error mapping.

### 4. Frontend On-Demand Timeline View

Keep `/terminals` overview table unchanged for polling cost. Add per-row “View Timeline” action that lazily fetches timeline pages for the selected workspace.

## Risks And Mitigations

- **Risk:** duplicate timeline entries from `latest.json` + archives.
  - **Mitigation:** dedupe by snapshot/session id and keep newest `snapshot_at`.
- **Risk:** malformed persisted files break timeline reads.
  - **Mitigation:** skip malformed entries, preserve best-effort read semantics.
- **Risk:** active-session recovery regression.
  - **Mitigation:** keep recovery path reading `latest.json`; timeline archiving is additive.
- **Risk:** overview polling payload growth.
  - **Mitigation:** timeline remains separate on-demand route.

## Testing Strategy

### Backend

- service tests for archive creation, pagination ordering, legacy `latest.json` fallback, malformed-file tolerance, dedupe semantics
- route tests for auth/access/success/404 and pagination parameters
- OpenAPI tests for new path and timeline schemas

### Frontend

- `/terminals` page renders timeline section only on demand
- frontend lint/build green

## Completion Signal

`M8.5.7` is complete when:

- workspace timeline route returns paginated multi-snapshot history metadata
- existing latest/history contracts remain backward-compatible
- focused terminal tests and full regression remain green
