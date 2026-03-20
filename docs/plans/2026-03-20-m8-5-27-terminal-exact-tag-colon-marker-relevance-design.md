# M8.5.27 Terminal Exact-Tag Colon-Marker Relevance Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so exact-tag colon-marker hits such as `[query]: text` outrank exact-tag dash-marker hits such as `[query] - text`, while preserving the existing priority of raw line-start markers over wrapper families. Keep the current search API, UI surface, RBAC, pagination model, and history compatibility boundaries unchanged.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep the existing match set unchanged:
  - substring matches still remain searchable and returnable
  - whole-word detection still remains ordering-only
  - line-start detection still remains ordering-only
  - raw log-marker detection still remains ordering-only
  - exact-tag wrapper detection still remains ordering-only
  - the new colon-marker signal only improves ordering among already matched snapshots
- add two lightweight ranking signals derived from already available search data:
  - `line_start_exact_tag_colon_marker_match_count`
  - `first_line_start_exact_tag_colon_marker_offset`
- preserve the existing `M8.5.26` relevance signals after the new colon-marker signals:
  - `line_start_log_marker_match_count`
  - `line_start_delimited_log_marker_match_count`
  - `line_start_exact_tag_marker_match_count`
  - `line_start_exact_tag_match_count`
  - `line_start_square_bracket_exact_tag_match_count`
  - `line_start_punctuation_wrap_match_count`
  - `line_start_whole_word_match_count`
  - `conditional_non_line_start_whole_word_match_count`
  - `whole_word_match_count`
  - `first_line_start_log_marker_offset`
  - `first_line_start_delimited_log_marker_offset`
  - `first_line_start_exact_tag_marker_offset`
  - `first_line_start_exact_tag_offset`
  - `first_line_start_square_bracket_exact_tag_offset`
  - `first_line_start_punctuation_wrap_offset`
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
- no generic exact-tag marker weighting model
- no raw marker refinement in this milestone
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes
- no general punctuation weighting beyond `:` versus strict ` -` inside exact-tag markers

## Context

`M8.5.25` established that exact-tag marker forms such as `[query]: text` and `[query] - text` outrank plain exact-tag forms such as `[query] text`. `M8.5.26` then refined exact-tag wrappers so square-bracket forms outrank other wrapper pairs.

The next remaining rough edge is now inside the exact-tag marker family itself. Today `[error]: failed` and `[error] - failed` are effectively peers once stronger signals tie. In operator-facing logs, the colon form is the most common explicit label separator and is usually more meaningful than the dash form.

The next step should stay backend-only and add one more deterministic signal family rather than widening the overall search contract.

## Approaches Considered

### 1. Narrow colon-only marker tie-break

Add a signal that rewards only exact-tag colon markers over exact-tag dash markers.

Pros:

- smallest implementation delta
- directly matches the most common exact-tag marker shape
- easy to regression test

Cons:

- explicitly introduces a colon-over-dash preference

### 2. General marker punctuation hierarchy

Add a broader ordering across multiple exact-tag punctuation forms.

Pros:

- more expressive

Cons:

- too wide for the next additive milestone
- more likely to need follow-up tuning

### 3. Exact-tag punctuation parser

Parse structured exact-tag markers and reason about them more holistically.

Pros:

- most expressive

Cons:

- too large for this incremental backend-only step
- unnecessary complexity for the current cadence

## Recommended Approach

Use approach 1: a narrow exact-tag colon-marker tie-break.

This is the smallest change that closes the remaining gap inside the exact-tag marker family while keeping the rule explainable and regression-friendly. It also avoids pulling in broader punctuation heuristics.

## Exact-Tag Colon-Marker Model

### Colon-Marker Rule

A match counts as an exact-tag colon-marker hit when:

- it already satisfies the current line-start exact-tag marker rule
- the text immediately after the closing wrapper begins with `:`
- the character after `:` is end-of-output or whitespace

The search match itself remains case-insensitive because the existing search offsets are already case-insensitive. Delimiter matching remains exact.

### Examples

