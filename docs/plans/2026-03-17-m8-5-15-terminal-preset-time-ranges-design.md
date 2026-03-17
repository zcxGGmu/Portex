# M8.5.15 Terminal Preset Time Ranges Design

## Goal

Add preset quick time ranges to `/terminals` so operators can apply common terminal-history windows with one click while preserving the existing `snapshot_from` / `snapshot_to` API contract and RBAC boundary.

## Scope

- add preset time-range controls to the `/terminals` history filter area
- support the fixed preset set: `1h`, `6h`, `24h`, `7d`, `30d`
- clicking a preset immediately updates the existing local `Snapshot From` / `Snapshot To` controls
- keep timeline and search aligned on the same shared filter state
- preserve current backend history/search APIs, timeline/search pagination, snippet deep links, and detail navigation

## Out Of Scope

- no backend API changes
- no change to `latest.json` or archived snapshot persistence format
- no change to `GET /terminals/{group_id}/sessions/current/history`
- no sort/ranking changes in search results
- no URL query persistence or cross-workspace filter persistence
- no timezone preference persistence or server-side timezone localization

## Context

`main` already includes `M8.5.14`, which added inclusive `snapshot_from` / `snapshot_to` filters for terminal history timeline and search. Operators can now filter history precisely, but the current UX still requires manual `datetime-local` entry even for common incident windows. The next minimal refinement is to add one-click preset ranges on top of the existing shared filter model.

## Approaches Considered

### 1. Frontend-only presets on top of existing time inputs

Add preset buttons in `/terminals` that write to the existing `snapshotFromLocal` / `snapshotToLocal` state and reuse the current request flow.

Pros:

- smallest safe delta
- no backend contract changes
- preserves current UTC conversion path and all compatibility anchors

Cons:

- preset semantics live only in the `/terminals` frontend

### 2. New backend `preset_range` query parameter

Expose preset names in the API and let the backend derive time boundaries.

Pros:

- centralizes preset semantics for future clients

Cons:

- unnecessary API expansion for a page-local UX improvement
- duplicates the existing frontend local-time to UTC boundary

### 3. Frontend presets plus URL/query persistence

Persist preset selection in router state or query params.

Pros:

- sharable links and refresh persistence

Cons:

- expands scope beyond the current incremental search-experience refinement

## Recommended Approach

Use approach 1: implement frontend-only presets that immediately populate the existing time inputs and reuse the current timeline/search request chain.

This keeps the work additive and local to `web/src/pages/Terminals.tsx`, avoids unnecessary backend churn, and directly builds on the `M8.5.14` shared filter state.

## UX And State Design

### Preset Controls

Add a lightweight preset row near the existing `Snapshot From` / `Snapshot To` controls with five options:

- `1h`
- `6h`
- `24h`
- `7d`
- `30d`

### Apply Behavior

When a preset is clicked:

- compute `to = now` in browser-local time
- compute `from = now - preset duration` in browser-local time
- write those values into the existing `snapshotFromLocal` / `snapshotToLocal` filter state
- immediately trigger the existing timeline/search refresh path through normal React state updates

### Shared Filter Contract

Preset application must reuse the same shared filter state that currently drives both:

- timeline requests
- search requests

This keeps timeline/search aligned on one filtered history set and avoids introducing a second time-filter model.

### Reset Behavior

Applying a preset must preserve the current filter-reset semantics used for timeline filter changes:

- `timelineOffset = 0`
- `searchOffset = 0`
- `pendingSearchPageMove = null`
- `detailSessionId = null`
- `pendingMatchTarget = null`

### Manual Override Behavior

After a preset is applied, operators can still manually edit `Snapshot From` and `Snapshot To`.

If the current local values no longer exactly match one of the preset-derived ranges, the UI should clear the active preset selection instead of attempting approximate matching.

### Search Clear Behavior

The existing `Clear` search button should keep its current meaning:

- clear search text and search navigation state
- do not clear timeline/search time filters

### Workspace Switch Behavior

Preset selection should not persist across workspace timeline switches. When the operator closes or opens a different timeline, the current logic that restores empty default filters should remain in place.

## Technical Design

### Frontend-Only Change Surface

Primary implementation surface:

- `web/src/pages/Terminals.tsx`

Supporting helpers may stay in the same file unless extraction becomes clearly necessary.

No backend changes are required in:

- `services/terminal_sessions.py`
- `app/routes/terminals.py`
- `web/src/api/client.ts`
- `web/src/hooks/useApi.ts`

because the preset feature only writes values into the already-supported `snapshotFrom` / `snapshotTo` request fields.

### Time Handling

To keep behavior testable and deterministic, introduce small helper functions for:

- mapping preset keys to durations
- generating local `datetime-local` strings from a `Date`
- deriving `from` / `to` local values from a fixed `now`

This allows focused frontend tests without relying on ambient clock timing.

## Error Handling

- preset application must not introduce new backend error semantics
- invalid manual ranges continue to rely on the existing backend `400` response when `snapshot_from > snapshot_to`
- if local time input conversion yields an invalid value, existing request-building behavior remains unchanged

## Testing Strategy

### Frontend

- add focused tests for preset selection writing the expected local `from` / `to` values
- verify preset application resets pagination/detail/search-navigation state
- verify manual `Snapshot From` / `Snapshot To` edits clear the active preset when values diverge
- keep `npm run lint` and `npm run build` green

### Backend

- no new backend tests are required because the API contract and service semantics remain unchanged

## Completion Signal

`M8.5.15` is complete when:

- `/terminals` exposes `1h` / `6h` / `24h` / `7d` / `30d` preset controls
- clicking a preset immediately updates both `Snapshot From` and `Snapshot To`
- timeline and search continue to reuse the same filtered history state
- manual edits can override preset values and clear the active preset state
- existing terminal history compatibility boundaries remain unchanged
