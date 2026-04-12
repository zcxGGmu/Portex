# M8.5.66 Terminal Cross-Workspace History Archive Group-Name Prefix Filter Design

## Goal

Add an optional `group_name_prefix` filter to the top-level cross-workspace terminal history archive export so operators can narrow the grouped archive by the displayed workspace name rather than only by canonical `group_id`.

## Scope

- extend `GET /terminals/history/archive` with one optional filter:
  - `group_name_prefix`
- treat `group_name_prefix` as a route-level workspace filter applied to canonical web workspaces before grouped archive loading
- match against the existing top-level `group_name` value using a trimmed, case-insensitive prefix check
- keep the grouped cross-workspace archive item payload shape unchanged
- extend the top-level `filters` object with:
  - `group_name_prefix`
- add one archive-only `Workspace Name Prefix` control near the `/terminals` summary export actions
- reuse the existing archive-only filter state introduced in `M8.5.62` and extended in `M8.5.63` / `M8.5.64` / `M8.5.65`

## Out Of Scope

- no changes to snapshot-level service filtering in `TerminalSessionService`
- no changes to `group_id_prefix`
- no changes to `chat_accessible`
- no changes to `status`
- no changes to `owner_user_id`
- no changes to `session_id_prefix`
- no changes to `snapshot_from` / `snapshot_to`
- no changes to `GET /terminals/export`
- no changes to `GET /terminals/history/export`
- no changes to workspace-scoped timeline/search/detail/export/archive routes
- no grouped archive item payload changes beyond `filters.group_name_prefix`
- no fuzzy matching, substring matching, or dual-field search
- no changes to `latest.json`, persistence layout, search/relevance/ranking semantics, or filenames

## Context

`M8.5.60` introduced the top-level grouped cross-workspace history archive. `M8.5.62` and `M8.5.63` added snapshot-derived top-level filters. `M8.5.64` and `M8.5.65` added route-owned workspace/user-context filters for `chat_accessible` and `group_id_prefix`.

The next useful additive boundary is the human-facing workspace label. Operators already see `group_name` in the top-level overview and grouped archive items, but the archive export can currently only be narrowed by canonical `group_id_prefix`. A small `group_name_prefix` filter closes that usability gap without widening the service boundary.

## Approaches Considered

### 1. Add a route-level `group_name_prefix` filter plus a small top-level `/terminals` control (recommended)

Pros:

- adds real operator value on a human-facing field already present in the payload
- keeps the change additive and narrowly scoped to one export action
- avoids widening `TerminalSessionService` with workspace-selection semantics
- case-insensitive prefix matching is simple and ergonomic

Cons:

- adds one more field to the archive-only filter state

### 2. Reuse `group_id_prefix` only and do not add name-based filtering

Pros:

- no new contract surface

Cons:

- forces operators to remember canonical folder IDs instead of the displayed workspace names
- leaves a visible top-level field unfilterable

### 3. Add fuzzy or substring workspace-name search

Pros:

- more flexible at first glance

Cons:

- broader and less deterministic than needed
- introduces matching rules that do not exist elsewhere on this surface
- harder to explain, document, and test than a simple prefix filter

## Recommended Approach

Use approach 1.

Expose one optional `group_name_prefix` filter on the top-level grouped archive route and wire it only into the top-level grouped archive action. Trim the value, ignore empty input, and filter candidate workspaces by `group_name.casefold().startswith(prefix.casefold())`, leaving service-level history filtering untouched.

## Backend Design

In `app/routes/terminals.py`:

- extend `GET /terminals/history/archive` with:
  - `group_name_prefix`
- trim the incoming string and normalize blank to `None`
- when present, filter canonical web workspaces before calling `list_history_snapshot_archives_by_groups(...)`
- compare against the same `group_name` value already emitted in grouped archive items
- keep current route-owned `group_id_prefix` / `chat_accessible` filtering and snapshot-level `status` / owner / session / time filtering exactly as they are
- extend the top-level `filters` object with:
  - `group_name_prefix`
- keep `404 terminal session not found` when no grouped snapshots remain after applying all filters

In `services/terminal_sessions.py`:

- no code change
- keep `list_history_snapshot_archives_by_groups(...)` responsible only for snapshot-derived filters

## Frontend Design

In `web/src/api/client.ts`:

- extend the top-level archive filter options object with:
  - `groupNamePrefix`
- let `downloadTerminalHistoryArchiveBundle(...)` append `group_name_prefix` when present

In `web/src/pages/Terminals.tsx`:

- extend the existing archive-only filter state with:
  - `groupNamePrefix`
- add one `Workspace Name Prefix` text input above the top-level export actions
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

- `GET /terminals/history/archive` accepts and applies `group_name_prefix`
- the service only receives workspace folders whose display names match the prefix
- response JSON includes top-level `filters.group_name_prefix`

OpenAPI coverage:

- `/terminals/history/archive` exposes:
  - `group_name_prefix`

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
- Risk: case-sensitive matching feels broken on human-facing names.
  - Mitigation: use a narrow but ergonomic case-insensitive prefix match.
- Risk: operators assume the filter searches both `group_id` and `group_name`.
  - Mitigation: keep the label explicit and preserve `group_id_prefix` as a separate, already-existing filter.

## Rollout

Additive backend + frontend operator-surface improvement. No migration, no contract break, and no behavior change outside the top-level grouped archive filtering path.
