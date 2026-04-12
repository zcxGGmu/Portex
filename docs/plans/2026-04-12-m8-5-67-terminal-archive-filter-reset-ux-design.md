# M8.5.67 Terminal Archive Filter Reset UX Design

## Goal

Add a small archive-only reset UX on `/terminals` so operators can tell when the top-level archive export is filtered and can clear all archive filters in one action.

## Scope

- frontend-only change in `/terminals`
- add one archive-only active-filter hint in the summary area
- add one archive-only reset action that restores the top-level archive filter state to defaults
- keep the existing archive-only filter fields:
  - `group_name_prefix`
  - `group_id_prefix`
  - `chat_accessible`
  - `status`
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`
- keep `Export History Archive JSON` as the only action that consumes these filters

## Out Of Scope

- no backend route changes
- no API client contract changes
- no changes to `GET /terminals/history/archive`
- no changes to `GET /terminals/export`
- no changes to `GET /terminals/history/export`
- no changes to workspace-scoped timeline/search/detail surfaces
- no automatic submit/export on reset
- no persistence of filter state across page reloads
- no new frontend test harness

## Context

`M8.5.62` through `M8.5.66` progressively expanded the archive-only top-level filter state to cover snapshot filters plus route-owned workspace filters. The resulting summary area is now useful but denser:

- workspace name prefix
- workspace id prefix
- chat access
- status
- owner user id
- session id prefix
- snapshot from
- snapshot to

Operators can filter the top-level archive precisely, but they still have to manually clear each field and cannot immediately tell from the summary copy whether they are exporting filtered or unfiltered data. The next useful step is therefore a small UX pass rather than another filter.

## Approaches Considered

### 1. Add an archive-only active-filter hint plus one `Clear Archive Filters` action (recommended)

Pros:

- solves the actual operator pain point directly
- keeps the change frontend-only
- preserves existing export semantics and action model
- easy to verify and explain

Cons:

- adds one more small control in the summary area

### 2. Add only a reset button

Pros:

- smallest possible UI delta

Cons:

- still leaves the current filtered/unfiltered state implicit

### 3. Automatically clear archive filters after each export

Pros:

- reduces stale-filter risk

Cons:

- surprising behavior
- makes repeated filtered exports annoying
- changes current page-state semantics too much

## Recommended Approach

Use approach 1.

Add one small summary line that indicates whether archive filters are active and how many fields are currently narrowing the export, plus one `Clear Archive Filters` ghost button that resets the archive-only state to `DEFAULT_ARCHIVE_FILTERS`.

## Frontend Design

In `web/src/pages/Terminals.tsx`:

- derive a small archive-filter activity summary from the existing archive-only state
- count active fields after trimming string inputs and ignoring empty/default values
- show:
  - `Archive export is unfiltered.` when nothing is active
  - `Archive export is filtered by N field(s).` when any archive filters are active
- add one `Clear Archive Filters` button near the top-level export actions
- disable that button when:
  - an action is already in progress, or
  - the archive filters are already at defaults
- resetting clears only the archive-only state
- timeline/search/detail state remains untouched

## Error Handling

- preserve the current page-level `actionKey` / `actionError` / `actionNotice` model
- reset should not trigger network requests
- reset should not emit failure/success notices
- keep the current export/download wording unchanged

## Testing Strategy

Frontend RED signal:

- create a small build-breaking reference to a not-yet-defined archive reset helper or activity value

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: reset accidentally affects timeline or search filters.
  - Mitigation: keep the implementation scoped to `archiveFilters` and `DEFAULT_ARCHIVE_FILTERS` only.
- Risk: the active-filter count feels inconsistent with backend semantics.
  - Mitigation: count only fields that actually alter the outgoing archive query options.
- Risk: extra UI noise in the summary area.
  - Mitigation: keep the hint to one short line and one small reset control.

## Rollout

Frontend-only operator-surface improvement. No migration, no API changes, and no behavior change outside the `/terminals` summary archive filter UX.
