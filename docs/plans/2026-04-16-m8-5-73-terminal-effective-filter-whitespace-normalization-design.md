# M8.5.73 Terminal Effective Filter Whitespace Normalization Design

## Goal

Normalize `/terminals` owner/session text filters so the page-local query wiring, archive summary, and active-filter chips reflect the same trimmed effective filter values the backend already applies.

## Scope

- frontend-only change in `/terminals`
- normalize `owner_user_id` and `session_id_prefix` text filters before they become effective query parameters
- align archive filter summary/chips with the normalized effective values
- keep timeline/search/archive route contracts unchanged

## Out Of Scope

- no backend route or service changes
- no OpenAPI or API-client contract changes
- no new archive filter fields
- no changes to search ranking, exports, RBAC, or file names
- no new frontend test harness

## Context

The current terminal backend already trims `owner_user_id` and `session_id_prefix` when filtering history snapshots. However, `web/src/pages/Terminals.tsx` still derives page-local query options and archive chips from raw text input:

- whitespace-only owner/session input is shown as an active archive filter even though the backend treats it as unset
- leading/trailing spaces can make the archive summary/chip labels differ from the effective filter value
- timeline/search/archive paths do not share one explicit frontend normalization rule for these text filters

This is not a backend bug, but it is a frontend consistency bug because the operator-facing summary can claim filters are active when the effective backend request is unfiltered.

## Approaches Considered

### 1. Normalize the relevant text filters in `Terminals.tsx` and reuse the normalized values everywhere they become effective (recommended)

Pros:

- smallest change
- keeps backend contracts untouched
- makes archive summary/chips match the effective request semantics
- keeps timeline/search/archive behavior aligned

Cons:

- adds one more small frontend helper

### 2. Push the normalization into API client helpers

Pros:

- centralizes request encoding

Cons:

- does not solve the page-local archive summary/chip inconsistency by itself
- expands scope beyond the one page that owns the UI state

### 3. Leave frontend state raw and only fix archive chips

Pros:

- even smaller patch

Cons:

- keeps query-option wiring inconsistent across timeline/search/archive
- leaves the page with multiple effective-filter rules instead of one

## Recommended Approach

Use approach 1.

Add one small page-local helper that trims optional text filters and returns `undefined` for empty results. Reuse it for:

- archive query options
- timeline query options
- search query/archive options
- archive chip derivation

## Frontend Design

In `web/src/pages/Terminals.tsx`:

- add a small helper for optional text-filter normalization
- derive normalized archive owner/session values before building query options
- derive normalized timeline owner/session values before building timeline/search query options
- build archive chips from normalized values so whitespace-only input does not create fake active filters
- keep raw input state unchanged while the operator is typing

## Error Handling

- preserve the current page-level `actionKey` / `actionError` / `actionNotice` model
- no new network requests
- no new success/failure notices

## Testing Strategy

Frontend RED signal:

- create a small build-breaking reference to a not-yet-defined normalization helper where the owner/session filter values become effective

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: the frontend accidentally changes filter semantics beyond whitespace trimming.
  - Mitigation: keep the helper limited to `trim()` plus empty-to-`undefined`, matching existing backend behavior.
- Risk: archive chip state no longer matches raw input fields while the user types spaces.
  - Mitigation: that is the intended correction because chips should describe effective filters, not raw text noise.

## Rollout

Frontend-only operator-surface consistency fix. No migration, no API changes, and no behavior change outside the effective normalization of existing owner/session text filters on `/terminals`.