- count as exact-tag colon-marker hits:
  - `[error]: failed to attach`
  - `[error]:\nfailed to attach`
- do not count as exact-tag colon-marker hits:
  - `[error] - failed to attach`
  - `[error]:failed to attach`
  - `prefix [error]: failed`

### Relative Strength

The new colon-marker signal is additive inside the existing exact-tag marker family. It does not change the broader raw-marker-versus-wrapper hierarchy.

Examples under `sort="relevance"`:

- `error: failed` still outranks `[error]: failed`
- `[error]: failed` outranks `[error] - failed`
- `[error] - failed` still outranks `[error] failed` because `M8.5.25` exact-tag marker priority remains in place

### Match Set Stability

The new rule does not change which snapshots match the query.

Examples:

- searching `error` still returns `[error]: failed`, `[error] - failed`, and `[error] failed`
- under `sort="relevance"`, colon-marker results simply rank ahead of dash-marker results when broader strength is otherwise similar

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `line_start_log_marker_match_count` descending
3. `line_start_delimited_log_marker_match_count` descending
4. `line_start_exact_tag_marker_match_count` descending
5. `line_start_exact_tag_colon_marker_match_count` descending
6. `line_start_exact_tag_match_count` descending
7. `line_start_square_bracket_exact_tag_match_count` descending
8. `line_start_punctuation_wrap_match_count` descending
9. `line_start_whole_word_match_count` descending
10. `conditional_non_line_start_whole_word_match_count` ascending
11. `whole_word_match_count` descending
12. `first_line_start_log_marker_offset` ascending
13. `first_line_start_delimited_log_marker_offset` ascending
14. `first_line_start_exact_tag_colon_marker_offset` ascending
15. `first_line_start_exact_tag_marker_offset` ascending
16. `first_line_start_exact_tag_offset` ascending
17. `first_line_start_square_bracket_exact_tag_offset` ascending
18. `first_line_start_punctuation_wrap_offset` ascending
19. `first_line_start_whole_word_offset` ascending
20. `first_whole_word_offset` ascending
21. `cluster_span` ascending
22. `first_match_offset` ascending
23. `match_density` descending
24. `snapshot_at` descending
25. `session_id` ascending

### Metric Semantics

- `line_start_exact_tag_colon_marker_match_count`
  - number of line-start exact-tag marker hits whose wrapper is immediately followed by `:` and then end-of-output or whitespace
- `first_line_start_exact_tag_colon_marker_offset`
  - earliest query offset among exact-tag colon-marker hits
  - when no such hit exists, use a stable sentinel so ordering falls back cleanly

All other metric semantics remain identical to `M8.5.26`.

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the two new colon-marker fields. Reuse the already-computed match offsets, the current exact-tag marker helper, and one new local helper that checks for `:` directly after the closing wrapper.

Do not change whole-word, line-start whole-word, raw log-marker, delimited raw-marker, wrapper, exact-tag, exact-tag-marker, or square-bracket detection semantics in this milestone. The new helper should be strictly additive.

Use a stable sentinel for `first_line_start_exact_tag_colon_marker_offset` when no such hit exists, so the order naturally falls back to the existing `M8.5.26` chain.

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

- exact-tag colon-marker hits such as `[query]: text` outrank exact-tag dash-marker hits such as `[query] - text`
- when exact-tag colon-marker counts tie, earlier `first_line_start_exact_tag_colon_marker_offset` wins
- when no exact-tag colon-marker hit exists, ordering falls back to the existing `M8.5.26` chain
- pagination still slices the fully ranked `relevance` list after the new ordering is applied

### Regression

Re-run the existing terminal-history search route/API regression coverage to confirm:

- search response shape is unchanged
- existing `relevance` / `newest` / `oldest` contracts remain valid
- timeline/detail/current-history compatibility stays intact
- OpenAPI and monitor surfaces remain unchanged

### Full Verification

Before handoff, run the same repo-wide verification expected by the current project workflow:

- focused terminal pytest selection
- full backend pytest suite
- `ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`
- `git diff --check`

