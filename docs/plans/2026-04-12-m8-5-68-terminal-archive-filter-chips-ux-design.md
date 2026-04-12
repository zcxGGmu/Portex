# M8.5.68 Terminal Archive Filter Chips UX Design

## Goal

Add archive-only active-filter chips on `/terminals` so operators can see exactly which top-level archive filters are active and clear individual filters without manually finding the corresponding inputs.

## Scope

- frontend-only change in `/terminals`
- add archive-only active-filter chips in the summary area
- add per-chip clear actions for the existing archive-only filters:
  - `group_name_prefix`
  - `group_id_prefix`
  - `chat_accessible`
  - `status`
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`
- keep the existing active-filter summary text
- keep the existing `Clear Archive Filters` bulk reset action
- keep `Export History Archive JSON` as the only action that consumes these filters

## Out Of Scope

- no backend route changes
- no API client contract changes
- no changes to `GET /terminals/history/archive`
- no changes to `GET /terminals/export`
- no changes to `GET /terminals/history/export`
- no changes to workspace-scoped timeline/search/detail surfaces
- no persistence of chip state across reloads
- no new frontend test harness

## Context

`M8.5.67` closed the first obvious UX gap by showing whether archive filters are active and adding one-click reset. That improved recovery, but it still leaves one operational blind spot: the operator knows that the archive is filtered, but not which fields are responsible unless they visually scan the whole filter form.

Now that the archive-only state spans workspace name, workspace id, chat access, status, owner, session, and time bounds, the next small but useful step is to surface the active filters directly and make them dismissible one by one.

## Approaches Considered

### 1. Add archive-only active-filter chips with per-chip clear actions (recommended)

Pros:

- solves the remaining visibility gap directly
- preserves the existing bulk reset path
- keeps the change frontend-only
- makes the current filtered state self-explanatory

Cons:

- adds a little more summary UI

### 2. Expand the summary sentence to include raw values

Pros:

- smaller UI delta

Cons:

- awkward for multiple simultaneous filters
- hard to scan and clear selectively

### 3. Only highlight non-default form inputs

Pros:

- very small visual change

Cons:

- still requires scanning the whole form
- weaker than chips for selective clearing

## Recommended Approach

Use approach 1.

Derive a small list of active archive filters from the existing archive-only state, render them as chips in the summary area, and wire each chip to clear only its own field while preserving the rest of the archive filter state.

## Frontend Design

In `web/src/pages/Terminals.tsx`:

- derive a list of active archive filters from the existing archive-only state
- each chip should include:
  - a short label
  - the current value
  - a clear action
- normalize displayed values for readability:
  - `chat_accessible=true` -> `Chat Access: Yes`
  - `chat_accessible=false` -> `Chat Access: No`
  - `status=closed` -> `Status: Closed`
  - text/date filters should show the entered value directly
- keep chip clearing local:
  - only the targeted archive filter resets
  - no network request fires
  - timeline/search/detail state remains untouched
- keep the existing bulk `Clear Archive Filters` action for full reset

## Error Handling

- preserve the current page-level `actionKey` / `actionError` / `actionNotice` model
- chip clear actions should not trigger network requests
- chip clear actions should not emit success/failure notices
- keep current export/download wording unchanged

## Testing Strategy

Frontend RED signal:

- create a small build-breaking reference to a not-yet-defined archive chip list or renderer

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: chip clearing accidentally affects timeline or search filters.
  - Mitigation: keep the implementation scoped to `archiveFilters` only.
- Risk: chip labels become noisy or inconsistent.
  - Mitigation: normalize display labels/values centrally next to the derived chip list.
- Risk: chips duplicate the reset action without adding much value.
  - Mitigation: chips solve selective clearing while the existing reset remains the bulk action.

## Rollout

Frontend-only operator-surface improvement. No migration, no API changes, and no behavior change outside the `/terminals` summary archive filter UX.
