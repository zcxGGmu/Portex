# M8.5.20 Terminal Line-Start Quality Relevance Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so results with cleaner line-start whole-word hits outrank results that mix the same line-start signal with more inline whole-word noise, without changing the current search API, UI surface, RBAC, pagination model, or history compatibility boundaries.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep the existing match set unchanged:
  - substring matches still remain searchable and returnable
  - whole-word detection still remains ordering-only
  - line-start detection still remains ordering-only
  - the new signal only improves ordering among already matched snapshots
- add one lightweight ranking signal derived from already available search data:
  - `non_line_start_whole_word_match_count`
- preserve the existing `M8.5.19` relevance signals after the new line-start-quality signal:
  - `whole_word_match_count`
  - `line_start_whole_word_match_count`
  - `first_line_start_whole_word_offset`
  - `first_whole_word_offset`
  - `cluster_span`
  - `first_match_offset`
  - `match_density`
  - weak recency tie-break
- keep `newest` and `oldest` semantics unchanged

## Out Of Scope

- no new `sort` values
- no new query parameters or response fields
- no change to the substring search contract
- no log-marker tokenizer or syntax-specific parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes

## Context

`M8.5.18` made default `relevance` whole-word-aware, and `M8.5.19` added line-start whole-word priority on top of that. The next remaining rough edge is that two results can now have similar line-start signal, but one of them still contains much more inline whole-word noise.

For operators scanning terminal history, a result where most whole-word hits occur at line starts usually feels more relevant than one where line-start hits exist but many other whole-word hits are buried inline. The next step should therefore stay backend-only and improve only the default `relevance` branch with one more deterministic, explainable integer signal.

## Approaches Considered

### 1. Minimal inline-noise tie-break

Add only `non_line_start_whole_word_match_count` after the current `M8.5.19` tuple.

Pros:

- smallest implementation delta
- easy to test

Cons:

- too weak when placed late in the tuple
- limited visible improvement for a standalone milestone

### 2. Small line-start-quality tuple

Add `non_line_start_whole_word_match_count` immediately after `line_start_whole_word_match_count`, then fall back to the existing `M8.5.19` signals.

Pros:

- materially improves log-style result quality
- stays deterministic and easy to regression test
- avoids float ratios and black-box scoring

Cons:

- requires a few more focused service tests than approach 1

### 3. Ratio or weighted score model

Introduce a ratio such as `line_start_whole_word_match_count / whole_word_match_count` or a composite weighted score.

Pros:

- more expressive ranking model

Cons:

- harder to explain and stabilize
- introduces unnecessary scoring complexity for this milestone

## Recommended Approach

Use approach 2: a small line-start-quality tuple for default `relevance`.

This is the smallest change that makes line-start-heavy results rank more intuitively while preserving the current search contract. It keeps the implementation narrow, deterministic, and easy to defend in tests.

## Line-Start Quality Model

### Signal Definition

Define:

- `non_line_start_whole_word_match_count = whole_word_match_count - line_start_whole_word_match_count`

This counts whole-word hits that are not line-start hits.

The signal is intentionally integer-only. It avoids float ratios while still preferring results where whole-word relevance is concentrated at line starts.

### Examples

- preferred:
  - `error: first\nerror: second\n`
  - whole-word hits: 2
  - line-start whole-word hits: 2
  - non-line-start whole-word hits: 0
- less preferred:
  - `prefix error text\nerror: second\nanother error\n`
  - whole-word hits: 3
  - line-start whole-word hits: 1
  - non-line-start whole-word hits: 2

### Match Set Stability

The new signal does not change which snapshots match the query.

Examples:

- searching `error` still returns both line-start-heavy and inline-heavy snapshots
- under `sort="relevance"`, snapshots with the same line-start strength but fewer inline whole-word mentions simply rank ahead of noisier ones

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `line_start_whole_word_match_count` descending
3. `non_line_start_whole_word_match_count` ascending
4. `whole_word_match_count` descending
5. `first_line_start_whole_word_offset` ascending
6. `first_whole_word_offset` ascending
7. `cluster_span` ascending
8. `first_match_offset` ascending
9. `match_density` descending
10. `snapshot_at` descending
11. `session_id` ascending

### Metric Semantics

- `match_count`
  - total number of case-insensitive substring matches in the snapshot output
- `line_start_whole_word_match_count`
  - number of whole-word hits whose left edge is also at the start of the transcript or immediately after `\n`
- `non_line_start_whole_word_match_count`
  - number of whole-word hits that are not line-start hits
  - smaller means less inline whole-word noise for the same broad line-start signal
- `whole_word_match_count`
  - number of those matches whose edges satisfy the lightweight word-boundary rule
  - still acts as a later strength signal, but no longer blocks the new noise signal from affecting the order
- `first_line_start_whole_word_offset`
  - earliest offset among line-start whole-word hits
- `first_whole_word_offset`
  - earliest offset among all whole-word hits
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

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the one new integer field. Reuse the already-computed `whole_word_match_count` and `line_start_whole_word_match_count`; no new search pass, DTO, or route change is needed.

Keep `match_count` first, but move `whole_word_match_count` after the new noise signal. If `whole_word_match_count` stayed ahead of `line_start_whole_word_match_count` plus `non_line_start_whole_word_match_count`, the new signal would be dominated and would not actually change ordering.

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

- when `match_count` and `line_start_whole_word_match_count` are tied, results with fewer non-line-start whole-word hits win
- when the new noise signal is tied, ordering still falls back to `first_line_start_whole_word_offset`
- when no line-start whole-word hits exist, ordering falls back to the existing `M8.5.19` signals
- pagination still slices the globally ranked `relevance` result set after the new ordering is applied

### Route / Regression

Reuse the current terminal route/API regression suites to prove:

- `sort=relevance|newest|oldest` remains accepted
- search route and OpenAPI contracts remain unchanged
- no search-surface regression is introduced by the backend-only line-start-quality refinement

## Completion Signal

`M8.5.20` is complete when:

- line-start-heavy exact whole-word results clearly outrank noisier inline-heavy whole-word results in default `relevance`
- existing line-start, whole-word, and fallback behavior remain intact
- `newest` and `oldest` remain unchanged
- search pagination, navigation, and snippet deep links continue to work without protocol changes
- existing terminal compatibility and RBAC boundaries remain unchanged
