# M8.5.8 Terminal History Filters/Detail Design

## Goal

Add server-side timeline filters and per-session history detail so operators can narrow workspace terminal-history timelines and inspect one snapshot in depth.

## Scope

- extend `GET /terminals/{group_id}/sessions/history` with additive server-side filters
- add `GET /terminals/{group_id}/sessions/history/{session_id}` detail read surface
- expose `snapshot_at` on timeline summary items
- add `/terminals` timeline filter controls and in-page detail panel
- keep the current terminal overview and polling model unchanged

## Out Of Scope

- no change to `GET /terminals/{group_id}/sessions/current/history`
- no change to `latest.json` or archived snapshot persistence format
- no transcript full-text search, highlighting, export, download, or delete actions
- no new RBAC or workspace-access behavior
- no dedicated detail page route outside `/terminals`

## Current Gap

`M8.5.7` added timeline pagination, but the operator surface still stops at metadata-only browsing. Users cannot filter the timeline server-side by owner/status/session prefix, and they cannot inspect the full persisted snapshot for one historical terminal session without manually reading files on disk.

## Recommended Architecture

### 1. Filtered Timeline Read Model

Extend `TerminalSessionService.list_history_timeline_by_group(...)` with optional filters:

- `status`
- `owner_user_id`
- `session_id_prefix`

The service keeps the current data-source merge order:

1. in-memory current snapshot
2. persisted `latest.json`
3. archived `snapshots/<session_id>.json`

After loading, it continues to dedupe by `session_id` using the newest `snapshot_at`, then applies filters, then paginates. This preserves the current compatibility behavior while ensuring filters operate across the full workspace timeline instead of only the current page.

### 2. Shared Detail Lookup

Add `TerminalSessionService.get_history_snapshot_by_group(group_folder, session_id)` that reuses the same merged snapshot inventory as the timeline path. The detail route should not reimplement file-path-specific lookup rules because that creates divergence between what the timeline lists and what detail can resolve.

If no matching snapshot exists after merge/dedupe, the service raises `TerminalSessionNotFoundError`, which the route layer already knows how to map to the existing terminal `404`.

### 3. Additive API Contract

Keep the current timeline route and add only optional query parameters:

- `status`
- `owner_user_id`
- `session_id_prefix`

Add a new detail route:

- `GET /terminals/{group_id}/sessions/history/{session_id}`

DTO changes remain additive:

- `TerminalSessionHistorySummaryResponse` gains `snapshot_at`
- `TerminalSessionHistoryDetailResponse` returns the full snapshot payload (`session`, `snapshot_at`, `output`, `output_bytes`, `history_max_bytes`, `truncated`)

### 4. Minimal Operator UX Upgrade

Keep `/terminals` as the only operator page for this workflow. Enhance the existing timeline panel with:

- filter controls for `status`, `owner_user_id`, `session_id_prefix`
- `snapshot_at` column in the timeline table
- `View Details` action on each timeline row
- an in-page detail panel showing metadata and full output text

This gives operators a direct flow: select workspace, narrow results, inspect one snapshot, without changing navigation or introducing another route surface.

## Risks And Mitigations

- **Risk:** filters are applied after pagination, producing misleading partial matches.
  - **Mitigation:** apply filters before `limit/offset`.
- **Risk:** timeline and detail diverge on duplicate/latest/archive resolution.
  - **Mitigation:** use one shared merged snapshot inventory for both.
- **Risk:** adding `snapshot_at` changes existing clients unexpectedly.
  - **Mitigation:** keep it additive on the existing summary schema.
- **Risk:** detail output payloads become large in the page.
  - **Mitigation:** stay within existing bounded snapshot/output persistence limits and avoid introducing cross-workspace bulk detail fetches.

## Testing Strategy

### Backend

- service tests for each timeline filter and filtered pagination
- service tests for detail lookup from in-memory, `latest.json`, and archived snapshots
- route tests for new query parameters, detail success path, and `404` mapping
- OpenAPI tests for new parameters, new detail path, and additive schema fields

### Frontend

- `/terminals` continues to lazy-load timeline data only when selected
- timeline filter changes reset pagination and refetch data
- detail panel renders only on demand
- frontend lint/build stay green

## Completion Signal

`M8.5.8` is complete when:

- operators can filter workspace terminal-history timeline entries server-side
- operators can open one history snapshot detail from `/terminals`
- `latest.json` compatibility and current-history route behavior remain unchanged
- focused terminal tests and full regression remain green
