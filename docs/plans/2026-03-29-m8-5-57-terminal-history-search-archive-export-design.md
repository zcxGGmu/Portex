# M8.5.57 Terminal History Search Archive Export Design

## Goal

Add an all-pages downloadable JSON archive for the current terminal-history search result set so operators can preserve the full filtered search slice outside the browser without changing existing current-page search export, timeline export/archive, detail export, relevance, or RBAC behavior.

## Scope

- add `GET /terminals/{group_id}/sessions/history/search/archive`
- reuse the existing search parameters:
  - `q`
  - `sort`
  - `status`
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`
- export all filtered matched sessions for the workspace instead of only the current page
- return an `application/json` attachment containing:
  - `group_id`
  - `query`
  - `sort`
  - full filter metadata
  - `total`
  - all matching search-result items in the existing snippet/match shape
- add one search archive JSON export action to the `/terminals` search panel

## Out Of Scope

- no current-page search export contract changes
- no timeline archive changes in this session
- no full snapshot detail expansion inside search archive
- no ZIP or text bundle format
- no background job or asynchronous export flow
- no changes to search ranking, relevance, or snippet construction
- no changes to `latest.json`, `/sessions/current/history`, or RBAC

## Context

`M8.5.52` through `M8.5.56` now cover:

- single-snapshot detail export
- timeline current-page export
- search current-page export
- timeline all-pages archive export

The remaining obvious export gap is the search page boundary. Operators can already narrow search by query, sort, owner, session prefix, and time range, but exporting the full matched result set still requires paging through the UI and merging current-page exports manually.

The next additive step is therefore search archive export:

- preserve the existing search query/filter/sort semantics
- cross the current-page boundary for search
- keep the output in JSON and reuse the current search match/snippet payload

## Approaches Considered

### 1. Add a filtered all-pages search archive route (recommended)

Pros:

- directly closes the remaining search page-boundary gap
- reuses the current search service semantics
- preserves current-page search export unchanged
- avoids conflating search archive with timeline archive

Cons:

- payload size can grow larger than current-page search export

### 2. Extend the current-page search export route with `scope=all`

Pros:

- fewer routes

Cons:

- mixes materially different size/behavior contracts into one route
- risks accidental drift in current-page semantics

### 3. Expand search archive to full detail payloads

Pros:

- richer archive output

Cons:

- overlaps with timeline archive scope
- changes the established search-result payload contract

### 4. Only polish export UX consistency

Pros:

- smaller frontend-only delta

Cons:

- does not advance archive/export capability meaningfully

## Recommended Approach

Use approach 1. Add a dedicated search archive route that reuses the existing search parameters and returns all filtered search-result items as one JSON attachment, leaving the current-page search export path untouched.

## Route Contract

### Path

- `GET /terminals/{group_id}/sessions/history/search/archive`

### Query Parameters

- `q`
- `sort`
- `status`
- `owner_user_id`
- `session_id_prefix`
- `snapshot_from`
- `snapshot_to`

### Semantics

- applies the same auth and workspace-access checks as the existing search/export routes
- applies the same filter and sort semantics as `GET /terminals/{group_id}/sessions/history/search`
- exports all filtered matched sessions, not only the current page
- returns `application/json`
- returns an attachment filename ending with `.json`

### Response Shape

Return a JSON object containing:

- `group_id`
- `query`
- `sort`
- `total`
- `filters`
- `items`
  - each item uses the same payload shape as `TerminalSessionHistorySearchMatchResponse`

Missing workspace/history and invalid input behavior should stay aligned with the current search route:

- same auth checks
- same workspace access checks
- same `404` mapping path
- same `400` mapping for service-level invalid query/time-range validation

## Backend Design

In `app/routes/terminals.py`:

- add a helper for search-archive filenames
- add the new archive route beside the existing search routes
- reuse `_require_accessible_workspace(...)`
- reuse `service.search_history_by_group(...)` with an internal all-results fetch
- return a JSON attachment built from the existing search-result payload shape

No service or persistence change is required if the route reuses `search_history_by_group(...)` with an all-results limit derived from a first pass. If that becomes awkward, add only the smallest helper necessary.

## Frontend Design

In `web/src/api/client.ts`:

- add `downloadTerminalHistorySearchArchive(...)`
- reuse the existing search query builder

In `web/src/pages/Terminals.tsx`:

- add one `Export Search Archive JSON` action in the search panel
- keep the existing current-page search export button intact
- reuse the existing page-level `actionKey` / `actionError` / `actionNotice` state
- reuse the existing blob-download browser flow

## Testing Strategy

Backend coverage:

- archive route returns JSON attachment content and forwards the current search parameters
- missing history still returns `404`
- invalid snapshot range still returns `400`
- OpenAPI exposes the new archive path with search parameters

Frontend verification:

- `npm run build` and `npm run lint` cover the new helper and action wiring

Regression verification:

- focused terminal route/API tests
- `ruff`
- web lint/build
- `git diff --check`

## Risks And Mitigations

- Risk: archive payloads can become much larger than current-page search exports.
  - Mitigation: keep the route scoped to one workspace and one filtered search slice, and label it explicitly as archive/export-all.
- Risk: search archive semantics could drift from the current search route.
  - Mitigation: reuse the same service method and parameter set instead of rebuilding query logic.
- Risk: operators may misread search archive as full transcript export.
  - Mitigation: keep the archive payload in the current search-result match/snippet shape and preserve timeline archive as the full-detail path.

## Rollout

Additive operator-facing API/UI change only. No migration and no compatibility break for existing search current-page export, timeline archive, detail export, or current history contracts.
