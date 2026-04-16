# M8.5.74 Terminal Effective Search Query Input Normalization Design

## Goal

Normalize the `/terminals` search input to the same trimmed effective query value that the page already uses for search requests, query summary copy, detail highlighting, and search export actions.

## Scope

- frontend-only change in `/terminals`
- normalize the controlled search input after submit so it matches the effective trimmed query
- keep existing search request/query behavior unchanged
- treat whitespace-only submit as an empty effective query path

## Out Of Scope

- no backend route or service changes
- no OpenAPI or API-client contract changes
- no search ranking or pagination changes
- no archive filter changes
- no new frontend test harness

## Context

The current search flow already trims whitespace for the effective query:

- `handleSearchSubmit(...)` computes `searchInput.trim()`
- `searchQuery` stores the trimmed value
- `Query:` copy, detail highlighting, search exports, and search request params all use the trimmed query

However, the controlled text input continues to display the raw pre-submit string. That creates a page-local inconsistency:

- input field may show `  error  `
- effective request and `Query:` line both use `error`

That mismatch is similar to the `M8.5.73` owner/session filter inconsistency: the operator-facing field can visually disagree with the effective value already driving the page.

## Approaches Considered

### 1. Snap the controlled search input to the trimmed effective query on submit (recommended)

Pros:

- smallest patch
- aligns visible input with effective query semantics
- preserves current request wiring and query summary behavior

Cons:

- none worth noting

### 2. Trim on every keystroke

Pros:

- input always stays normalized

Cons:

- more intrusive editing experience
- removes the user's raw typing before submit

### 3. Leave the input raw and only keep `Query:` normalized

Pros:

- no code change

Cons:

- keeps the visible inconsistency
- leaves whitespace-only submit looking like an active query in the input box even when the effective query is empty

## Recommended Approach

Use approach 1.

On submit:

- compute the trimmed query exactly as today
- store that trimmed value back into `searchInput`
- continue storing it in `searchQuery`
- only arm the pending first-match target when the effective query is non-empty

## Frontend Design

In `web/src/pages/Terminals.tsx`:

- keep `searchInput` as the raw controlled field while typing
- in `handleSearchSubmit(...)`, write the trimmed value back into `searchInput`
- keep `searchQuery` as the same trimmed value
- set `pendingMatchTarget` to `null` when the effective query is empty

## Error Handling

- preserve the current page-level `actionKey` / `actionError` / `actionNotice` model
- no new network requests
- no new success/failure notices

## Testing Strategy

Frontend RED signal:

- create a small build-breaking reference to a not-yet-defined helper/value in the search submit path

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: submit-time normalization changes the request semantics.
  - Mitigation: keep using the same `trim()` logic already applied today; only align the visible input with that effective value.
- Risk: whitespace-only submit accidentally leaves stale pending match state.
  - Mitigation: explicitly clear pending match targeting when the effective query is empty.

## Rollout

Frontend-only operator-surface consistency fix. No migration, no API changes, and no behavior change outside submit-time alignment of the search input with the already-effective query semantics.
