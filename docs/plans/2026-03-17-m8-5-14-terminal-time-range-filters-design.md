# M8.5.14 Terminal Time-Range Filters Design

## Goal

Add `snapshot_at` time-range filters to terminal history timeline and search so operators can narrow terminal history to a precise local date-time window.

## Scope

- extend terminal history timeline with optional `snapshot_from` and `snapshot_to` filters
- extend terminal history search with the same optional time-range filters
- keep timeline and search aligned on one shared filter state in `/terminals`
- use minute-granularity local date-time input on the frontend and convert to UTC for API requests
- preserve existing search pagination, snippet deep-linking, and cross-session navigation behavior
- preserve current RBAC/workspace-access boundaries and history compatibility anchors

## Out Of Scope

- no change to `GET /terminals/{group_id}/sessions/current/history`
- no change to `latest.json` / archived snapshot persistence format
- no preset quick ranges (`24h`, `7d`, `30d`) in this milestone
- no sort/ranking changes
- no timezone preference persistence or server-side timezone localization
- no new standalone page outside `/terminals`

## Current Gap

`main` currently includes `M8.5.13`, so operators can filter by status, owner, and session-id prefix. But they still cannot constrain timeline/search to a precise time window based on `snapshot_at`, which makes incident triage noisy once a workspace accumulates a long history tail.

## Recommended Architecture

### 1. Additive Snapshot Time Filters

Extend both:

- `TerminalSessionService.list_history_timeline_by_group(...)`
- `TerminalSessionService.search_history_by_group(...)`

with optional:

- `snapshot_from`
- `snapshot_to`

Both filters apply to `TerminalSessionHistorySnapshot.snapshot_at`.

Semantics:

- `snapshot_from`: inclusive lower bound (`snapshot_at >= snapshot_from`)
- `snapshot_to`: inclusive upper bound (`snapshot_at <= snapshot_to`)
- if both are present and `snapshot_from > snapshot_to`, raise `ValueError`

The service should keep reusing one shared snapshot filter path so timeline and search stay aligned on the same history set.

### 2. Additive API Contract

Extend both routes:

- `GET /terminals/{group_id}/sessions/history`
- `GET /terminals/{group_id}/sessions/history/search`

with optional query parameters:

- `snapshot_from`
- `snapshot_to`

Use UTC datetime strings on the wire.

Behavior:

- workspace has no history snapshots: preserve current `404`
- filters remove every snapshot: preserve current `404`
- filtered snapshot set exists but search query yields no output match: preserve current `200` empty page
- invalid time range (`from > to`): return `400`

### 3. Frontend Time Inputs And Shared State

On `/terminals`, extend the existing filter block with:

- `From` (`datetime-local`)
- `To` (`datetime-local`)

The page keeps local minute-granularity strings in filter state, then converts them to UTC ISO strings before timeline/search requests.

Timeline and search continue to share one filter source of truth. When any time filter changes, reset:

- `timelineOffset`
- `searchOffset`
- `pendingSearchPageMove`
- `detailSessionId`
- `pendingMatchTarget`

This prevents stale detail/search navigation state after the filtered snapshot set changes.

### 4. Compatibility Boundary

Keep unchanged:

- `latest.json` and archived snapshot file formats
- `GET /terminals/{group_id}/sessions/current/history`
- existing search result ordering and pagination shape
- snippet metadata/deep-link behavior
- terminal role/workspace access checks

## Risks And Mitigations

- **Risk:** local `datetime-local` input is interpreted inconsistently.
  - **Mitigation:** treat input as browser-local time and always convert to UTC ISO before sending.
- **Risk:** timeline and search diverge on the time-filtered snapshot set.
  - **Mitigation:** reuse one shared service-side snapshot filter helper.
- **Risk:** ambiguous behavior at exact boundaries.
  - **Mitigation:** document and test inclusive `from` / inclusive `to`.
- **Risk:** invalid ranges produce confusing empty states.
  - **Mitigation:** reject `from > to` with `400` instead of silently returning no results.

## Testing Strategy

### Backend

- service tests for inclusive `snapshot_from`
- service tests for inclusive `snapshot_to`
- service tests for bounded `snapshot_from + snapshot_to`
- service tests for invalid range rejection
- route tests for parameter pass-through and invalid-range `400`
- OpenAPI tests for both routes exposing `snapshot_from` and `snapshot_to`

### Frontend

- search/timeline request helpers accept and send UTC time-range params
- query keys include time-range filters
- filter changes reset stale search/detail state cleanly
- frontend lint/build remain green

## Completion Signal

`M8.5.14` is complete when:

- timeline and search both accept additive `snapshot_from` / `snapshot_to` filters
- `/terminals` exposes local minute-granularity `From` / `To` controls and converts them to UTC requests
- search pagination/navigation/snippet deep links still work within the filtered result set
- compatibility anchors and focused regression remain green
