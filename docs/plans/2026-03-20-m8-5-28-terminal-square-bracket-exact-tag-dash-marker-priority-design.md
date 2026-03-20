# M8.5.28 Terminal Square-Bracket Exact-Tag Dash-Marker Priority Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so square-bracket exact-tag dash-marker hits such as `[query] - text` outrank other wrapper exact-tag dash-marker hits such as `(query) - text`, while preserving the existing priority of raw line-start markers, exact-tag colon markers, and the current API/UI/history compatibility boundaries.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep the existing match set unchanged:
  - substring matches still remain searchable and returnable
  - whole-word detection still remains ordering-only
  - line-start detection still remains ordering-only
  - raw log-marker detection still remains ordering-only
  - exact-tag wrapper detection still remains ordering-only
  - exact-tag marker detection still remains ordering-only
  - exact-tag colon-marker detection still remains ordering-only
  - the new square-bracket dash-marker signal only improves ordering among already matched snapshots
- add two lightweight ranking signals derived from already available search data:
  - `line_start_square_bracket_exact_tag_dash_marker_match_count`
  - `first_line_start_square_bracket_exact_tag_dash_marker_offset`
- preserve the existing `M8.5.27` relevance signals after the new square-bracket dash-marker signals:
  - `line_start_log_marker_match_count`
  - `line_start_delimited_log_marker_match_count`
  - `line_start_exact_tag_marker_match_count`
  - `line_start_exact_tag_colon_marker_match_count`
  - `line_start_exact_tag_match_count`
  - `line_start_square_bracket_exact_tag_match_count`
  - `line_start_punctuation_wrap_match_count`
  - `line_start_whole_word_match_count`
  - `conditional_non_line_start_whole_word_match_count`
  - `whole_word_match_count`
  - `first_line_start_log_marker_offset`
  - `first_line_start_delimited_log_marker_offset`
  - `first_line_start_exact_tag_marker_offset`
  - `first_line_start_exact_tag_colon_marker_offset`
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
- no generic wrapper-family weighting model
- no new colon-marker behavior
- no raw marker refinement in this milestone
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes

## Context

`M8.5.25` established that exact-tag marker forms such as `[query]: text` and `[query] - text` outrank plain exact-tag forms such as `[query] text`. `M8.5.26` then refined exact-tag wrappers so square-bracket exact-tag forms outrank other wrapper pairs. `M8.5.27` added another tie-break inside the exact-tag marker family by preferring colon markers such as `[query]: text` over dash markers such as `[query] - text`.

The next remaining rough edge is now inside the exact-tag dash-marker subfamily itself. Today `[error] - failed` and `(error) - failed` are effectively peers once stronger signals tie. Since square-bracket wrappers already represent the preferred exact-tag wrapper family, the smallest next step is to carry that preference into the dash-marker branch as well.

## Approaches Considered

### 1. Narrow square-bracket dash-marker tie-break

Add a signal that rewards only square-bracket exact-tag dash markers over other wrapper exact-tag dash markers.

Pros:

- smallest implementation delta
- aligns with the existing `M8.5.26` square-bracket preference
- easy to regression test

Cons:

- explicitly introduces one more narrow wrapper-family preference

### 2. General wrapper-family marker hierarchy

Add a broader ordering across multiple wrapper exact-tag marker forms.

Pros:

- more expressive

Cons:

- too wide for the next additive milestone
- more likely to need follow-up tuning

### 3. Unified exact-tag marker parser

Parse structured exact-tag markers and reason about wrapper and separator together.

Pros:

- most expressive

Cons:

- too large for this incremental backend-only step
- unnecessary complexity for the current cadence

## Recommended Approach

Use approach 1: a narrow square-bracket exact-tag dash-marker tie-break.

This keeps the change additive and explainable. It extends the existing square-bracket preference into the exact-tag dash-marker branch without changing broader family boundaries or introducing a wider marker grammar.

## Square-Bracket Dash-Marker Model

### Dash-Marker Rule

A match counts as a square-bracket exact-tag dash-marker hit when:

- it already satisfies the current line-start exact-tag marker rule
- it already satisfies the current line-start square-bracket exact-tag rule
- the text immediately after the closing wrapper begins with the strict delimiter ` -`
- the character after that delimiter is end-of-output or whitespace

The search match itself remains case-insensitive because the existing search offsets are already case-insensitive. Delimiter matching remains exact.

### Examples

