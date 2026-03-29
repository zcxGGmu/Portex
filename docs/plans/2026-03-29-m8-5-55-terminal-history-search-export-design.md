# M8.5.55 Terminal History Search Export Design

## Goal

Add a bounded downloadable JSON export for the current terminal-history search result page so operators can preserve one filtered search slice outside the browser without changing existing search, timeline, detail, relevance, or RBAC behavior.

## Scope

- add `GET /terminals/{group_id}/sessions/history/search/export`
- reuse the existing search query parameters:
  - `q`
  - `limit`
  - `offset`
  - `sort`
  - `status`
  - `owner_user_id`
  - `session_id_prefix`
  - `snapshot_from`
  - `snapshot_to`
- keep export size bounded by the same search page contract already used on the search route
- return an `application/json` attachment containing:
  - the current search/filter/pagination metadata
  - the current search result page items in the existing snippet/match shape
- add one current-page JSON export action to the `/terminals` search panel

## Out Of Scope

- no workspace-wide archive export
- no search-history persistence
- no timeline export changes in this session
- no full snapshot detail expansion inside search export
- no changes to search ranking, relevance, or snippet construction
- no changes to `latest.json`, `/sessions/current/history`, or RBAC

## Context

`M8.5.54` already added bounded multi-snapshot full-detail export for the current timeline page. The remaining adjacent operator-surface gap is the search view: operators can query terminal history, inspect snippets, and paginate across matched sessions, but they still cannot export the current search result page without repeating the query through the API or copying snippets manually.

The next additive step should therefore stay page-bounded and mirror the current search surface:

- preserve the existing search query and filter semantics
- preserve the existing `relevance` / `newest` / `oldest` sort behavior
- export the same match/snippet payload the UI is already showing

This is smaller than workspace-wide archive export and stays aligned with the current operator-surface path.

## Approaches Considered

### 1. Add a bounded search-result JSON export route for the current page (recommended)

Pros:

- smallest additive search-surface export
- reuses the existing search service method directly
- preserves the exact snippet/match structure operators already inspect
- stays bounded by the current `limit` / `offset` contract

Cons:

- exports search results rather than full detail payloads

### 2. Export full detail payloads for each matched search result

Pros:

- richer archive output

Cons:

- larger payloads and more complex semantics
- starts overlapping with `M8.5.54` timeline bulk export
- may require additional service aggregation work

### 3. Add workspace-wide search export

Pros:

- stronger archive story

Cons:

- larger scope
- unclear output-size boundary
- likely needs streaming or background job semantics

### 4. Build search export client-side from existing query data only

Pros:

- no backend route change

Cons:

- browser-only behavior
- no server-owned attachment contract
- duplicates serialization rules in the frontend

## Recommended Approach

Use approach 1. Add a dedicated export route that mirrors the existing search parameters and returns one bounded page of `TerminalSessionHistorySearchResponse`-shaped data as a JSON attachment, then expose it through one extra action in the search panel.

## Route Contract

### Path

- `GET /terminals/{group_id}/sessions/history/search/export`

### Query Parameters

- `q`
- `limit`
- `offset`
- `sort`
- `status`
- `owner_user_id`
- `session_id_prefix`
- `snapshot_from`
- `snapshot_to`

### Semantics

- applies the same auth and workspace-access checks as the existing search route
- applies the same filter, sort, and pagination semantics as `GET /terminals/{group_id}/sessions/history/search`
- keeps export size bounded by the selected page size
- returns `application/json`
- returns an attachment filename ending with `.json`

### Response Shape

Return a JSON object containing:

- `group_id`
- `query`
- `limit`
- `offset`
- `total`
- `has_more`
- `sort`
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

- add a helper for search-export filenames
- add the new export route beside the existing search route
- reuse `_require_accessible_workspace(...)`
- reuse `service.search_history_by_group(...)`
- return a JSON attachment built from the existing `TerminalSessionHistorySearchResponse` shape

No service or persistence change is required.

## Frontend Design

In `web/src/api/client.ts`:

- add `downloadTerminalHistorySearch(...)`
- add one small shared query-param builder for search fetch and export

In `web/src/pages/Terminals.tsx`:

- add one export action in the search panel
- scope it to the current search page
- reuse the existing page-level `actionKey` / `actionError` / `actionNotice` state
- reuse the existing blob-download browser flow

## Testing Strategy

Backend coverage:

- export returns JSON attachment content and forwards the current search parameters
- missing history still returns `404`
- invalid snapshot range still returns `400`
- OpenAPI exposes the new export path with search parameters

Frontend verification:

- `npm run build` and `npm run lint` cover the new helper and action wiring

Regression verification:

- focused terminal route/API tests
- `ruff`
- web lint/build
- `git diff --check`

## Risks And Mitigations

- Risk: search export semantics could drift from the current search route.
  - Mitigation: call the same service method with the same parameter set and serialize the same payload shape.
- Risk: operators may misread search export as full transcript export.
  - Mitigation: keep the action label explicit about exporting the current search page JSON, not raw transcript bundles.
- Risk: route ordering could conflict with the existing `/history/search` path.
  - Mitigation: use a static `/history/search/export` path.

## Rollout

Additive operator-facing API/UI change only. No migration and no compatibility break for existing terminal search/detail/timeline contracts.
