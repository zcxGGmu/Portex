# M8.5.19 Terminal Line-Boundary Relevance Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so line-start whole-word hits outrank later-in-line whole-word hits when the broader match quality is otherwise similar, without changing the current search API, UI surface, RBAC, pagination model, or history compatibility boundaries.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep the existing match set unchanged:
  - substring matches still remain searchable and returnable
  - whole-word detection still remains ordering-only
  - line-boundary detection only adds ordering signals on top of the current whole-word model
- add two lightweight ranking signals derived from already available search data:
  - `line_start_whole_word_match_count`
  - `first_line_start_whole_word_offset`
- preserve the existing `M8.5.18` relevance signals after the new line-boundary signals:
  - `whole_word_match_count`
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
- no change to snippet generation or deep-link metadata
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer, full-text index, or per-line scoring engine

## Context

`M8.5.17` made default `relevance` more text-quality-aware, and `M8.5.18` added whole-word awareness on top of that. The next remaining rough edge is visible in terminal transcripts where the same search term can appear both as a line-leading log marker and as a later-in-line mention.

For operators scanning terminal history, a line-start exact hit is often a stronger signal than the same exact word appearing later inside a longer sentence. The next step should therefore stay backend-only and only refine the default `relevance` branch with one more deterministic, explainable signal family.

## Approaches Considered

### 1. Minimal line-start tie-break

Add only `first_line_start_whole_word_offset` after the current `M8.5.18` tuple.

Pros:

- smallest implementation delta
- very easy to test

Cons:

- too weak when line-start exact-hit counts differ
- limited visible improvement for a standalone milestone

### 2. Small line-boundary-aware ranking tuple

Add `line_start_whole_word_match_count` plus `first_line_start_whole_word_offset`, then fall back to the existing `M8.5.18` signals.

Pros:

- materially improves log-style transcript relevance
- stays easy to explain and regression test
- no API, UI, or persistence changes

Cons:

- requires a few more focused service tests than approach 1

### 3. Per-line scoring model

Split outputs into lines and compute richer line-level ranking scores.

Pros:

- potentially best long-term quality

Cons:

- scope expansion
- harder to stabilize and explain
- too large for the next additive milestone

## Recommended Approach

Use approach 2: a small line-boundary-aware ranking tuple for default `relevance`.

This is the smallest change that makes terminal-log-style line-leading exact hits rank more intuitively while preserving the current search contract. It keeps the implementation narrow, deterministic, and regression-friendly.

## Line-Boundary Model

### Boundary Rule

A match counts as a line-start whole-word hit when:

- it already satisfies the current `M8.5.18` whole-word rule
- and its start offset is `0`, or the preceding character is `\n`

This definition deliberately builds on whole-word detection. It avoids promoting substring-only noise such as `terror` just because it appears at the beginning of a line.

### Examples

- count as line-start whole-word hits:
  - `error\n`
  - `error: failed to attach`
  - `...\nerror: failed to attach`
- do not count as line-start whole-word hits:
  - `prefix error`
  - `...\nprefix error`
  - `terror at line start`

### Match Set Stability

Line-boundary detection does not change which snapshots match the query.

Examples:

- searching `error` still returns snapshots containing `terror`
- snapshots with line-start whole-word `error` simply rank ahead of later-in-line whole-word matches under `sort="relevance"`

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `whole_word_match_count` descending
3. `line_start_whole_word_match_count` descending
4. `first_line_start_whole_word_offset` ascending
5. `first_whole_word_offset` ascending
6. `cluster_span` ascending
7. `first_match_offset` ascending
8. `match_density` descending
9. `snapshot_at` descending
10. `session_id` ascending

### Metric Semantics

- `match_count`
  - total number of case-insensitive substring matches in the snapshot output
- `whole_word_match_count`
  - number of those matches whose edges satisfy the current lightweight word-boundary rule
- `line_start_whole_word_match_count`
  - number of whole-word hits whose left edge is also at the start of the transcript or immediately after `\n`
- `first_line_start_whole_word_offset`
  - earliest offset among line-start whole-word hits
  - when no such hit exists, use a stable sentinel that preserves fallback to the existing `M8.5.18` ordering
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

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the two new line-boundary signals. Add a small local helper that evaluates line-start whole-word hits from the existing substring offsets and query length. No new DTO is required.

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

- line-start whole-word hits outrank later-in-line whole-word hits when stronger signals are otherwise tied
- when line-start whole-word counts tie, earlier `first_line_start_whole_word_offset` wins
- when no line-start whole-word hits exist, ordering falls back to the existing `M8.5.18` signals
- pagination still slices the globally ranked `relevance` result set after the new ordering is applied

### Route / Regression

Reuse the current terminal route/API regression suites to prove:

- `sort=relevance|newest|oldest` remains accepted
- search route and OpenAPI contracts remain unchanged
- no search-surface regression is introduced by the backend-only line-boundary refinement

## Completion Signal

`M8.5.19` is complete when:

- line-start exact whole-word hits clearly outrank later-in-line whole-word hits in default `relevance`
- substring-only and later-in-line whole-word matches still remain searchable and visible
- `newest` and `oldest` remain unchanged
- search pagination, navigation, and snippet deep links continue to work without protocol changes
- existing terminal compatibility and RBAC boundaries remain unchanged
