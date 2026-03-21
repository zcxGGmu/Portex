# M8.5.35 Terminal Exact-Tag Punctuation-Noise Demotion Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so line-start exact-tag hits such as `(query) text`, `{query} text`, and `[query] text` rank ahead of otherwise similar results that carry extra tighter-wrapper punctuation noise such as `(query)text`, `{query}text`, or `<query>text`, while preserving the existing priority of raw line-start markers, exact-tag marker families, square-bracket wrapper preference, and all current API/UI/history compatibility boundaries.

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
  - angle-wrapper plain exact-tag demotion still remains ordering-only
  - paren-wrapper plain exact-tag precedence still remains ordering-only
  - non-square-bracket exact-tag colon-marker detection still remains ordering-only
  - non-square-bracket exact-tag dash-marker detection still remains ordering-only
  - the new exact-tag punctuation-noise signal only improves ordering among already matched snapshots
- add one lightweight ranking signal derived from already available search data:
  - `conditional_non_exact_tag_punctuation_wrap_match_count`
- preserve the existing `M8.5.34` relevance signals around the new signal:
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
  - `line_start_paren_wrapper_plain_exact_tag_match_count`
  - `line_start_angle_wrapper_plain_exact_tag_match_count`
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
  - `first_line_start_paren_wrapper_plain_exact_tag_offset`
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
- no broader wrapper-family model beyond the narrow exact-tag punctuation-noise demotion
- no changes to marker-family precedence from `M8.5.25` through `M8.5.34`
- no raw marker refinement in this milestone
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes

## Context

`M8.5.22` introduced punctuation-aware line-start wrapper relevance. `M8.5.23` then promoted delimiter-aware exact-tag wrappers above tighter wrappers. `M8.5.25` through `M8.5.32` iteratively refined the marker branch of the exact-tag family. `M8.5.33` and `M8.5.34` then refined the plain exact-tag branch so `<query> text` falls behind `(query) text` and `{query} text`, and `(query) text` outranks `{query} text`.

The next remaining rough edge is not another wrapper-family precedence gap. It is noise sensitivity inside snapshots that already contain exact-tag hits. Today a snapshot such as `{error} aa\n{error}aa\n` can gain extra credit from `line_start_punctuation_wrap_match_count` because the tighter wrapper `{error}aa` is still a punctuation-wrap hit, even though it should act as noise once an exact-tag hit already exists in the same snapshot. The smallest next step is to add a conditional demotion signal that counts non-exact-tag punctuation-wrap noise only when at least one line-start exact-tag hit exists.

## Approaches Considered

### 1. Conditional exact-tag punctuation-noise demotion

Add a conditional signal that penalizes extra punctuation-wrap hits beyond the exact-tag hits, but only when at least one exact-tag hit exists.

Pros:

- directly targets the actual ranking defect
- stays neutral when no exact-tag hit exists
- reuses the same conditional-demotion pattern already used by `M8.5.20`

Cons:

- slightly broader than a single wrapper-pair preference

### 2. Brace-specific plain exact-tag refinement

Reward only brace-wrapped plain exact-tag hits in more cases.

Pros:

- narrower on paper

Cons:

- misses the same noise problem for `[]`, `()`, and other wrapper families
- duplicates work across multiple wrapper families later

### 3. Generic cleanliness model

Introduce a wider ranking model for multiple kinds of textual noise around exact-tag results.

Pros:

- more expressive

Cons:

- too wide for the next incremental backend-only milestone
- increases regression surface without enough evidence

## Recommended Approach

Use approach 1: a conditional exact-tag punctuation-noise demotion.

This keeps the change additive and evidence-based. It fixes the actual gap in the current ranking chain without widening the public search contract or introducing another wrapper-specific mini-hierarchy.

## Exact-Tag Punctuation-Noise Model

### Noise Rule

The new signal is:

- `conditional_non_exact_tag_punctuation_wrap_match_count`

Calculate it as:

- `line_start_punctuation_wrap_match_count - line_start_exact_tag_match_count` when `line_start_exact_tag_match_count > 0`
- `0` when `line_start_exact_tag_match_count == 0`

Because line-start exact-tag hits are a strict subset of line-start punctuation-wrap hits, this value is non-negative. Lower is better.

### Examples

- noise count is `0`:
  - `{error} failed\nterror zz`
  - `(error) failed\nterror zz`
- noise count is `1`:
  - `{error} failed\n{error}failed`
  - `(error) failed\n(error)failed`
