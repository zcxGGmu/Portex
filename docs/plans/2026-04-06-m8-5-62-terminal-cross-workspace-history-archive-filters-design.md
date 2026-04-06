# M8.5.62 Terminal Cross-Workspace History Archive Filters Design

## Goal

Add minimal operator-facing filters to the top-level cross-workspace terminal history archive export so operators can narrow the grouped archive by owner, session prefix, and snapshot time range without changing any other terminal export contract.

## Scope

- extend `GET /terminals/history/archive` with these optional filters:
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`
- keep the grouped cross-workspace archive response shape, but add a top-level `filters` object that echoes the applied filter values
- add a small `/terminals` top-level UI for cross-workspace archive filters near the `Export History Archive JSON` action
- reuse the current local-datetime to UTC conversion logic already used by workspace timeline filters
- preserve existing filename behavior and grouped per-workspace archive payload items

## Out Of Scope

- no changes to `GET /terminals/export`
- no changes to `GET /terminals/history/export`
- no changes to workspace-scoped timeline/search/detail routes
- no `status` filter on the top-level archive in this milestone
- no ZIP/CSV/text bundle format
- no changes to search/relevance/ranking semantics
- no changes to `latest.json`, persistence layout, or history merge order
- no new download state machine or export-center redesign

## Context

`M8.5.60` added `GET /terminals/history/archive` so operators can export the full grouped transcript archive across canonical web workspaces. `M8.5.61` then normalized the `/terminals` export UX and consolidated the repeated browser download flow into a shared page-local helper.

The current gap is that the top-level cross-workspace archive is still all-or-nothing. Workspace-scoped timeline/search archive surfaces already support:

- `owner_user_id`
- `session_id_prefix`
- `snapshot_from`
- `snapshot_to`

The service layer also already has a shared `_filter_history_snapshots(...)` helper that implements these semantics. The smallest useful next step is therefore to expose the same filter family on the top-level grouped archive route and give operators a minimal way to set them from `/terminals`.

## Approaches Considered

### 1. Add backend filters plus a small top-level `/terminals` UI for cross-workspace archive only (recommended)

Pros:

- directly useful to operators
- reuses existing filter semantics instead of inventing a new model
- keeps the change narrowly scoped to one top-level export action
- builds on the current shared frontend download helper without redesigning the page

Cons:

- introduces one more small state slice in `Terminals.tsx`

### 2. Add backend filters only and leave the UI unchanged

Pros:

- smallest backend delta

Cons:

- low operator value because the filtered archive is not discoverable from the page
- leaves the top-level archive meaningfully behind the workspace-scoped operator surfaces

### 3. Unify all three top-level exports behind one shared filter model

Pros:

- most systematic top-level operator surface

Cons:

- broader redesign than needed
- would spill into overview/latest-history semantics that do not currently use filters
- unnecessary before there is evidence that those two exports also need narrowing

## Recommended Approach

Use approach 1.

Add filtering only to the top-level cross-workspace history archive route and UI. This closes the current operator gap while staying additive and narrowly aligned with existing workspace-scoped filter semantics.

## Backend Design

In `services/terminal_sessions.py`:

- extend `list_history_snapshot_archives_by_groups(...)` to accept:
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`
- for each workspace folder, reuse `_list_merged_history_snapshots_by_group(...)` followed by `_filter_history_snapshots(...)`
- keep the current behavior of omitting empty workspace entries from the returned mapping
- keep current `ValueError` semantics when `snapshot_from > snapshot_to`

In `app/routes/terminals.py`:

- extend `GET /terminals/history/archive` with matching query parameters
- pass those parameters through to `list_history_snapshot_archives_by_groups(...)`
- keep `404 terminal session not found` when the filtered grouped result is empty
- add a top-level `filters` object to the JSON response:
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`
- serialize datetime filters through the existing UTC serializer used by other terminal history routes

## Frontend Design

In `web/src/api/client.ts`:

- add a small typed options object for top-level archive filters
- let `downloadTerminalHistoryArchiveBundle(...)` accept those optional filters and append matching query params

In `web/src/pages/Terminals.tsx`:

- add one archive-only filter state slice near the top-level summary section:
  - `ownerUserId`
  - `sessionIdPrefix`
  - `snapshotFromLocal`
  - `snapshotToLocal`
- reuse `localDateTimeToUtcIso(...)` for conversion
- place the filter inputs immediately above or beside the top-level export actions so the scope is obvious
- only `Export History Archive JSON` uses these filters
- keep `Export Overview JSON` and `Export Latest Histories JSON` unfiltered

This keeps the UI honest: only the archive export is filter-aware, and the other top-level exports preserve their existing semantics.

## Error Handling

- keep current `400` behavior for invalid time bounds:
  - `snapshot_from must be less than or equal to snapshot_to`
- keep current `404` behavior when the filtered cross-workspace archive has no matching snapshots
- keep current page-level `actionKey` / `actionError` / `actionNotice` model
- do not add a separate top-level archive form submit flow; the export button remains the action trigger

## Testing Strategy

Service coverage:

- `list_history_snapshot_archives_by_groups(...)` applies owner/session/time filters to each workspace archive
- invalid time bounds raise the existing `ValueError`
- workspaces filtered to zero items are omitted from the mapping

Route coverage:

- `GET /terminals/history/archive` forwards filter params to the service
- response includes grouped filtered items plus top-level `filters` metadata
- invalid time bounds return `400`
- filtered no-match result returns `404`

OpenAPI coverage:

- `/terminals/history/archive` exposes:
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: top-level archive filtering drifts from workspace-scoped filtering semantics.
  - Mitigation: route and service layers reuse the existing filter helper and serializer patterns.
- Risk: users may assume the other top-level exports are also filtered.
  - Mitigation: limit the new filter inputs to the archive action area and keep overview/latest-history actions visually separate.
- Risk: adding `status` now would widen the change into a broader top-level export redesign.
  - Mitigation: explicitly exclude `status` in this milestone and revisit only if real operator demand appears.

## Rollout

Additive backend + frontend operator-surface improvement. No migration and no compatibility break for any existing terminal export or download contract.
