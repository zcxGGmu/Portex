# M8.5.21 Terminal Log-Marker Relevance Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so line-start log-marker hits outrank plain line-start whole-word hits, without changing the current search API, UI surface, RBAC, pagination model, or history compatibility boundaries.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep the existing match set unchanged:
  - substring matches still remain searchable and returnable
  - whole-word detection still remains ordering-only
  - line-start detection still remains ordering-only
  - the new marker signal only improves ordering among already matched snapshots
- add two lightweight ranking signals derived from already available search data:
  - `line_start_log_marker_match_count`
  - `first_line_start_log_marker_offset`
- preserve the existing `M8.5.20` relevance signals after the new marker signals:
  - `line_start_whole_word_match_count`
  - `conditional_non_line_start_whole_word_match_count`
  - `whole_word_match_count`
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
- no generic punctuation-aware ranking
- no `[query]` log-marker handling in this milestone
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes

## Context

`M8.5.19` made line-start whole-word hits outrank later-in-line hits, and `M8.5.20` made cleaner line-start results outrank noisier ones. The next remaining rough edge is that not all line-start hits are equally meaningful: log-style prefixes such as `error:` and `ERROR -` usually carry stronger operator signal than a plain line-start `error` sentence.

The next step should therefore stay backend-only and improve only the default `relevance` branch with one more narrow, deterministic signal family. To keep the milestone small and stable, the first version should only recognize the most conservative log-marker shapes.

## Approaches Considered

### 1. Minimal marker bonus

Add only a boolean-like marker bonus ahead of the current `M8.5.20` tuple.

Pros:

- smallest implementation delta
- easy to test

Cons:

- too weak when marker counts tie
- limited value for a standalone milestone

### 2. Small marker-aware ranking tuple

Add `line_start_log_marker_match_count` plus `first_line_start_log_marker_offset`, then fall back to the existing `M8.5.20` signals.

Pros:

- materially improves terminal-log relevance
- stays deterministic and easy to regression test
- no API, UI, or persistence changes

Cons:

- requires a few more focused service tests than approach 1

### 3. Generic punctuation-aware model

Promote any query occurrence near punctuation at the beginning of a line.

Pros:

- more general

Cons:

- much blurrier semantics
- likely to over-promote ordinary prose
- too wide for the next additive milestone

## Recommended Approach

Use approach 2: a small marker-aware ranking tuple for default `relevance`.

This is the smallest change that makes log-style line-start markers rank more intuitively while preserving the current search contract. It keeps the implementation narrow enough to be explainable and regression-friendly.

## Log-Marker Model

### Marker Rule

A match counts as a line-start log-marker hit when:

- it already satisfies the current line-start whole-word rule
- and the text immediately after the query is either:
  - `:`
  - ` -`

The search match itself remains case-insensitive because the existing search offsets are already case-insensitive. Marker punctuation matching remains exact.

### Examples

- count as line-start log-marker hits:
  - `error: failed to attach`
  - `ERROR - failed to attach`
  - `error -`
- do not count as line-start log-marker hits:
  - `prefix error: failed`
  - `[error] failed`
  - `error- failed`
  - `error  - failed`

### Match Set Stability

The marker rule does not change which snapshots match the query.

Examples:

- searching `error` still returns both marker-style and plain-text snapshots
- under `sort="relevance"`, line-start `error:` and `ERROR -` results simply rank ahead of plain line-start `error` results

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `line_start_log_marker_match_count` descending
3. `line_start_whole_word_match_count` descending
4. `conditional_non_line_start_whole_word_match_count` ascending
5. `whole_word_match_count` descending
6. `first_line_start_log_marker_offset` ascending
7. `first_line_start_whole_word_offset` ascending
8. `first_whole_word_offset` ascending
9. `cluster_span` ascending
10. `first_match_offset` ascending
11. `match_density` descending
12. `snapshot_at` descending
13. `session_id` ascending

### Metric Semantics

- `match_count`
  - total number of case-insensitive substring matches in the snapshot output
- `line_start_log_marker_match_count`
  - number of line-start whole-word hits immediately followed by `:` or strict ` -`
- `line_start_whole_word_match_count`
  - number of whole-word hits whose left edge is also at the start of the transcript or immediately after `\n`
- `conditional_non_line_start_whole_word_match_count`
  - when line-start whole-word hits exist, this is the number of whole-word hits that are not line-start hits
  - when no line-start whole-word hits exist, this remains a neutral sentinel and preserves the existing `M8.5.20` fallback
- `whole_word_match_count`
  - number of case-insensitive substring hits that satisfy the lightweight word-boundary rule
- `first_line_start_log_marker_offset`
  - earliest offset among line-start log-marker hits
  - when no such hit exists, use a stable sentinel so ordering falls back cleanly
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

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the two new marker fields. Reuse the already-computed match offsets and current line-start whole-word helper; no new DTO, route field, or extra search pass is needed.

Use a stable sentinel for `first_line_start_log_marker_offset` when no marker hit exists, so the order naturally falls back to the existing `M8.5.20` chain.

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

- line-start `query:` / `query -` marker results outrank plain line-start whole-word results when the broader strength is otherwise similar
- when marker counts tie, earlier `first_line_start_log_marker_offset` wins
- when no marker hits exist, ordering falls back to the existing `M8.5.20` signals
- pagination still slices the globally ranked `relevance` result set after the new ordering is applied

### Route / Regression

Reuse the current terminal route/API regression suites to prove:

- `sort=relevance|newest|oldest` remains accepted
- search route and OpenAPI contracts remain unchanged
- no search-surface regression is introduced by the backend-only marker refinement

## Completion Signal

`M8.5.21` is complete when:

- line-start `query:` and strict `query -` results clearly outrank plain line-start whole-word results in default `relevance`
- no-marker paths continue to fall back to `M8.5.20`
- `newest` and `oldest` remain unchanged
- search pagination, navigation, and snippet deep links continue to work without protocol changes
- existing terminal compatibility and RBAC boundaries remain unchanged
