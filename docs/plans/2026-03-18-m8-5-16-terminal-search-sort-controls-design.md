# M8.5.16 Terminal Search Sort Controls Design

## Goal

Add explicit search-result sort controls to `/terminals` so operators can switch terminal history search ordering without changing existing RBAC, history persistence, or non-search terminal APIs.

## Scope

- add a search-only `sort` contract to `GET /terminals/{group_id}/sessions/history/search`
- support the fixed sort set:
  - `relevance`
  - `newest`
  - `oldest`
- keep `relevance` as the default so existing callers remain compatible
- add a sort selector to the `/terminals` search form
- keep search pagination, cross-session navigation, and snippet deep links aligned with the selected sort order

## Out Of Scope

- no changes to timeline sorting
- no changes to `latest.json` or archived snapshot persistence
- no changes to `GET /terminals/{group_id}/sessions/current/history`
- no relevance-score algorithm beyond the current `match_count`-driven behavior
- no URL query persistence or per-user sort preference persistence
- no changes to RBAC or workspace-access checks

## Context

`main` already includes terminal-history search pagination, snippet deep links, metadata filters, inclusive time-range filtering, and preset time ranges through `M8.5.15`. The remaining rough edge is that search results always use one fixed backend order: highest `match_count`, then newest `snapshot_at`. That works as a default, but operators cannot intentionally pivot between “most relevant” and “most recent/oldest” views while keeping pagination and cross-session navigation consistent.

## Approaches Considered

### 1. Backend `sort` parameter plus frontend selector

Add a narrow `sort` query parameter to the existing search route and expose it via a frontend select in `/terminals`.

Pros:

- keeps pagination and cross-session navigation globally consistent
- preserves one source of truth for ordering
- minimal additive API change

Cons:

- touches backend route/service, API client, hooks, frontend state, and tests

### 2. Frontend-only reordering of the current page

Leave the backend contract unchanged and sort only the currently fetched search page in React state.

Pros:

- smallest code delta

Cons:

- pagination becomes misleading because each page is locally reordered, not globally sorted
- cross-session next/previous navigation stops matching the displayed ordering

### 3. Replace the default backend order without user control

Change the current backend default and document it, but do not add a UI control.

Pros:

- smallest end-user surface

Cons:

- removes intentional operator control
- silently changes semantics for existing users
- does not satisfy the approved “explicit sort switching” goal

## Recommended Approach

Use approach 1: add a backend `sort` parameter with a frontend selector.

This is the smallest approach that keeps ordering truthful across the full search result set. Pagination, previous/next match navigation, snippet deep links, and detail-opening behavior all continue to operate on the same globally sorted dataset rather than a locally reshuffled page.

## Sort Model

### Allowed Sort Values

- `relevance`
- `newest`
- `oldest`

### Semantics

- `relevance`:
  - sort by `match_count` descending
  - tie-break by `snapshot_at` descending
  - final tie-break by `session_id` ascending
- `newest`:
  - sort by `snapshot_at` descending
  - tie-break by `match_count` descending
  - final tie-break by `session_id` ascending
- `oldest`:
  - sort by `snapshot_at` ascending
  - tie-break by `match_count` descending
  - final tie-break by `session_id` ascending

### Compatibility

When `sort` is omitted, backend behavior remains `relevance`. Existing clients therefore keep the current ordering without any request changes.

## Backend Design

### Service

Extend `TerminalSessionService.search_history_by_group(...)` with an optional `sort` parameter. The existing query normalization, snapshot filtering, substring matching, snippet generation, and pagination behavior stay unchanged.

Refactor the current fixed ordering in `_search_history_snapshots(...)` into a small helper that sorts the already-built match list according to the selected mode. This keeps matching logic and ordering logic separate.

### Route

Extend `GET /terminals/{group_id}/sessions/history/search` with a narrow enum query parameter named `sort`.

Route behavior remains otherwise unchanged:

- same RBAC checks
- same workspace access checks
- same `404` for inaccessible or empty filtered history sets
- same `400`/`422` semantics for existing invalid input categories

### Schema

The response DTO does not need a new field. Sorting is a request concern, not a response payload concern.

## Frontend Design

### Search Controls

Add a small sort selector next to the existing search form controls in `web/src/pages/Terminals.tsx`.

Labels:

- `Relevance`
- `Newest`
- `Oldest`

The control is only part of the search path. Timeline filters remain unchanged.

### State Behavior

Maintain a dedicated local search sort state with default `relevance`.

When sort changes:

- preserve the current search input text
- preserve timeline filters
- reset `searchOffset`
- clear `pendingSearchPageMove`
- clear `detailSessionId`
- clear `pendingMatchTarget`

This matches the existing behavior used when the active search dataset changes in a way that would invalidate current pagination/detail anchors.

### Clear Behavior

The current `Clear` button should continue to reset search-specific state. It should also restore sort to `relevance`, because sort is part of the search dataset rather than the shared timeline filter model.

## Error Handling

- invalid `sort` values should be rejected by route-level enum validation
- service code should still guard against unknown values if called directly from non-route paths
- no new custom error envelope is introduced
- existing invalid-range and empty-query behavior remains unchanged

## Testing Strategy

### Backend

- add service tests covering `relevance`, `newest`, and `oldest` result ordering
- verify search pagination continues to slice the fully sorted result set
- add route tests covering:
  - default `relevance` behavior when `sort` is omitted
  - explicit `sort` pass-through
  - invalid `sort` rejection
- add OpenAPI coverage for the additive `sort` query parameter

### Frontend

- extend the search request path so `sort` participates in the query key and request params
- verify the page still builds and lints cleanly after adding the selector

## Completion Signal

`M8.5.16` is complete when:

- `/terminals` exposes explicit search sort controls for `Relevance`, `Newest`, and `Oldest`
- backend search honors the selected sort order with `relevance` as the default
- search pagination, previous/next navigation, and snippet deep links remain aligned with the selected sort
- existing terminal compatibility and RBAC boundaries remain unchanged
