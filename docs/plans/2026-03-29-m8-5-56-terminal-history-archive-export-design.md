# M8.5.56 Terminal History Archive Export Design

## Goal

Add an all-pages downloadable JSON archive for the current filtered terminal-history timeline so operators can preserve the full filtered workspace history slice outside the browser without changing existing current-page export, search, detail, relevance, or RBAC behavior.

## Scope

- add `GET /terminals/{group_id}/sessions/history/archive`
- reuse the existing timeline filter parameters:
  - `status`
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`
- export all filtered snapshots for the workspace instead of only the current page
- return an `application/json` attachment containing:
  - `group_id`
  - full filter metadata
  - `total`
  - all matching full snapshot detail records
- add one archive JSON export action to the `/terminals` timeline panel

## Out Of Scope

- no current-page export contract changes
- no search archive export in this session
- no ZIP or text bundle format
- no background job or asynchronous export flow
- no changes to terminal relevance / offline baseline / search sorting
- no changes to `latest.json`, `/sessions/current/history`, or RBAC

## Context

`M8.5.52` through `M8.5.55` completed three bounded operator export layers:

- single-snapshot detail export
- current timeline page bulk export
- current search page export

The remaining obvious operator-surface gap is the page boundary itself. Operators can already narrow the timeline to a precise workspace/status/owner/session/time window, but exporting the entire filtered set still requires stepping page by page and merging files manually.

The next additive step is therefore not another current-page button. It is one timeline-level archive export that:

- reuses the existing timeline filter semantics
- crosses the current-page boundary
- keeps the output as JSON so it remains aligned with the current export family

## Approaches Considered

### 1. Add a filtered all-pages timeline archive route (recommended)

Pros:

- directly addresses the remaining page-boundary gap
- reuses the current timeline filter semantics
- preserves the existing current-page export route unchanged
- keeps the scope narrower than a broader multi-surface archive system

Cons:

- payload size can grow larger than current-page export

### 2. Extend the current-page export route with `scope=all`

Pros:

- fewer routes

Cons:

- mixes two materially different size/behavior contracts into one route
- risks accidental drift in current-page semantics

### 3. Add workspace-wide archive across timeline and search together

Pros:

- broader archive story

Cons:

- too large for the next additive step
- unclear combined payload semantics

### 4. Only polish export UX consistency

Pros:

- smaller frontend-only delta

Cons:

- does not advance the archive/export capability meaningfully

## Recommended Approach

Use approach 1. Add a dedicated timeline archive route that reuses the current filter semantics and returns all filtered full snapshot detail records as one JSON attachment, leaving the current-page export path untouched.

## Route Contract

### Path

- `GET /terminals/{group_id}/sessions/history/archive`

### Query Parameters

- `status`
- `owner_user_id`
- `session_id_prefix`
- `snapshot_from`
- `snapshot_to`

### Semantics

- applies the same auth and workspace-access checks as the existing timeline/export/detail routes
- applies the same filter semantics as `GET /terminals/{group_id}/sessions/history`
- exports all filtered snapshots in the workspace timeline, not only the current page
- returns `application/json`
- returns an attachment filename ending with `.json`

### Response Shape

Return a JSON object containing:

- `group_id`
- `total`
- `filters`
- `items`
  - each item uses the same payload shape as `TerminalSessionHistoryDetailResponse`

Missing workspace/history and invalid filter behavior should stay aligned with the current timeline route:

- same auth checks
- same workspace access checks
- same `404` mapping path
- same `400` mapping for service-level invalid time-range validation

## Backend Design

In `services/terminal_sessions.py`:

- add one helper that returns the full filtered snapshot list for a workspace
- reuse the existing merged snapshot ordering and filter path

In `app/routes/terminals.py`:

- add an archive filename helper
- add the new archive route beside the current timeline export route
- reuse `_require_accessible_workspace(...)`
- reuse the new full-list service helper
- reuse `_to_terminal_history_detail_response(...)` for exported items

No persistence or ranking change is required.

## Frontend Design

In `web/src/api/client.ts`:

- add `downloadTerminalHistoryArchive(...)`
- reuse the existing timeline filter query builder

In `web/src/pages/Terminals.tsx`:

- add one `Export Archive JSON` action in the timeline panel
- keep the existing current-page export button intact
- reuse the existing page-level `actionKey` / `actionError` / `actionNotice` state
- reuse the existing blob-download browser flow

## Testing Strategy

Service coverage:

- new helper returns the expected full filtered list
- empty filtered result still raises `TerminalSessionNotFoundError`

Backend route coverage:

- archive route returns JSON attachment content and forwards the current filter set
- missing history still returns `404`
- invalid snapshot range still returns `400`
- OpenAPI exposes the new archive path with timeline filter parameters

Frontend verification:

- `npm run build` and `npm run lint` cover the new helper and action wiring

Regression verification:

- focused terminal service + route/API tests
- `ruff`
- web lint/build
- `git diff --check`

## Risks And Mitigations

- Risk: archive payloads can become much larger than current-page exports.
  - Mitigation: keep the route scoped to one workspace and one filtered timeline slice, and document that it is the all-pages/export-all path.
- Risk: archive filter semantics could drift from timeline semantics.
  - Mitigation: reuse the existing filter path and ordering in the service layer instead of rebuilding logic in the route.
- Risk: the new route could tempt future route overloading with search/archive semantics.
  - Mitigation: keep this milestone timeline-only and additive.

## Rollout

Additive operator-facing API/UI change only. No migration and no compatibility break for existing current-page export, detail export, timeline, or search contracts.
