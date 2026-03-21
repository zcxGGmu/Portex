# M8.5.33 Terminal Angle-Wrapper Exact-Tag Demotion Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so angle-wrapped plain exact-tag hits such as `<query> text` rank behind other non-square plain exact-tag hits such as `(query) text` and `{query} text`, while preserving the existing priority of raw line-start markers, exact-tag marker families, square-bracket wrapper preference, and all current API/UI/history compatibility boundaries.

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
  - brace-wrapper marker detection still remains ordering-only
  - non-square-bracket exact-tag colon-marker detection still remains ordering-only
  - non-square-bracket exact-tag dash-marker detection still remains ordering-only
  - the new angle-wrapper plain exact-tag signal only improves ordering among already matched snapshots
- add one lightweight ranking signal derived from already available search data:
  - `line_start_angle_wrapper_plain_exact_tag_match_count`
- preserve the existing `M8.5.32` relevance signals around the new signal:
  - `line_start_log_marker_match_count`
  - `line_start_delimited_log_marker_match_count`
  - `line_start_exact_tag_marker_match_count`
  - `line_start_exact_tag_colon_marker_match_count`
  - `line_start_square_bracket_exact_tag_dash_marker_match_count`
  - `line_start_paren_wrapper_marker_match_count`
  - `line_start_brace_wrapper_marker_match_count`
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
  - `first_line_start_brace_wrapper_marker_offset`
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
- no new wrapper-family model beyond the narrow `<>` demotion rule
- no changes to marker-family precedence from `M8.5.25` through `M8.5.32`
- no new precedence between `()` and `{}`
- no raw marker refinement in this milestone
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes

## Context

`M8.5.22` introduced punctuation-aware line-start wrapper relevance. `M8.5.23` then refined delimiter-aware exact-tag wrappers such as `[query] text`, `[query]: text`, and `[query] - text`. `M8.5.25` through `M8.5.32` iteratively refined the marker branch of the exact-tag family: exact-tag markers, square-bracket priority, colon-marker and dash-marker sub-ordering, then `()` over `{}` / `<>`, and finally `{}` over `<>` for wrapper markers.

The next remaining rough edge is now the plain exact-tag branch rather than the marker branch. Today `(error) failed`, `{error} failed`, and `<error> failed` are effectively peers once stronger signals tie. A direct positive `{}` signal would unintentionally also separate `{}` from `()`, which is broader than intended. The smallest safe next step is therefore to demote only the `<>` plain exact-tag family so it falls behind the other non-square plain exact-tag wrappers, while keeping `()` and `{}` tied.

## Approaches Considered

### 1. Narrow angle-wrapper demotion

Add a signal that penalizes only angle-wrapped plain exact-tag hits.

Pros:

- smallest implementation delta
- keeps `()` and `{}` tied
- avoids widening the wrapper-family ordering model

Cons:

- expresses the rule as a demotion rather than a positive preference

### 2. Positive brace-wrapper plain exact-tag preference

Add a positive `{}` signal in the plain exact-tag branch.

Pros:

- straightforward to describe

Cons:

- would also make `{}` outrank `()`
- wider behavior change than the approved goal

### 3. Full plain-wrapper ordering model

Define explicit plain exact-tag ordering across `[]`, `()`, `{}`, and `<>`.

Pros:

- more uniform on paper

Cons:

- too wide for the next backend-only milestone
- increases regression surface without enough evidence

## Recommended Approach

Use approach 1: a narrow angle-wrapper demotion.

This keeps the change additive and stable. It fixes the remaining `<>` rough edge in the plain exact-tag branch without introducing a broader `()` versus `{}` ordering model and without widening the public search contract.

## Angle-Wrapper Plain Exact-Tag Model

### Plain Exact-Tag Rule

A match counts toward the new signal when:

- it already satisfies the current line-start exact-tag rule
- it does not satisfy the current line-start exact-tag marker rule
- the opening wrapper is `<`
- the closing wrapper is `>`

This intentionally limits the new signal to plain exact-tag forms such as `<error> failed`. Colon-style and dash-style marker forms remain governed only by the existing marker-family signals from earlier milestones.

### Examples

