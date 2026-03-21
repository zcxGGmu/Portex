# M8.5.32 Terminal Brace-Wrapper Marker Precedence Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so brace-wrapped exact-tag marker hits such as `{query}: text` and `{query} - text` outrank angle-wrapped exact-tag marker hits such as `<query>: text` and `<query> - text`, while preserving the existing priority of raw line-start markers, square-bracket wrapper preference, paren-wrapper marker preference, and all current API/UI/history compatibility boundaries.

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
  - square-bracket exact-tag dash-marker detection still remains ordering-only
  - paren-wrapper marker detection still remains ordering-only
  - non-square-bracket exact-tag colon-marker detection still remains ordering-only
  - non-square-bracket exact-tag dash-marker detection still remains ordering-only
  - the new brace-wrapper marker signal only improves ordering among already matched snapshots
- add two lightweight ranking signals derived from already available search data:
  - `line_start_brace_wrapper_marker_match_count`
  - `first_line_start_brace_wrapper_marker_offset`
- preserve the existing `M8.5.31` relevance signals after the new brace-wrapper marker signals:
  - `line_start_log_marker_match_count`
  - `line_start_delimited_log_marker_match_count`
  - `line_start_exact_tag_marker_match_count`
  - `line_start_exact_tag_colon_marker_match_count`
  - `line_start_square_bracket_exact_tag_dash_marker_match_count`
  - `line_start_paren_wrapper_marker_match_count`
  - `line_start_non_square_bracket_exact_tag_colon_marker_match_count`
  - `line_start_non_square_bracket_exact_tag_dash_marker_match_count`
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
  - `first_line_start_square_bracket_exact_tag_dash_marker_offset`
  - `first_line_start_paren_wrapper_marker_offset`
  - `first_line_start_non_square_bracket_exact_tag_colon_marker_offset`
  - `first_line_start_non_square_bracket_exact_tag_dash_marker_offset`
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
- no new wrapper-family model beyond the narrow `{}` over `<>` rule
- no changes to `()` precedence from `M8.5.31`
- no raw marker refinement in this milestone
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes

## Context

`M8.5.25` established that exact-tag marker forms such as `[query]: text` and `[query] - text` outrank plain exact-tag forms such as `[query] text`. `M8.5.26` then refined exact-tag wrappers so square-bracket exact-tag forms outrank other wrapper pairs. `M8.5.27` added a tie-break inside the exact-tag marker family by preferring colon markers such as `[query]: text` over dash markers such as `[query] - text`. `M8.5.28` extended the square-bracket preference into the dash-marker branch. `M8.5.29` added a non-square-bracket colon-marker tie-break after shared square-bracket colon baselines have already equalized stronger signals. `M8.5.30` added a non-square-bracket dash-marker placement tie-break after shared square-bracket dash baselines have already equalized stronger signals. `M8.5.31` then added a narrow paren-wrapper marker precedence so `(query): text` and `(query) - text` outrank the remaining non-square wrapper marker peers.

The next remaining rough edge is now the `{}` versus `<>` branch inside the non-square wrapper marker family. Today `{error}: failed`, `<error>: failed`, `{error} - failed`, and `<error> - failed` are still effectively peers once stronger signals tie and there is no `()` hit. The smallest next step is to reward the brace-wrapper marker family over the angle-wrapper marker family while intentionally keeping the change backend-only and limited to already matched exact-tag marker hits.

## Approaches Considered

### 1. Narrow brace-over-angle precedence

Add a signal that rewards only brace-wrapped exact-tag marker hits over angle-wrapped exact-tag marker hits.

Pros:

- smallest implementation delta
- directly continues the existing `M8.5.31` incremental wrapper chain
- easy to explain and regression test

Cons:

- explicitly introduces one more narrow wrapper-pair rule

### 2. Full wrapper-family ordering model

Replace the current additive chain with a single explicit wrapper precedence model across `[]`, `()`, `{}`, and `<>`.

Pros:

- looks more uniform on paper

Cons:

- too wide for the next backend-only milestone
- risks disturbing a search-quality chain that is already covered by focused tests

### 3. Skip wrapper work and add a different relevance signal

Leave `{}` and `<>` tied and move to another signal family.

Pros:

- could explore a different ranking dimension

Cons:

- leaves the most obvious remaining wrapper-family rough edge unresolved
- breaks the current small-step refinement cadence

## Recommended Approach

Use approach 1: a narrow brace-over-angle precedence.

This keeps the change additive and easy to audit. It preserves the existing hierarchy of raw markers, square-bracket wrappers, and paren-wrapper markers, while filling the next smallest gap inside the non-square wrapper marker family without broadening the public search contract.

## Brace-Wrapper Marker Model

### Marker Rule

A match counts as a brace-wrapper marker hit when:

- it already satisfies the current line-start exact-tag marker rule
- it already satisfies the current line-start exact-tag rule
- the opening wrapper is `{`
- the closing wrapper is `}`

Delimiter matching remains unchanged because the existing exact-tag marker rule already constrains the post-wrapper text to `:` + delimiter or strict ` -` + delimiter. The search match itself remains case-insensitive because the existing search offsets are already case-insensitive.

