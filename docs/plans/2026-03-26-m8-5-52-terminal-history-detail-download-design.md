# M8.5.52 Terminal History Detail Download Design

## Goal

Add a raw terminal-history download action to `/terminals` so operators can export one history snapshot as plain text without changing existing timeline, search, detail, ranking, or RBAC behavior.

## Scope

- add one additive backend route:
  - `GET /terminals/{group_id}/sessions/history/{session_id}/download`
- reuse the existing terminal history detail lookup path for snapshot resolution
- return the snapshot output as a downloadable UTF-8 text attachment
- add one download action to the `/terminals` history detail panel
- keep current timeline/search/detail APIs and state transitions unchanged

## Out Of Scope

- no changes to terminal ranking, offline relevance baseline, or search sort
- no changes to `latest.json` or `/sessions/current/history`
- no timeline bulk export or workspace-wide archive download
- no new persistence fields, DTOs, or database schema changes
- no changes to RBAC or workspace-access rules
- no frontend file-manager style preview surface for terminal history

## Context

The current `/terminals` surface already lets operators browse timeline entries, search across snapshots, and open one history detail view. The remaining operator rough edge is that the detail panel is read-only inside the browser. When an operator needs to attach raw terminal output to an incident note or inspect it in external tooling, there is no direct export action even though the backend already has the full snapshot output.

This is a good post-convergence step because it adds operator value without touching the dense terminal relevance chain that was just audited and intentionally paused.

## Approaches Considered

### 1. Add one raw text download endpoint plus a detail-panel button (recommended)

Pros:

- smallest additive backend change
- reuses the existing detail lookup and RBAC path
- avoids duplicating snapshot metadata in a second JSON export format
- easy for operators to understand and easy to regression-test

Cons:

- adds one more terminal route

### 2. Reuse the JSON detail route and let the frontend build a text file client-side

Pros:

- no new backend route

Cons:

- forces the browser to fetch metadata and output even when the operator only wants the raw text
- no direct download URL for API clients
- makes filename/content-type behavior a frontend-only convention

### 3. Add workspace-wide export

Pros:

- could support larger audit workflows

Cons:

- broader than the current detail-oriented UX
- introduces scope questions around filters, archives, and size limits

## Recommended Approach

Use approach 1: add a dedicated raw download route that reuses the existing snapshot lookup path and surface it through a download button inside the current detail panel.

## Route Contract

### Path

- `GET /terminals/{group_id}/sessions/history/{session_id}/download`

### Behavior

- require the same terminal operator role checks as the existing terminal history routes
- require the same accessible-workspace resolution as the existing detail route
- reuse `TerminalSessionService.get_history_snapshot_by_group(...)`
- on success:
  - return `200`
  - return `text/plain; charset=utf-8`
  - include a conservative `Content-Disposition: attachment; filename="..."` header
  - response body is exactly the stored snapshot output
- on missing workspace or missing session:
  - preserve the existing `404` behavior

### Filename

Use a deterministic ASCII filename derived from the current workspace/session identity, for example:

- `terminal-history-project-alpha-terminal-session-3.log`

Sanitize any unexpected characters conservatively so the route never emits path-like or quoted garbage in the attachment header.

## Backend Design

In `app/routes/terminals.py`:

- add one small helper to derive a safe attachment filename
- add the new download route beside the existing history detail route
- reuse the current error mapping path so `TerminalSessionNotFoundError` still becomes `404`

No `services/terminal_sessions.py` changes are required because the existing snapshot lookup already returns the exact output payload needed for download.

## Frontend Design

In `web/src/api/client.ts`:

- add one `downloadTerminalHistoryDetail(...)` client helper that returns a `Blob`

In `web/src/pages/Terminals.tsx`:

- add one `Download Output` action to the history detail panel when `detailData` is loaded
- reuse the existing browser download pattern already used by the files page
- keep current search match navigation, detail rendering, and timeline/detail selection behavior unchanged
- route download failures through the page-level action error path

## Testing Strategy

Backend coverage:

- terminal route test proves the new route returns `text/plain`, the raw output body, and an attachment filename
- terminal route test proves missing sessions still return `404`
- OpenAPI route test proves the new path exists and advertises `404`

Frontend verification:

- TypeScript build and lint cover the new client/helper wiring

Regression verification:

- focused terminal route/API tests
- web lint/build
- `git diff --check`

## Risks And Mitigations

- Risk: the attachment filename could include unsafe characters from session/workspace IDs.
  - Mitigation: sanitize the generated filename to a conservative ASCII subset.
- Risk: the new route could accidentally diverge from the existing detail RBAC path.
  - Mitigation: reuse `_require_terminal_role(...)`, `_require_accessible_workspace(...)`, and `get_history_snapshot_by_group(...)` exactly as the detail route does.
- Risk: frontend download errors could silently fail.
  - Mitigation: route failures through the existing page-level action error state.

## Rollout

Additive operator-facing API and UI change only. No migration, no persistence backfill, and no compatibility impact on existing terminal history callers.
