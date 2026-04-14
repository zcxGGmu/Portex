# M8.5.72 Terminal Overview Empty-State Deduplication Design

## Goal

Remove duplicate empty-state messaging from the `/terminals` overview so operators see one clear empty-state message when no canonical workspaces exist.

## Scope

- frontend-only change in `/terminals`
- deduplicate the overview empty-state messaging when `items.length === 0`
- keep the current overview table, actions, and payloads unchanged

## Out Of Scope

- no backend route changes
- no API client contract changes
- no changes to overview sorting, exports, or terminal actions
- no changes to archive filters, timeline/search/detail state, or terminal history routes
- no new frontend test harness

## Context

The current overview surface renders two empty-state messages for the same condition:

- a paragraph above the table: `No canonical workspaces found.`
- a table-body row: `Terminal overview is empty.`

That duplication adds noise without adding meaning. Since the table already needs an empty-state row for layout consistency, the cleanest fix is to keep the in-table empty state and remove the extra paragraph.

## Approaches Considered

### 1. Remove the extra paragraph and keep the table empty-state row (recommended)

Pros:

- smallest UI change
- keeps the table structure stable
- avoids duplicate messaging

Cons:

- none worth noting

### 2. Remove the table empty-state row and keep only the paragraph

Pros:

- also deduplicates the message

Cons:

- loses the current stable empty table layout
- larger UI change than necessary

### 3. Keep both messages but make one conditional on another state

Pros:

- preserves all current copy

Cons:

- unnecessary complexity for a simple duplication issue

## Recommended Approach

Use approach 1.

Keep the current in-table empty-state row and remove the redundant paragraph above the overview table.

## Frontend Design

In `web/src/pages/Terminals.tsx`:

- remove the standalone `No canonical workspaces found.` paragraph before the overview table
- preserve the existing empty-state table row and its `colSpan`
- do not change overview table headers, rows, or actions

## Error Handling

- preserve the current page-level `actionKey` / `actionError` / `actionNotice` model
- no new network requests
- no new success/failure notices

## Testing Strategy

Frontend RED signal:

- create a small build-breaking reference to a not-yet-defined helper/value in the overview empty-state branch

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: the fix accidentally removes the only visible empty-state message.
  - Mitigation: keep the existing in-table empty-state row unchanged and only remove the redundant paragraph.
- Risk: overview layout changes more than intended.
  - Mitigation: keep the patch scoped to the single conditional paragraph.

## Rollout

Frontend-only operator-surface cleanup. No migration, no API changes, and no behavior change outside the `/terminals` overview empty state.
