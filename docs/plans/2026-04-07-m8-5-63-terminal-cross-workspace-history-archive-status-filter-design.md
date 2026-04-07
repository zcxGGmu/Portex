# M8.5.63 Terminal Cross-Workspace History Archive Status Filter Design

## Goal

Add the missing `status` filter to the top-level cross-workspace terminal history archive export so operators can narrow the grouped archive by lifecycle status without changing any other terminal export contract.

## Scope

- extend `GET /terminals/history/archive` with one optional filter:
  - `status`
- reuse the existing five workspace-scoped terminal statuses:
  - `created`
  - `attached`
  - `detached`
  - `closed`
  - `exited`
- keep the grouped cross-workspace archive response shape, but extend the top-level `filters` object with `status`
- add one archive-only `Status` control near the `/terminals` summary export actions
- reuse the existing archive-only filter state introduced in `M8.5.62`

## Out Of Scope

- no changes to `owner_user_id`
- no changes to `session_id_prefix`
- no changes to `snapshot_from` / `snapshot_to`
- no changes to `GET /terminals/export`
- no changes to `GET /terminals/history/export`
- no changes to workspace-scoped timeline/search/detail routes
- no grouped archive payload changes beyond `filters.status`
- no new combined or alias statuses such as `active` / `archived`
- no changes to `latest.json`, persistence layout, search/relevance/ranking semantics, or filenames

## Context

`M8.5.60` introduced the top-level grouped cross-workspace history archive. `M8.5.61` normalized the `/terminals` export UX. `M8.5.62` added top-level owner/session/time filters and a small archive-only UI.

The remaining obvious parity gap is `status`. Workspace-scoped history timeline, search, current-page export, and all-pages archive surfaces already support `status`, but the top-level grouped archive still does not. The service layer already centralizes status filtering in `_filter_history_snapshots(...)`, so the smallest useful next step is to thread that same filter through the top-level archive route and UI.

## Approaches Considered

### 1. Add backend `status` filtering plus a small top-level `/terminals` status control (recommended)

Pros:

- closes the last obvious top-level filter gap
- reuses existing service and UI concepts
- keeps the change additive and narrowly scoped to one export action
- provides immediate operator value

Cons:

- adds one more field to the archive-only filter state

### 2. Add backend `status` filtering only

Pros:

- smallest backend delta

Cons:

- low discoverability from the operator page
- leaves the top-level archive behind the workspace-scoped surfaces

### 3. Restrict top-level archive `status` to `closed` / `exited`

Pros:

- feels more archive-oriented at first glance

Cons:

- creates a semantic fork from workspace-scoped filtering
- does not match the actual merged-snapshot behavior of the grouped archive
- adds one more special case to explain and maintain

## Recommended Approach

Use approach 1.

Expose the same five-state `status` filter that workspace-scoped history surfaces already use, and wire it only into the top-level grouped archive action. This keeps top-level and workspace-level operator semantics aligned without broadening the change.

## Backend Design

In `services/terminal_sessions.py`:

- extend `list_history_snapshot_archives_by_groups(...)` to accept:
  - `status`
- pass `status` through to `_filter_history_snapshots(...)`
- keep the current behavior of omitting workspace entries that filter down to zero items
- keep current `ValueError` behavior for invalid time bounds unchanged

In `app/routes/terminals.py`:

- extend `GET /terminals/history/archive` with:
  - `status`
- define it with the same five-value literal constraint already used by workspace-scoped history routes
- pass it through to `list_history_snapshot_archives_by_groups(...)`
- extend the top-level `filters` object with:
  - `status`
- keep `404 terminal session not found` when the grouped result is empty after filtering

## Frontend Design

In `web/src/api/client.ts`:

- extend the top-level archive filter options object with:
  - `status`
- let `downloadTerminalHistoryArchiveBundle(...)` append `status` when present

In `web/src/pages/Terminals.tsx`:

- extend the existing archive-only filter state with:
  - `status`
- add an `All statuses` dropdown above the top-level export actions
- reuse the existing `TERMINAL_HISTORY_STATUS_OPTIONS`
- only `Export History Archive JSON` uses this value
- keep `Export Overview JSON` and `Export Latest Histories JSON` unfiltered

## Error Handling

- preserve current `400` behavior for invalid time bounds
- preserve current `404` behavior when no grouped snapshots match
- preserve the current page-level `actionKey` / `actionError` / `actionNotice` model
- do not add any separate top-level archive submit/reset flow

## Testing Strategy

Service coverage:

- `list_history_snapshot_archives_by_groups(...)` filters grouped snapshots by `status`
- workspaces filtered to zero items are omitted
- existing owner/session/time behavior remains intact

Route coverage:

- `GET /terminals/history/archive` forwards `status`
- response includes top-level `filters.status`
- invalid `status` values are rejected by FastAPI/OpenAPI validation

OpenAPI coverage:

- `/terminals/history/archive` exposes:
  - `status`

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: top-level archive semantics drift from workspace-scoped history semantics.
  - Mitigation: reuse the same five-state literal and the existing `_filter_history_snapshots(...)` helper.
- Risk: operators may assume the other top-level exports are also status-filtered.
  - Mitigation: keep the control inside the archive-only filter area and retain the explicit copy that only the archive export uses these filters.
- Risk: introducing combined/archive-only statuses would widen the change unnecessarily.
  - Mitigation: explicitly reuse the existing five statuses and avoid any new abstractions.

## Rollout

Additive backend + frontend operator-surface improvement. No migration, no contract break, and no behavior change outside the top-level grouped archive filtering path.
