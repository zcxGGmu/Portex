# M8.5.54 Terminal History Bulk JSON Export Design

## Goal

Add a bounded downloadable JSON export for the current filtered terminal-history page so operators can preserve multiple full snapshot detail records outside the browser without changing existing timeline/search/detail/relevance/RBAC behavior.

## Scope

- add `GET /terminals/{group_id}/sessions/history/export`
- reuse the existing timeline query parameters:
  - `limit`
  - `offset`
  - `status`
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`
- keep export size bounded by the same pagination contract already used on the timeline route
- return an `application/json` attachment containing:
  - the current filter/pagination metadata
  - multiple full snapshot detail records for the selected page
- add one current-page JSON export action to the `/terminals` history timeline panel

## Out Of Scope

- no workspace-wide archive export
- no cross-page aggregation or background export job
- no search export in this session
- no ZIP/text bundle format
- no changes to `latest.json`, `/sessions/current/history`, or persistence layout
- no changes to terminal relevance / offline baseline / search sorting

## Context

`M8.5.52` and `M8.5.53` completed the single-snapshot export story by adding text and JSON download actions on the history detail panel. That leaves one operator-surface gap: timeline browsing can already filter and paginate multiple snapshots, but exporting more than one snapshot still requires manual repetition or multiple detail API calls.

The next additive step should therefore stay on the operator surface and move one level up from single-snapshot export:

- preserve current timeline filters and pagination
- export more than one snapshot at a time
- keep the scope bounded so this is not yet a workspace-wide archive feature

This matches the documented post-`M8.5.53` direction toward bulk export / larger-scope metadata export without reopening the converged relevance line.

## Approaches Considered

### 1. Add a bounded bulk JSON export route for the current filtered page (recommended)

Pros:

- directly addresses the documented bulk-export direction
- keeps output size bounded by the current `limit` / `offset` contract
- exports full detail payloads, not just summary rows
- keeps the frontend action model simple because `/terminals` already knows the active timeline filters

Cons:

- requires a small new service helper or equivalent bulk-detail path

### 2. Export only the current timeline summary page

Pros:

- smaller backend delta

Cons:

- weaker operator value because the actual transcript output is missing
- does not fully close the “export multiple snapshots” gap

### 3. Add workspace-wide filtered export

Pros:

- stronger archive story

Cons:

- larger API and UX scope
- output size and long-running request semantics become ambiguous
- more likely to need streaming or background job semantics

### 4. Build bulk JSON client-side from existing detail queries only

Pros:

- no backend route change

Cons:

- browser-only behavior
- duplicates serialization rules in the frontend
- no stable server-owned attachment contract

## Recommended Approach

Use approach 1. Add a dedicated export route that mirrors the existing timeline filters and returns one bounded page of full detail payloads as a JSON attachment, backed by a small service helper that reuses the current filtered snapshot ordering instead of looping through detail lookups one-by-one in the route.

## Route Contract

### Path

- `GET /terminals/{group_id}/sessions/history/export`

### Query Parameters

- `limit`
- `offset`
- `status`
- `owner_user_id`
- `session_id_prefix`
- `snapshot_from`
- `snapshot_to`

### Semantics

- applies the same auth and workspace-access checks as the existing timeline/detail/download routes
- applies the same filter and pagination semantics as `GET /terminals/{group_id}/sessions/history`
- keeps export size bounded by the selected page size
- returns `application/json`
- returns an attachment filename ending with `.json`

### Response Shape

Return a JSON object containing:

- `group_id`
- `limit`
- `offset`
- `total`
- `has_more`
- `filters`
- `items`
  - each item is the same payload shape as `TerminalSessionHistoryDetailResponse`

Missing workspace/history and invalid-filter behavior should stay aligned with the current timeline route:

- same auth checks
- same workspace access checks
- same `404` mapping path
- same `400` mapping for service-level invalid time-range validation

## Backend Design

In `services/terminal_sessions.py`:

- add one small helper that reuses merged snapshot listing plus the existing filter logic
- return a bounded page of `TerminalSessionHistorySnapshot` records together with pagination metadata

In `app/routes/terminals.py`:

- add a helper for bounded bulk-export filenames
- add the new export route beside the existing history collection routes
- reuse `_require_accessible_workspace(...)`
- reuse the new bounded bulk-detail service helper
- reuse `_to_terminal_history_detail_response(...)` for each exported item

No persistence or ranking change is required.

## Frontend Design

In `web/src/api/client.ts`:

- add `downloadTerminalHistoryExport(...)`
- reuse the existing timeline query parameter model for the export request

In `web/src/pages/Terminals.tsx`:

- add one export action in the timeline panel
- clearly scope it to the current filtered page
- reuse the existing page-level `actionKey` / `actionError` / `actionNotice` state
- reuse the existing blob-download browser flow

## Testing Strategy

Service coverage:

- new helper returns the expected filtered bounded page of snapshot details
- empty filtered result still raises `TerminalSessionNotFoundError`

Backend route coverage:

- export returns JSON attachment content and forwards the current filter set
- missing history still returns `404`
- invalid snapshot range still returns `400`
- OpenAPI exposes the new export path with the timeline filter parameters

Frontend verification:

- `npm run build` and `npm run lint` cover the new helper and action wiring

Regression verification:

- focused terminal service + route/API tests
- `ruff`
- web lint/build
- `git diff --check`

## Risks And Mitigations

- Risk: export filter semantics could drift from timeline semantics.
  - Mitigation: reuse the existing filter path and ordering in the service layer instead of rebuilding logic in the route.
- Risk: bounded bulk export could accidentally become unbounded.
  - Mitigation: keep the current page-based `limit` / `offset` contract intact.
- Risk: route implementation could degenerate into avoidable N+1 snapshot lookups.
  - Mitigation: add one bulk-detail page helper in the service and export directly from that result.

## Rollout

Additive operator-facing API/UI change only. No migration and no compatibility break for the existing timeline/detail/search/history contracts.
