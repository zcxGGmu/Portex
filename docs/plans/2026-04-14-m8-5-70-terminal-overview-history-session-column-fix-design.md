# M8.5.70 Terminal Overview History Session Column Fix Design

## Goal

Fix the `/terminals` overview table so the `History Session` column shows the history snapshot session identifier instead of incorrectly displaying the history session status.

## Scope

- frontend-only change in `/terminals`
- fix the `History Session` column rendering in the top-level workspace overview table
- reuse the existing `TerminalWorkspaceSummary.history.session.session_id` data already returned by the API client
- keep all overview sorting, actions, archive controls, and history export surfaces unchanged

## Out Of Scope

- no backend route changes
- no API client contract changes
- no changes to `TerminalWorkspaceSummary`
- no changes to archive filters, timeline/search/detail state, or export behavior
- no new frontend test harness

## Context

The current top-level overview table labels one column `History Session`, but the cell renderer currently uses `item.history.session.status`. That is a correctness bug in the UI rather than a missing capability: the typed payload already includes the correct `session_id` under `history.session.session_id`.

Since the handoff explicitly says not to keep growing the archive surface without evidence, the right next move is a small correctness fix on the existing overview surface.

## Approaches Considered

### 1. Render `history.session.session_id` in the existing column (recommended)

Pros:

- fixes the bug directly
- matches the current column label
- keeps the change minimal and frontend-only

Cons:

- does not surface history status in that cell anymore

### 2. Rename the column to `History Status`

Pros:

- would match current buggy behavior

Cons:

- hides the more useful session identifier
- changes the existing operator-facing meaning of the column instead of fixing the bug

### 3. Render both session id and status in the same cell

Pros:

- exposes more information

Cons:

- expands the surface beyond the bug fix
- unnecessary without operator evidence

## Recommended Approach

Use approach 1.

Keep the column label unchanged and fix the cell renderer to display `item.history.session.session_id`. Leave status information in the existing `Status` column and history volume/truncation columns as they are.

## Frontend Design

In `web/src/pages/Terminals.tsx`:

- change the `History Session` cell to render `item.history.session.session_id`
- preserve the current `-` fallback when `item.history` is missing
- do not add new state, helpers, or contracts unless needed for the minimal fix

## Error Handling

- preserve the current page-level `actionKey` / `actionError` / `actionNotice` model
- no new network requests
- no new success/failure notices

## Testing Strategy

Frontend RED signal:

- create a small build-breaking reference to a not-yet-defined helper/value for the history session cell

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: the fix accidentally changes behavior outside the overview table.
  - Mitigation: keep the patch scoped to the single overview cell renderer.
- Risk: the overview column still becomes ambiguous later if operators want both id and status.
  - Mitigation: treat that as a separate evidence-driven UX request rather than folding it into this bug fix.

## Rollout

Frontend-only correctness fix. No migration, no API changes, and no behavior change outside the `/terminals` overview table.
