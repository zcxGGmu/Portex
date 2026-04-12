# M8.5.64 Terminal Cross-Workspace History Archive Chat-Access Filter Design

## Goal

Add an optional `chat_accessible` filter to the top-level cross-workspace terminal history archive export so operators can narrow the grouped archive to workspaces they can open in chat, or explicitly inspect the ones they cannot.

## Scope

- extend `GET /terminals/history/archive` with one optional filter:
  - `chat_accessible`
- treat `chat_accessible` as a tri-state operator filter:
  - omitted: all workspaces
  - `true`: only workspaces the current operator can access in chat
  - `false`: only workspaces the current operator cannot access in chat
- keep the grouped cross-workspace archive item payload shape unchanged
- extend the top-level `filters` object with:
  - `chat_accessible`
- add one archive-only `Chat Access` control near the `/terminals` summary export actions
- reuse the existing archive-only filter state introduced in `M8.5.62` and extended in `M8.5.63`

## Out Of Scope

- no changes to snapshot-level service filtering in `TerminalSessionService`
- no changes to `status`
- no changes to `owner_user_id`
- no changes to `session_id_prefix`
- no changes to `snapshot_from` / `snapshot_to`
- no changes to `GET /terminals/export`
- no changes to `GET /terminals/history/export`
- no changes to workspace-scoped timeline/search/detail/export/archive routes
- no grouped archive item payload changes beyond `filters.chat_accessible`
- no changes to `latest.json`, persistence layout, search/relevance/ranking semantics, or filenames

## Context

`M8.5.60` introduced the top-level grouped cross-workspace history archive. `M8.5.61` normalized the `/terminals` export UX. `M8.5.62` added archive-only owner/session/time filters, and `M8.5.63` added the missing top-level `status` filter.

The remaining useful top-level filter dimension already present in the operator payload is `chat_accessible`. Operators can currently see that flag in the top-level overview and in grouped archive items, but they cannot narrow the archive export by it. Unlike `status`, this flag is derived from the current user and workspace access rules, so the filter belongs in the route layer rather than in `TerminalSessionService`.

## Approaches Considered

### 1. Add a route-level `chat_accessible` filter plus a small top-level `/terminals` control (recommended)

Pros:

- adds real operator value on a dimension that already exists in the payload
- keeps the change additive and narrowly scoped to one export action
- respects the current access-derived semantics instead of pretending this is a snapshot property
- avoids unnecessary service-surface growth

Cons:

- adds one more field to the archive-only filter state

### 2. Add a service-level `chat_accessible` filter

Pros:

- might look symmetrical with snapshot-level filters at first glance

Cons:

- incorrect ownership boundary because `TerminalSessionService` does not know the current user
- would require threading workspace access context into a service that currently operates only on persisted/runtime history snapshots
- makes the implementation less elegant than the problem requires

### 3. Hard-code the top-level archive to only export `chat_accessible=true`

Pros:

- simpler operator story for one use case

Cons:

- would silently change existing export behavior
- removes visibility into inaccessible workspaces that operators may still need to audit
- does not match the additive terminal-operator-surface pattern established by `M8.5.58` to `M8.5.63`

## Recommended Approach

Use approach 1.

Expose one optional boolean `chat_accessible` filter on the top-level grouped archive route and wire it only into the top-level grouped archive action. Compute access once per workspace in the route, reuse that value for both filtering and response payloads, and leave service-level history filtering untouched.

## Backend Design

In `app/routes/terminals.py`:

- extend `GET /terminals/history/archive` with:
  - `chat_accessible`
- define it as an optional boolean query parameter
- compute `chat_accessible` once per canonical web workspace for the current user
- if the filter is provided, narrow the workspace list before calling `list_history_snapshot_archives_by_groups(...)`
- keep current snapshot-level filters (`status`, `owner_user_id`, `session_id_prefix`, `snapshot_from`, `snapshot_to`) exactly as they are
- extend the top-level `filters` object with:
  - `chat_accessible`
- keep `404 terminal session not found` when no grouped snapshots remain after applying all filters

In `services/terminal_sessions.py`:

- no code change
- keep `list_history_snapshot_archives_by_groups(...)` responsible only for snapshot-derived filters

## Frontend Design

In `web/src/api/client.ts`:

- extend the top-level archive filter options object with:
  - `chatAccessible`
- let `downloadTerminalHistoryArchiveBundle(...)` append `chat_accessible=true|false` when present

In `web/src/pages/Terminals.tsx`:

- extend the existing archive-only filter state with:
  - `chatAccessible`
- add one `Chat Access` dropdown above the top-level export actions with:
  - `All workspaces`
  - `Chat accessible only`
  - `No chat access`
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

- `GET /terminals/history/archive` forwards `chat_accessible` into route-level workspace filtering
- `chat_accessible=true` keeps only accessible workspaces
- `chat_accessible=false` keeps only inaccessible workspaces
- response JSON includes top-level `filters.chat_accessible`

OpenAPI coverage:

- `/terminals/history/archive` exposes:
  - `chat_accessible`

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: `chat_accessible` gets treated like a persisted snapshot property.
  - Mitigation: keep the filter entirely in the route layer and document why the service remains unchanged.
- Risk: top-level archive behavior drifts from overview payload semantics.
  - Mitigation: compute the same `user_can_access_group(...)` value already used by `/terminals` and grouped archive items, then reuse it for filtering and payload generation.
- Risk: operators may assume overview/latest-history exports also respect the filter.
  - Mitigation: keep the control in the archive-only filter area and preserve the existing copy that only the archive export uses these filters.

## Rollout

Additive backend + frontend operator-surface improvement. No migration, no contract break, and no behavior change outside the top-level grouped archive filtering path.