- signal stays neutral:
  - `{error}failed\nmid error here`
  - `<error>failed\nmid error here`
  - because there is no exact-tag hit in the snapshot

### Relative Strength

The new signal is a conditional demotion inside the exact-tag branch. It does not change the broader raw-marker-versus-wrapper hierarchy, does not change marker ordering, and does not replace the existing wrapper-family preferences from `M8.5.33` and `M8.5.34`.

Examples under `sort="relevance"`:

- `{error} failed\nterror zz` outranks `{error} failed\n{error}failed`
- `(error) failed\nterror zz` outranks `(error) failed\n(error)failed`
- if neither snapshot has any exact-tag hit, the new signal is neutral and ordering falls back to the existing punctuation-wrap chain

### Match Set Stability

The new rule does not change which snapshots match the query.

Examples:

- searching `error` still returns `{error} failed`, `{error}failed`, and `(error) failed`
- under `sort="relevance"`, snapshots with exact-tag hits simply stop getting extra credit from additional tighter-wrapper punctuation noise

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
13. `line_start_paren_wrapper_plain_exact_tag_match_count` descending
14. `line_start_angle_wrapper_plain_exact_tag_match_count` ascending
15. `conditional_non_exact_tag_punctuation_wrap_match_count` ascending
16. `line_start_punctuation_wrap_match_count` descending
17. `line_start_whole_word_match_count` descending
18. `conditional_non_line_start_whole_word_match_count` ascending
19. `whole_word_match_count` descending
20. `first_line_start_log_marker_offset` ascending
21. `first_line_start_delimited_log_marker_offset` ascending
22. `first_line_start_exact_tag_colon_marker_offset` ascending
23. `first_line_start_square_bracket_exact_tag_dash_marker_offset` ascending
24. `first_line_start_paren_wrapper_marker_offset` ascending
25. `first_line_start_brace_wrapper_marker_offset` ascending
26. `first_line_start_non_square_bracket_exact_tag_colon_marker_offset` ascending
27. `first_line_start_non_square_bracket_exact_tag_dash_marker_offset` ascending
28. `first_line_start_paren_wrapper_plain_exact_tag_offset` ascending
29. `first_line_start_exact_tag_marker_offset` ascending
30. `first_line_start_exact_tag_offset` ascending
31. `first_line_start_square_bracket_exact_tag_offset` ascending
32. `first_line_start_punctuation_wrap_offset` ascending
33. `first_line_start_whole_word_offset` ascending
34. `first_whole_word_offset` ascending
35. `cluster_span` ascending
36. `first_match_offset` ascending
37. `match_density` descending
38. `snapshot_at` descending
39. `session_id` ascending

### Metric Semantics

- `conditional_non_exact_tag_punctuation_wrap_match_count`
  - count of line-start punctuation-wrap hits that are not exact-tag hits, but only when at least one exact-tag hit exists
  - lower is better
  - when no exact-tag hit exists, use `0` so ordering falls back cleanly

All other metric semantics remain identical to `M8.5.34`.

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the one new conditional exact-tag punctuation-noise count field. Reuse the already-computed `line_start_punctuation_wrap_match_count` and `line_start_exact_tag_match_count` values. The new field should be purely derived; no new parsing helper is required.

Do not change whole-word, line-start whole-word, raw log-marker, delimited raw-marker, punctuation wrapper, exact-tag, exact-tag marker, square-bracket exact-tag, square-bracket dash-marker, paren-wrapper marker, brace-wrapper marker, angle-wrapper plain exact-tag demotion, paren-wrapper plain exact-tag precedence, non-square-bracket colon-marker, or non-square-bracket dash-marker detection semantics in this milestone. The new signal should be strictly additive and should stay neutral when no exact-tag hit exists.

### Route

No route signature changes are needed. The existing `sort` enum and response DTOs remain unchanged.

### Pagination

Search pagination remains:

- build the full ordered match list first
- then apply `offset` / `limit`

This preserves existing search pagination, cross-session navigation, and snippet deep-link behavior.

## Testing Strategy

Add focused service tests that prove:

- exact-tag results outrank otherwise similar snapshots that carry extra tighter-wrapper punctuation noise
- when stronger exact-tag signals tie, fewer `conditional_non_exact_tag_punctuation_wrap_match_count` wins
- when no exact-tag hit exists, ordering falls back to the `M8.5.34` chain
- pagination still slices the globally ranked results after the new ordering is applied

Then rerun the focused terminal regression suite plus the repository verification commands already used by recent `M8.5.x` backend-only milestones.
