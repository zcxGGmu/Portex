# M8.5.17 Terminal Relevance Ranking Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so the default search mode prioritizes textual match quality more clearly than recency, without changing the existing search API, UI surface, RBAC, or history compatibility boundaries.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep `newest` and `oldest` semantics unchanged
- compute the improved relevance ordering only from data already available during search:
  - match count
  - match concentration
  - first match position
  - lightweight match density
  - recency only as a weak tie-break
- preserve existing search pagination, cross-session navigation, and snippet deep-link behavior

## Out Of Scope

- no new `sort` values
- no new query parameters or response fields
- no snippet-generation changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no full-text index, tokenization layer, or persistent search metadata
- no changes to RBAC or workspace-access checks

## Context

`main` already includes explicit `relevance` / `newest` / `oldest` search controls through `M8.5.16`. The remaining rough edge is that default `relevance` is still mostly `match_count`, then recency. That makes the default mode too close to `newest`, even though operators now have explicit time-based sort modes when they want them.

The next small step should therefore improve only the default `relevance` behavior. The change should be narrow, explainable, and easy to regression test.

## Approaches Considered

### 1. Minimal tie-break tweak

Keep `match_count` first and only replace the recency tie-break with `first_match_offset`.

Pros:

- smallest implementation delta
- very low regression risk

Cons:

- too weak to distinguish concentrated matches from sparse matches
- likely not enough visible improvement to justify a milestone

### 2. Small heuristic ranking tuple

Use a deterministic backend ranking tuple that still starts from `match_count`, but adds concentration, first-hit position, and density before weak recency tie-breaks.

Pros:

- noticeably better default relevance
- still explainable and testable
- no API, UI, or persistence changes

Cons:

- requires a few more focused service tests

### 3. Full scoring layer

Introduce a richer search-scoring model with line-aware weighting, snippet quality, or token-boundary heuristics.

Pros:

- potentially highest quality ordering

Cons:

- scope expansion
- harder to explain and stabilize
- too large for the next additive milestone

## Recommended Approach

Use approach 2: a small heuristic ranking tuple for default `relevance`.

This is the smallest change that makes `relevance` materially different from `newest` while staying fully inside the current search boundary. It avoids a black-box score and keeps the implementation readable enough that future regressions can be caught with narrow deterministic tests.

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `cluster_span` ascending
3. `first_match_offset` ascending
4. `match_density` descending
5. `snapshot_at` descending
6. `session_id` ascending

### Metric Semantics

- `match_count`
  - total number of case-insensitive substring matches in the snapshot output
- `cluster_span`
  - the span from the first match offset to the last match offset
  - smaller means the matches are more concentrated
- `first_match_offset`
  - the earliest match position in the output
  - smaller means the search term appears earlier in the transcript
- `match_density`
  - a lightweight ratio derived from `match_count` and output length
  - only used after the stronger structural signals above
- `snapshot_at`
  - weak recency tie-break only

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` sorting branch changes.

Add a small helper that derives ranking metadata from the existing `offsets` list and snapshot output length. This helper should stay local to `services/terminal_sessions.py`; no new DTO is required.

### Route

No route signature changes are needed. The existing `sort` enum and response DTOs remain unchanged.

### Pagination

Search pagination remains:

- build the full ordered match list first
- then apply `offset` / `limit`

This keeps existing search result pagination, cross-session next/previous navigation, and snippet deep links aligned with one global ordering.

## Contract Stability

The following must remain unchanged:

- `sort` API contract
- search response shape
- snippet text and deep-link metadata
- frontend search controls
- `newest` / `oldest` ordering semantics
- `latest.json` compatibility
- current RBAC and workspace access behavior

## Testing Strategy

### Service

Add focused service tests that lock:

- concentrated matches outrank sparse matches when `match_count` is equal
- earlier first match outranks later first match when stronger signals are tied
- weak recency only decides near-ties, not clearly better textual matches
- pagination still slices the globally ranked `relevance` result set

### Route / Regression

Reuse the current terminal route/API regression suites to prove:

- `sort=relevance|newest|oldest` remains accepted
- search route and OpenAPI contracts remain unchanged
- no search-surface regression is introduced by the backend-only ranking refinement

## Completion Signal

`M8.5.17` is complete when:

- default `relevance` ordering clearly differs from `newest`
- stronger textual matches outrank merely newer matches in `relevance`
- `newest` and `oldest` remain unchanged
- search pagination, navigation, and snippet deep links continue to work without protocol changes
- existing terminal compatibility and RBAC boundaries remain unchanged
