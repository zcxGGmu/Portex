# M8.5.30 Terminal Non-Square-Bracket Exact-Tag Dash-Marker Placement Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so non-square-bracket exact-tag dash-marker hits such as `(query) - text`, `{query} - text`, and `<query> - text` can break ties by earlier placement after shared square-bracket dash-marker signals have already equalized stronger signals, while preserving the existing priority of raw line-start markers, square-bracket wrapper preference, exact-tag colon-marker preference, and all current API/UI/history compatibility boundaries.

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
  - non-square-bracket exact-tag colon-marker detection still remains ordering-only
  - the new non-square-bracket dash-marker signal only improves ordering among already matched snapshots
- add two lightweight ranking signals derived from already available search data:
  - `line_start_non_square_bracket_exact_tag_dash_marker_match_count`
  - `first_line_start_non_square_bracket_exact_tag_dash_marker_offset`
- preserve the existing `M8.5.29` relevance signals after the new non-square-bracket dash-marker signals:
  - `line_start_log_marker_match_count`
  - `line_start_delimited_log_marker_match_count`
  - `line_start_exact_tag_marker_match_count`
  - `line_start_exact_tag_colon_marker_match_count`
  - `line_start_square_bracket_exact_tag_dash_marker_match_count`
  - `line_start_non_square_bracket_exact_tag_colon_marker_match_count`
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
  - `first_line_start_non_square_bracket_exact_tag_colon_marker_offset`
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
- no generic non-square-bracket wrapper precedence
- no new non-square-bracket dash-marker strength-over-noise rule in this milestone
- no raw marker refinement in this milestone
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes

## Context

`M8.5.25` established that exact-tag marker forms such as `[query]: text` and `[query] - text` outrank plain exact-tag forms such as `[query] text`. `M8.5.26` then refined exact-tag wrappers so square-bracket exact-tag forms outrank other wrapper pairs. `M8.5.27` added a tie-break inside the exact-tag marker family by preferring colon markers such as `[query]: text` over dash markers such as `[query] - text`. `M8.5.28` extended the square-bracket preference into the dash-marker branch so `[query] - text` can outrank generic exact-tag noise and earlier non-square-bracket marker placement. `M8.5.29` then extended the tie-break chain into the non-square-bracket colon-marker branch so `(query): text` can win once shared square-bracket colon markers have already equalized stronger signals.

The next remaining rough edge is now inside the non-square-bracket exact-tag dash-marker family. Today two snapshots that both share the same square-bracket dash-marker baseline can still fall through to broader exact-tag or generic offset signals even when one has an earlier non-square-bracket dash-marker placement. The smallest next step is to carry the same placement-sensitive tie-break pattern into the non-square-bracket dash-marker branch without widening the overall marker hierarchy.

## Approaches Considered

### 1. Narrow non-square-bracket dash-marker placement tie-break

Add a signal that rewards only non-square-bracket exact-tag dash-marker hits after shared square-bracket dash-marker baselines have already tied stronger signals.

Pros:

- smallest implementation delta
- aligns with the existing `M8.5.29` placement-sensitive non-square-bracket colon-marker refinement
- avoids changing broader family strength rules

Cons:

- explicitly introduces one more narrow wrapper-marker tie-break

### 2. Broader non-square-bracket dash-marker strength rule

Add broader ordering so non-square-bracket dash-marker hits more often outrank generic exact-tag noise directly.

Pros:

- reduces future micro-iterations

Cons:

- too wide for the next additive milestone
- increases regression surface

### 3. Wrapper-specific dash precedence

Define ordering between `()`, `{}`, and `<>` inside the dash-marker family.

Pros:

- most expressive

Cons:

- too subjective for the current evidence
- unnecessary for this incremental backend-only step

## Recommended Approach

Use approach 1: a narrow non-square-bracket exact-tag dash-marker placement tie-break.

This keeps the change additive and symmetric with `M8.5.29`. It improves the non-square-bracket dash-marker branch only when stronger signals are already tied, without broadening the overall search contract or introducing wrapper-pair subjectivity.

## Non-Square-Bracket Dash-Marker Model

### Dash-Marker Rule

A match counts as a non-square-bracket exact-tag dash-marker hit when:

- it already satisfies the current line-start exact-tag marker rule
- it already satisfies the current line-start exact-tag rule
- it does not satisfy the current line-start square-bracket exact-tag rule
- the text immediately after the closing wrapper begins with the strict delimiter ` -`
- the character after that delimiter is end-of-output or whitespace

The search match itself remains case-insensitive because the existing search offsets are already case-insensitive. Delimiter matching remains exact.

### Examples

- count as non-square-bracket exact-tag dash-marker hits:
  - `(error) - failed to attach`
  - `{error} - failed to attach`
  - `<error> -\nfailed to attach`
