# M8.5.65 Terminal Cross-Workspace History Archive Group-Prefix Filter Design

## Goal

Add an optional `group_id_prefix` filter to the top-level cross-workspace terminal history archive export so operators can narrow the grouped archive to one workspace family or naming slice without changing snapshot-level history semantics.

## Scope

- extend `GET /terminals/history/archive` with one optional filter:
  - `group_id_prefix`
- treat `group_id_prefix` as a route-level workspace filter applied to canonical web workspaces before grouped archive loading
- match against the existing top-level `group_id` / workspace folder value using a simple case-sensitive prefix check
- keep the grouped cross-workspace archive item payload shape unchanged
- extend the top-level `filters` object with:
  - `group_id_prefix`
- add one archive-only `Workspace Prefix` control near the `/terminals` summary export actions
- reuse the existing archive-only filter state introduced in `M8.5.62` and extended in `M8.5.63` / `M8.5.64`

## Out Of Scope

- no changes to snapshot-level service filtering in `TerminalSessionService`
- no changes to `chat_accessible`
- no changes to `status`
- no changes to `owner_user_id`
- no changes to `session_id_prefix`
- no changes to `snapshot_from` / `snapshot_to`
- no changes to `GET /terminals/export`
- no changes to `GET /terminals/history/export`
- no changes to workspace-scoped timeline/search/detail/export/archive routes
- no grouped archive item payload changes beyond `filters.group_id_prefix`
- no fuzzy matching, substring matching, or group-name matching
- no changes to `latest.json`, persistence layout, search/relevance/ranking semantics, or filenames

## Context

`M8.5.60` introduced the top-level grouped cross-workspace history archive. `M8.5.62` and `M8.5.63` added snapshot-derived top-level filters. `M8.5.64` added the route-owned `chat_accessible` filter.

The next useful additive boundary is workspace identity itself. Operators may need to export only one naming family such as `project-` or `customer-a-` without narrowing by snapshot owner/session/time. This dimension already exists in the grouped archive item shape as `group_id`, so the filter belongs in the route layer, not in `TerminalSessionService`.

## Approaches Considered

### 1. Add a route-level `group_id_prefix` filter plus a small top-level `/terminals` control (recommended)

Pros:

- adds real operator value on a workspace boundary already present in the payload
- keeps the change additive and narrowly scoped to one export action
- avoids widening `TerminalSessionService` with workspace-selection semantics
- straightforward to reason about and test

Cons:

- adds one more field to the archive-only filter state

### 2. Add a service-level workspace-prefix filter

Pros:

- might look symmetrical with snapshot-level filters

Cons:

- wrong ownership boundary because workspace selection happens before grouped archive loading
- would couple the service to top-level route concerns
- less elegant than filtering candidate workspaces before the service call

### 3. Add a fuzzy workspace-name search filter

Pros:

- potentially friendlier for operators

Cons:

- broader and more ambiguous than needed
- introduces matching rules that do not exist elsewhere on this surface
- harder to explain, document, and test than a simple prefix filter

## Recommended Approach

Use approach 1.

Expose one optional `group_id_prefix` filter on the top-level grouped archive route and wire it only into the top-level grouped archive action. Trim the value, ignore empty input, filter candidate workspaces by `group_id.startswith(prefix)`, and leave service-level history filtering untouched.

## Backend Design

In `app/routes/terminals.py`:

- extend `GET /terminals/history/archive` with:
  - `group_id_prefix`
- trim the incoming string and normalize blank to `None`
- when present, filter canonical web workspaces before calling `list_history_snapshot_archives_by_groups(...)`
- keep current route-owned `chat_accessible` filtering and snapshot-level `status` / owner / session / time filtering exactly as they are
- extend the top-level `filters` object with:
  - `group_id_prefix`
- keep `404 terminal session not found` when no grouped snapshots remain after applying all filters

In `services/terminal_sessions.py`:

- no code change
- keep `list_history_snapshot_archives_by_groups(...)` responsible only for snapshot-derived filters

## Frontend Design

In `web/src/api/client.ts`:

- extend the top-level archive filter options object with:
  - `groupIdPrefix`
- let `downloadTerminalHistoryArchiveBundle(...)` append `group_id_prefix` when present

In `web/src/pages/Terminals.tsx`:

- extend the existing archive-only filter state with:
  - `groupIdPrefix`
- add one `Workspace Prefix` text input above the top-level export actions
- only `Export History Archive JSON` uses this value
- keep `Export Overview JSON` and `Export Latest Histories JSON` unfiltered

## Error Handling

- preserve current `400` behavior for invalid time bounds
- preserve current `404` behavior when no grouped snapshots match
- preserve current `403` operator-role boundary
- preserve the current page-level `actionKey` / `actionError` / `actionNotice` model
- do not add any separate top-level archive submit/reset flow

## Testing Strategy

Route coverage:

- `GET /terminals/history/archive` accepts and applies `group_id_prefix`
- the service only receives the matching workspace folders
- response JSON includes top-level `filters.group_id_prefix`

OpenAPI coverage:

- `/terminals/history/archive` exposes:
  - `group_id_prefix`

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: workspace-selection logic drifts into snapshot-level service code.
  - Mitigation: keep the filter entirely in the route layer and document why the service remains unchanged.
- Risk: operators expect fuzzy or case-insensitive matching.
  - Mitigation: keep the contract explicit and narrow: simple prefix match on `group_id`.
- Risk: top-level archive behavior drifts from the visible grouped payload.
  - Mitigation: filter on the same `group_id` value already returned in grouped archive items.

## Rollout

Additive backend + frontend operator-surface improvement. No migration, no contract break, and no behavior change outside the top-level grouped archive filtering path.