- count toward the new signal:
  - `<error> failed to attach`
  - `<error> failed`
- do not count toward the new signal:
  - `<error>: failed to attach`
  - `<error> - failed to attach`
  - `{error} failed to attach`
  - `(error) failed to attach`

### Relative Strength

The new signal is a narrow demotion inside the plain exact-tag branch. It does not change the broader raw-marker-versus-wrapper hierarchy, does not change any exact-tag marker ordering, and does not create a new precedence between `()` and `{}`.

Examples under `sort="relevance"`:

- `error: failed` still outranks `[error]: failed`
- `[error]: failed` still outranks `(error) failed`
- `(error) failed` outranks `<error> failed`
- `{error} failed` outranks `<error> failed`
- `(error) failed` and `{error} failed` remain peers unless some other existing signal distinguishes them

### Match Set Stability

The new rule does not change which snapshots match the query.

Examples:

- searching `error` still returns `(error) failed`, `{error} failed`, and `<error> failed`
- under `sort="relevance"`, angle-wrapped plain exact-tag results simply rank behind other plain exact-tag wrapper results when stronger signals are otherwise similar

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
13. `line_start_angle_wrapper_plain_exact_tag_match_count` ascending
14. `line_start_punctuation_wrap_match_count` descending
15. `line_start_whole_word_match_count` descending
16. `conditional_non_line_start_whole_word_match_count` ascending
17. `whole_word_match_count` descending
18. `first_line_start_log_marker_offset` ascending
19. `first_line_start_delimited_log_marker_offset` ascending
20. `first_line_start_exact_tag_colon_marker_offset` ascending
21. `first_line_start_square_bracket_exact_tag_dash_marker_offset` ascending
22. `first_line_start_paren_wrapper_marker_offset` ascending
23. `first_line_start_brace_wrapper_marker_offset` ascending
24. `first_line_start_non_square_bracket_exact_tag_colon_marker_offset` ascending
25. `first_line_start_non_square_bracket_exact_tag_dash_marker_offset` ascending
26. `first_line_start_exact_tag_marker_offset` ascending
27. `first_line_start_exact_tag_offset` ascending
28. `first_line_start_square_bracket_exact_tag_offset` ascending
29. `first_line_start_punctuation_wrap_offset` ascending
30. `first_line_start_whole_word_offset` ascending
31. `first_whole_word_offset` ascending
32. `cluster_span` ascending
33. `first_match_offset` ascending
34. `match_density` descending
35. `snapshot_at` descending
36. `session_id` ascending

### Metric Semantics

- `line_start_angle_wrapper_plain_exact_tag_match_count`
  - number of line-start plain exact-tag hits whose wrapper pair is `<>`
  - lower is better because this is an explicit demotion signal inside the plain exact-tag branch

All other metric semantics remain identical to `M8.5.32`.

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the one new angle-wrapper plain exact-tag count field. Reuse the already-computed match offsets plus the existing exact-tag and exact-tag-marker helpers. The new helper should recognize hits only when they are already plain exact-tags and the wrapper pair is exactly `<>`.

Do not change whole-word, line-start whole-word, raw log-marker, delimited raw-marker, punctuation wrapper, exact-tag, exact-tag marker, square-bracket exact-tag, square-bracket dash-marker, paren-wrapper marker, brace-wrapper marker, non-square-bracket colon-marker, or non-square-bracket dash-marker detection semantics in this milestone. The new helper should be strictly additive and should not alter marker-family behavior.

### Route

No route signature changes are needed. The existing `sort` enum and response DTOs remain unchanged.

### Pagination

Search pagination remains:

- build the full ordered match list first
- then apply `offset` / `limit`

This preserves existing search pagination, cross-session navigation, and snippet deep-link behavior.

## Testing Strategy

Add focused service tests that prove:

- plain exact-tag results such as `{query} text` outrank `<query> text`
- plain exact-tag results such as `(query) text` outrank `<query> text`
- when no angle-wrapper plain exact-tag signal exists, ordering falls back to the `M8.5.32` chain
- pagination still slices the globally ranked results after the new ordering is applied

Then rerun the focused terminal regression suite plus the repository verification commands already used by recent `M8.5.x` backend-only milestones.