- do not count as non-square-bracket exact-tag dash-marker hits:
  - `[error] - failed to attach`
  - `(error): failed to attach`
  - `(error)- failed to attach`
  - `prefix (error) - failed`

### Relative Strength

The new signal is additive inside the existing non-square-bracket exact-tag dash-marker family. It does not change the broader raw-marker-versus-wrapper hierarchy, does not outrank the square-bracket dash-marker chain, and does not outrank the non-square-bracket colon-marker chain.

Examples under `sort="relevance"`:

- `error - failed` still outranks `[error] - failed`
- `[error] - failed` still outranks `(error) - failed`
- `(error): failed` still outranks `(error) - failed`
- when both snapshots share the same `[error] - ...` baseline, the one with the earlier `(error) - ...` placement can outrank the later one

### Match Set Stability

The new rule does not change which snapshots match the query.

Examples:

- searching `error` still returns `[error] - failed`, `(error) - failed`, and `(error) failed`
- under `sort="relevance"`, non-square-bracket dash-marker results simply gain a new tie-break after the stronger square-bracket dash-marker baseline has already tied

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `line_start_log_marker_match_count` descending
3. `line_start_delimited_log_marker_match_count` descending
4. `line_start_exact_tag_marker_match_count` descending
5. `line_start_exact_tag_colon_marker_match_count` descending
6. `line_start_square_bracket_exact_tag_dash_marker_match_count` descending
7. `line_start_non_square_bracket_exact_tag_colon_marker_match_count` descending
8. `line_start_non_square_bracket_exact_tag_dash_marker_match_count` descending
9. `line_start_exact_tag_match_count` descending
10. `line_start_square_bracket_exact_tag_match_count` descending
11. `line_start_punctuation_wrap_match_count` descending
12. `line_start_whole_word_match_count` descending
13. `conditional_non_line_start_whole_word_match_count` ascending
14. `whole_word_match_count` descending
15. `first_line_start_log_marker_offset` ascending
16. `first_line_start_delimited_log_marker_offset` ascending
17. `first_line_start_exact_tag_colon_marker_offset` ascending
18. `first_line_start_square_bracket_exact_tag_dash_marker_offset` ascending
19. `first_line_start_non_square_bracket_exact_tag_colon_marker_offset` ascending
20. `first_line_start_non_square_bracket_exact_tag_dash_marker_offset` ascending
21. `first_line_start_exact_tag_marker_offset` ascending
22. `first_line_start_exact_tag_offset` ascending
23. `first_line_start_square_bracket_exact_tag_offset` ascending
24. `first_line_start_punctuation_wrap_offset` ascending
25. `first_line_start_whole_word_offset` ascending
26. `first_whole_word_offset` ascending
27. `cluster_span` ascending
28. `first_match_offset` ascending
29. `match_density` descending
30. `snapshot_at` descending
31. `session_id` ascending

### Metric Semantics

- `line_start_non_square_bracket_exact_tag_dash_marker_match_count`
  - number of line-start exact-tag dash-marker hits whose wrapper is not square brackets
- `first_line_start_non_square_bracket_exact_tag_dash_marker_offset`
  - earliest query offset among non-square-bracket exact-tag dash-marker hits
  - when no such hit exists, use a stable sentinel so ordering falls back cleanly

All other metric semantics remain identical to `M8.5.29`.

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the two new non-square-bracket dash-marker fields. Reuse the already-computed match offsets, the current exact-tag marker helper, the current exact-tag helper, and the current square-bracket exact-tag helper. The new helper should only recognize hits that are already dash markers and already exact tags, but are explicitly not square-bracket exact tags.

Do not change whole-word, line-start whole-word, raw log-marker, delimited raw-marker, punctuation wrapper, exact-tag, exact-tag-marker, square-bracket exact-tag, square-bracket dash-marker, or non-square-bracket colon-marker detection semantics in this milestone. The new helper should be strictly additive.

Use a stable sentinel for `first_line_start_non_square_bracket_exact_tag_dash_marker_offset` when no such hit exists, so the order naturally falls back to the existing `M8.5.29` chain.

### Route

No route signature changes are needed. The existing `sort` enum and response DTOs remain unchanged.

### Pagination

Search pagination remains:

- build the full ordered match list first
- then apply `offset` / `limit`

This preserves existing search pagination, cross-session navigation, and snippet deep-link behavior.

## Testing Strategy

Add focused service tests that prove:

- once shared square-bracket dash-marker baselines tie, earlier non-square-bracket dash-marker placement wins
- earlier `first_line_start_non_square_bracket_exact_tag_dash_marker_offset` wins when non-square-bracket dash-marker counts tie
- when no non-square-bracket dash-marker signal exists, ordering falls back to the `M8.5.29` chain
- pagination still slices the globally ranked results after the new ordering is applied

Then rerun the focused terminal regression suite plus the repository verification commands already used by recent `M8.5.x` backend-only milestones.