### Examples

- count as brace-wrapper marker hits:
  - `{error}: failed to attach`
  - `{error} - failed to attach`
- do not count as brace-wrapper marker hits:
  - `<error>: failed to attach`
  - `(error) - failed to attach`
  - `[error]: failed to attach`
  - `{error} failed to attach`

### Relative Strength

The new signal is additive inside the existing wrapper marker family. It does not change the broader raw-marker-versus-wrapper hierarchy, does not outrank the square-bracket marker chain, and does not outrank the paren-wrapper marker chain.

Examples under `sort="relevance"`:

- `error: failed` still outranks `[error]: failed`
- `[error]: failed` still outranks `(error): failed`
- `(error): failed` still outranks `{error}: failed`
- `{error}: failed` outranks `<error>: failed`
- `{error} - failed` outranks `<error> - failed`

### Match Set Stability

The new rule does not change which snapshots match the query.

Examples:

- searching `error` still returns `{error}: failed`, `<error>: failed`, and `<error> - failed`
- under `sort="relevance"`, brace-wrapped marker results simply rank ahead of angle-wrapped marker results when stronger signals are otherwise similar

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `line_start_log_marker_match_count` descending
3. `line_start_delimited_log_marker_match_count` descending
4. `line_start_exact_tag_marker_match_count` descending
5. `line_start_exact_tag_colon_marker_match_count` descending
6. `line_start_square_bracket_exact_tag_dash_marker_match_count` descending
7. `line_start_paren_wrapper_marker_match_count` descending
8. `line_start_brace_wrapper_marker_match_count` descending
9. `line_start_non_square_bracket_exact_tag_colon_marker_match_count` descending
10. `line_start_non_square_bracket_exact_tag_dash_marker_match_count` descending
11. `line_start_exact_tag_match_count` descending
12. `line_start_square_bracket_exact_tag_match_count` descending
13. `line_start_punctuation_wrap_match_count` descending
14. `line_start_whole_word_match_count` descending
15. `conditional_non_line_start_whole_word_match_count` ascending
16. `whole_word_match_count` descending
17. `first_line_start_log_marker_offset` ascending
18. `first_line_start_delimited_log_marker_offset` ascending
19. `first_line_start_exact_tag_colon_marker_offset` ascending
20. `first_line_start_square_bracket_exact_tag_dash_marker_offset` ascending
21. `first_line_start_paren_wrapper_marker_offset` ascending
22. `first_line_start_brace_wrapper_marker_offset` ascending
23. `first_line_start_non_square_bracket_exact_tag_colon_marker_offset` ascending
24. `first_line_start_non_square_bracket_exact_tag_dash_marker_offset` ascending
25. `first_line_start_exact_tag_marker_offset` ascending
26. `first_line_start_exact_tag_offset` ascending
27. `first_line_start_square_bracket_exact_tag_offset` ascending
28. `first_line_start_punctuation_wrap_offset` ascending
29. `first_line_start_whole_word_offset` ascending
30. `first_whole_word_offset` ascending
31. `cluster_span` ascending
32. `first_match_offset` ascending
33. `match_density` descending
34. `snapshot_at` descending
35. `session_id` ascending

### Metric Semantics

- `line_start_brace_wrapper_marker_match_count`
  - number of line-start exact-tag marker hits whose wrapper pair is `{}`
- `first_line_start_brace_wrapper_marker_offset`
  - earliest query offset among brace-wrapper marker hits
  - when no such hit exists, use a stable sentinel so ordering falls back cleanly

All other metric semantics remain identical to `M8.5.31`.

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the two new brace-wrapper marker fields. Reuse the already-computed match offsets and the existing exact-tag marker helper. The new helper should only recognize hits that are already exact-tag markers and whose wrapper pair is exactly `{}`.

Do not change whole-word, line-start whole-word, raw log-marker, delimited raw-marker, punctuation wrapper, exact-tag, exact-tag marker, square-bracket exact-tag, square-bracket dash-marker, paren-wrapper marker, non-square-bracket colon-marker, or non-square-bracket dash-marker detection semantics in this milestone. The new helper should be strictly additive.

Use a stable sentinel for `first_line_start_brace_wrapper_marker_offset` when no such hit exists, so the order naturally falls back to the existing `M8.5.31` chain.

### Route

No route signature changes are needed. The existing `sort` enum and response DTOs remain unchanged.

### Pagination

Search pagination remains:

- build the full ordered match list first
- then apply `offset` / `limit`

This preserves existing search pagination, cross-session navigation, and snippet deep-link behavior.

## Testing Strategy

Add focused service tests that prove:

- brace-wrapper marker hits outrank angle-wrapper marker hits when stronger signals tie
- earlier `first_line_start_brace_wrapper_marker_offset` wins when brace-wrapper marker counts tie
- when no brace-wrapper marker signal exists, ordering falls back to the `M8.5.31` chain
- pagination still slices the globally ranked results after the new ordering is applied

Then rerun the focused terminal regression suite plus the repository verification commands already used by recent `M8.5.x` backend-only milestones.
