# M8.5.18 Terminal Word-Boundary Relevance Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so exact word-boundary hits outrank substring-only hits, without changing the current search API, UI surface, RBAC, pagination model, or history compatibility boundaries.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep the existing match set unchanged:
  - substring matches still remain searchable and returnable
  - word-boundary hits only affect ordering
- add two lightweight ranking signals derived from already available search data:
  - `whole_word_match_count`
  - `first_whole_word_offset`
- preserve the existing `M8.5.17` relevance signals after the new word-boundary signals:
  - `cluster_span`
  - `first_match_offset`
  - `match_density`
  - weak recency tie-break
- keep `newest` and `oldest` semantics unchanged

## Out Of Scope

- no new `sort` values
- no new query parameters or response fields
- no change to the substring search contract
- no regex search mode
- no tokenizer, stemming, or full-text index
- no snippet-generation changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes

## Context

`M8.5.17` already made default `relevance` more text-quality-aware by adding concentration, first-hit position, and density ahead of weak recency. The next rough edge is that substring-only hits such as `terror` can still rank too close to exact `error` matches when the raw match count is similar.

The next small step should therefore stay backend-only and improve only the default `relevance` branch. The result should remain deterministic, explainable, and easy to regression test.

## Approaches Considered

### 1. Minimal exact-word bonus

Add only `whole_word_match_count` ahead of the current `M8.5.17` tuple.

Pros:

- smallest implementation delta
- very easy to test

Cons:

- too weak when exact-word counts tie
- does not distinguish earlier whole-word hits from later ones

### 2. Small boundary-aware ranking tuple

Add `whole_word_match_count` plus `first_whole_word_offset`, then fall back to the existing `M8.5.17` signals.

Pros:

- materially improves exact-word relevance
- stays easy to explain and regression test
- no API, UI, or persistence changes

Cons:

- requires a few more focused service tests than approach 1

### 3. Token-aware scoring layer

Introduce a richer tokenization or scoring model for words, symbols, and lines.

Pros:

- potentially highest long-term quality

Cons:

- scope expansion
- harder to stabilize and explain
- too large for the next additive milestone

## Recommended Approach

Use approach 2: a small boundary-aware ranking tuple for default `relevance`.

This is the smallest change that makes exact word hits clearly outrank substring-only hits while preserving the current search contract. It avoids a heavy tokenization layer and keeps the implementation narrow enough for deterministic service-level TDD.

## Word-Boundary Model

### Boundary Rule

Treat ASCII letters, digits, and underscore (`[A-Za-z0-9_]`) as word characters.

A match counts as a whole-word hit when:

- its left edge is at the start of the string, or the preceding character is not a word character
- and its right edge is at the end of the string, or the following character is not a word character

### Examples

- count as whole-word hits:
  - `error`
  - `error:`
  - `(error)`
  - `error-log`
- do not count as whole-word hits:
  - `terror`
  - `supererrorx`
  - `error_code`

### Match Set Stability

Whole-word detection does not change which snapshots match the query.

Examples:

- searching `error` still returns snapshots containing `terror`
- snapshots with whole-word `error` simply rank ahead of substring-only matches under `sort="relevance"`

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `whole_word_match_count` descending
3. `first_whole_word_offset` ascending
4. `cluster_span` ascending
5. `first_match_offset` ascending
6. `match_density` descending
7. `snapshot_at` descending
8. `session_id` ascending

### Metric Semantics

- `match_count`
  - total number of case-insensitive substring matches in the snapshot output
- `whole_word_match_count`
  - number of those matches whose edges satisfy the lightweight word-boundary rule
- `first_whole_word_offset`
  - earliest offset among whole-word hits
  - when no whole-word hit exists, use a stable sentinel that preserves fallback to the existing `M8.5.17` ordering
- `cluster_span`
  - span from the first substring hit to the last substring hit
- `first_match_offset`
  - earliest substring-hit position in the output
- `match_density`
  - lightweight ratio derived from `match_count` and output length
- `snapshot_at`
  - weak recency tie-break only

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Add a small helper local to `services/terminal_sessions.py` that evaluates whole-word hits from the existing substring offsets and query length. No new DTO is required.

### Route

No route signature changes are needed. The existing `sort` enum and response DTOs remain unchanged.

### Pagination

Search pagination remains:

- build the full ordered match list first
- then apply `offset` / `limit`

This preserves existing search pagination, cross-session navigation, and snippet deep-link behavior.

## Contract Stability

The following must remain unchanged:

- `sort` API contract
- search response shape
- substring matching semantics
- snippet text and deep-link metadata
- frontend search controls
- `newest` / `oldest` ordering semantics
- `latest.json` compatibility
- current RBAC and workspace access behavior

## Testing Strategy

### Service

Add focused service tests that lock:

- whole-word hits outrank substring-only hits when `match_count` is equal
- when whole-word counts tie, earlier `first_whole_word_offset` wins
- when no whole-word hits exist, ordering falls back to the existing `M8.5.17` signals
- pagination still slices the globally ranked `relevance` result set after the new ordering is applied

### Route / Regression

Reuse the current terminal route/API regression suites to prove:

- `sort=relevance|newest|oldest` remains accepted
- search route and OpenAPI contracts remain unchanged
- no search-surface regression is introduced by the backend-only word-boundary refinement

## Completion Signal

`M8.5.18` is complete when:

- exact word-boundary hits clearly outrank substring-only hits in default `relevance`
- substring-only matches still remain searchable and visible
- `newest` and `oldest` remain unchanged
- search pagination, navigation, and snippet deep links continue to work without protocol changes
- existing terminal compatibility and RBAC boundaries remain unchanged
