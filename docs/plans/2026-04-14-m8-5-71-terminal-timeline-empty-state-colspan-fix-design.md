# M8.5.71 Terminal Timeline Empty-State ColSpan Fix Design

## Goal

Fix the `/terminals` history timeline empty-state row so its `colSpan` matches the current 8-column table header.

## Scope

- frontend-only change in `/terminals`
- fix the timeline empty-state row inside the workspace history timeline table
- keep the current timeline columns, filters, actions, and payloads unchanged

## Out Of Scope

- no backend route changes
- no API client contract changes
- no changes to timeline data fetching, pagination, or export behavior
- no changes to archive filters, search/detail state, or overview table rendering
- no new frontend test harness

## Context

The current workspace timeline table renders 8 headers:

- `Session`
- `Status`
- `Owner`
- `Snapshot At`
- `Created`
- `Output Bytes`
- `Truncated`
- `Actions`

But the empty-state row still uses `colSpan={7}`. That is a small UI correctness bug: when the timeline is empty, the fallback cell no longer spans the full table width.

## Approaches Considered

### 1. Update the empty-state row to span all 8 columns (recommended)

Pros:

- fixes the bug directly
- minimal frontend-only patch
- keeps the current table structure intact

Cons:

- none worth noting

### 2. Remove the table wrapper when the timeline is empty

Pros:

- avoids `colSpan` bookkeeping

Cons:

- larger UI change
- unnecessary for a simple alignment bug

## Recommended Approach

Use approach 1.

Keep the current table and empty-state message, and fix the empty-state cell so it spans all current columns.

## Frontend Design

In `web/src/pages/Terminals.tsx`:

- fix the timeline empty-state row so its `colSpan` is `8`
- keep the current message text unchanged
- do not introduce new state or API wiring unless needed for the minimal fix

## Error Handling

- preserve the current page-level `actionKey` / `actionError` / `actionNotice` model
- no new network requests
- no new success/failure notices

## Testing Strategy

Frontend RED signal:

- create a small build-breaking reference to a not-yet-defined constant or helper for the timeline empty-state `colSpan`

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: the patch accidentally touches the wrong table.
  - Mitigation: keep the change scoped to the timeline empty-state row only.
- Risk: future column-count changes can reintroduce the mismatch.
  - Mitigation: route the value through one local constant rather than leaving a stale literal in the row.

## Rollout

Frontend-only correctness fix. No migration, no API changes, and no behavior change outside the `/terminals` timeline empty state.