- count as square-bracket exact-tag dash-marker hits:
  - `[error] - failed to attach`
  - `[error] -\nfailed to attach`
- do not count as square-bracket exact-tag dash-marker hits:
  - `(error) - failed to attach`
  - `[error]: failed to attach`
  - `[error]- failed to attach`
  - `prefix [error] - failed`

### Relative Strength

The new signal is additive inside the existing wrapper exact-tag marker family. It does not change the broader raw-marker-versus-wrapper hierarchy and does not outrank exact-tag colon markers.

Examples under `sort="relevance"`:

- `error: failed` still outranks `[error]: failed`
- `[error]: failed` still outranks `[error] - failed`
- `[error] - failed` outranks `(error) - failed`
- `(error) - failed` still outranks `(error) failed` because `M8.5.25` exact-tag marker priority remains in place

### Match Set Stability

The new rule does not change which snapshots match the query.

Examples:

- searching `error` still returns `[error] - failed`, `(error) - failed`, and `(error) failed`
- under `sort="relevance"`, square-bracket dash-marker results simply rank ahead of other wrapper dash-marker results when stronger signals are otherwise similar

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `line_start_log_marker_match_count` descending
3. `line_start_delimited_log_marker_match_count` descending
4. `line_start_exact_tag_marker_match_count` descending
5. `line_start_exact_tag_colon_marker_match_count` descending
6. `line_start_square_bracket_exact_tag_dash_marker_match_count` descending
7. `line_start_exact_tag_match_count` descending
8. `line_start_square_bracket_exact_tag_match_count` descending
9. `line_start_punctuation_wrap_match_count` descending
10. `line_start_whole_word_match_count` descending
11. `conditional_non_line_start_whole_word_match_count` ascending
12. `whole_word_match_count` descending
13. `first_line_start_log_marker_offset` ascending
14. `first_line_start_delimited_log_marker_offset` ascending
15. `first_line_start_exact_tag_colon_marker_offset` ascending
16. `first_line_start_square_bracket_exact_tag_dash_marker_offset` ascending
17. `first_line_start_exact_tag_marker_offset` ascending
18. `first_line_start_exact_tag_offset` ascending
19. `first_line_start_square_bracket_exact_tag_offset` ascending
20. `first_line_start_punctuation_wrap_offset` ascending
21. `first_line_start_whole_word_offset` ascending
22. `first_whole_word_offset` ascending
23. `cluster_span` ascending
24. `first_match_offset` ascending
25. `match_density` descending
26. `snapshot_at` descending
27. `session_id` ascending

### Metric Semantics

- `line_start_square_bracket_exact_tag_dash_marker_match_count`
  - number of line-start exact-tag marker hits whose wrapper is square brackets and whose wrapper is immediately followed by the strict delimiter ` -` and then end-of-output or whitespace
- `first_line_start_square_bracket_exact_tag_dash_marker_offset`
  - earliest query offset among square-bracket exact-tag dash-marker hits
  - when no such hit exists, use a stable sentinel so ordering falls back cleanly

All other metric semantics remain identical to `M8.5.27`.

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the two new square-bracket dash-marker fields. Reuse the already-computed match offsets, the current exact-tag marker helper, and one new local helper that checks for both the square-bracket wrapper and the strict ` -` delimiter directly after the closing wrapper.

Do not change whole-word, line-start whole-word, raw log-marker, delimited raw-marker, wrapper, exact-tag, exact-tag-marker, colon-marker, or square-bracket exact-tag detection semantics in this milestone. The new helper should be strictly additive.

Use a stable sentinel for `first_line_start_square_bracket_exact_tag_dash_marker_offset` when no such hit exists, so the order naturally falls back to the existing `M8.5.27` chain.

### Route

No route signature changes are needed. The existing `sort` enum and response DTOs remain unchanged.

### Pagination

Search pagination remains:

- build the full ordered match list first
- then apply `offset` / `limit`

This preserves existing search pagination, cross-session navigation, and snippet deep-link behavior.

## Testing Strategy

Add focused service tests that prove:

- `[query] - text` outranks `(query) - text`
- earlier `first_line_start_square_bracket_exact_tag_dash_marker_offset` wins when counts tie
- when no square-bracket dash-marker signal exists, ordering falls back to the `M8.5.27` chain
- pagination still slices the globally ranked results after the new ordering is applied

Then rerun the focused terminal regression suite plus the repository verification commands already used by recent `M8.5.x` backend-only milestones.
