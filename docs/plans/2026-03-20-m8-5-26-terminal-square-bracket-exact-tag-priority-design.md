# M8.5.26 Terminal Square-Bracket Exact-Tag Priority Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so square-bracket exact-tag hits such as `[query] text`, `[query]: text`, and `[query] - text` outrank other wrapper exact-tag hits such as `(query) text`, `{query} text`, and `<query> text`, while preserving the existing priority of raw line-start markers over wrapper families. Keep the current search API, UI surface, RBAC, pagination model, and history compatibility boundaries unchanged.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep the existing match set unchanged:
  - substring matches still remain searchable and returnable
  - whole-word detection still remains ordering-only
  - line-start detection still remains ordering-only
  - raw log-marker detection still remains ordering-only
  - exact-tag wrapper detection still remains ordering-only
  - the new square-bracket signal only improves ordering among already matched snapshots
- add two lightweight ranking signals derived from already available search data:
  - `line_start_square_bracket_exact_tag_match_count`
  - `first_line_start_square_bracket_exact_tag_offset`
- preserve the existing `M8.5.25` relevance signals after the new square-bracket signals:
  - `line_start_log_marker_match_count`
  - `line_start_delimited_log_marker_match_count`
  - `line_start_exact_tag_marker_match_count`
  - `line_start_exact_tag_match_count`
  - `line_start_punctuation_wrap_match_count`
  - `line_start_whole_word_match_count`
  - `conditional_non_line_start_whole_word_match_count`
  - `whole_word_match_count`
  - `first_line_start_log_marker_offset`
  - `first_line_start_delimited_log_marker_offset`
  - `first_line_start_exact_tag_marker_offset`
  - `first_line_start_exact_tag_offset`
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
- no raw marker refinement in this milestone
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes
- no general “operator wrapper class” ranking for angle/paren/brace families

## Context

`M8.5.23` introduced wrapper exact-tag preference, `M8.5.24` refined raw markers, and `M8.5.25` refined wrapper markers such as `[query]: text` and `[query] - text`.

The next remaining rough edge is now inside the broader exact-tag wrapper family. Today `[error] text`, `(error) text`, `{error} text`, and `<error> text` are effectively peers once stronger signals tie. In terminal and log output, square-bracket labels are the most common explicit tag form and are usually more operator-meaningful than the other supported wrapper pairs.

The next step should stay backend-only and add one more deterministic signal family rather than redefining the broader search contract.

## Approaches Considered

### 1. Square-bracket-only exact-tag tie-break

Add a narrow signal that rewards only square-bracket exact-tag hits.

Pros:

- smallest implementation delta
- directly matches the most common log-tag shape
- easy to regression test

Cons:

- explicitly introduces wrapper-pair priority

### 2. Operator-wrapper class ranking

Promote `[ ]` and `< >` together over `( )` and `{ }`.

Pros:

- broader than approach 1

Cons:

- harder to justify
- subjective grouping
- wider regression surface than needed

### 3. Full wrapper-pair weighting model

Add a general ranking map across all wrapper pairs.

Pros:

- most expressive

Cons:

- too wide for the next additive milestone
- likely to require follow-up tuning

## Recommended Approach

Use approach 1: a narrow square-bracket exact-tag tie-break.

This is the smallest change that nudges the wrapper family in a more operator-friendly direction while keeping the rule explainable and easy to regression test. It also avoids expanding into a broader wrapper taxonomy.

## Square-Bracket Model

### Square-Bracket Rule

A match counts as a square-bracket exact-tag hit when:

- it already satisfies the current line-start exact-tag rule
- the opening wrapper character is `[`
- the closing wrapper character is `]`

The search match itself remains case-insensitive because the existing search offsets are already case-insensitive. Wrapper matching remains exact.

### Examples

- count as square-bracket exact-tag hits:
  - `[error] failed to attach`
  - `[error]: failed to attach`
  - `[error] - failed to attach`
- do not count as square-bracket exact-tag hits:
  - `(error) failed to attach`
  - `{error} failed to attach`
  - `<error> failed to attach`
  - `[error]failed to attach`

### Relative Strength

The new square-bracket signal is additive inside the existing wrapper exact-tag family. It does not change the broader raw-marker-versus-wrapper hierarchy.

Examples under `sort="relevance"`:

- `error: failed` still outranks `[error] failed`
- `[error]: failed` outranks `(error): failed`
- `(error) failed` still outranks tighter `(error)failed` because the existing exact-tag chain remains in place

### Match Set Stability

The new rule does not change which snapshots match the query.

Examples:

- searching `error` still returns `[error] failed`, `(error) failed`, and `<error> failed`
- under `sort="relevance"`, square-bracket exact-tag results simply rank ahead of other wrapper exact-tag results when broader strength is otherwise similar

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `line_start_log_marker_match_count` descending
3. `line_start_delimited_log_marker_match_count` descending
4. `line_start_exact_tag_marker_match_count` descending
5. `line_start_exact_tag_match_count` descending
6. `line_start_square_bracket_exact_tag_match_count` descending
7. `line_start_punctuation_wrap_match_count` descending
8. `line_start_whole_word_match_count` descending
9. `conditional_non_line_start_whole_word_match_count` ascending
10. `whole_word_match_count` descending
11. `first_line_start_log_marker_offset` ascending
12. `first_line_start_delimited_log_marker_offset` ascending
13. `first_line_start_exact_tag_marker_offset` ascending
14. `first_line_start_exact_tag_offset` ascending
15. `first_line_start_square_bracket_exact_tag_offset` ascending
16. `first_line_start_punctuation_wrap_offset` ascending
17. `first_line_start_whole_word_offset` ascending
18. `first_whole_word_offset` ascending
19. `cluster_span` ascending
20. `first_match_offset` ascending
21. `match_density` descending
22. `snapshot_at` descending
23. `session_id` ascending

### Metric Semantics

- `line_start_square_bracket_exact_tag_match_count`
  - number of line-start exact-tag hits whose wrapper pair is exactly `[ ]`
- `first_line_start_square_bracket_exact_tag_offset`
  - earliest query offset among square-bracket exact-tag hits
  - when no such hit exists, use a stable sentinel so ordering falls back cleanly

All other metric semantics remain identical to `M8.5.25`.

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the two new square-bracket fields. Reuse the already-computed match offsets, the current exact-tag helper, and one new local helper that checks the wrapper pair.

Do not change whole-word, line-start whole-word, raw log-marker, delimited raw-marker, wrapper, exact-tag, or exact-tag-marker detection semantics in this milestone. The new helper should be strictly additive.

Use a stable sentinel for `first_line_start_square_bracket_exact_tag_offset` when no such hit exists, so the order naturally falls back to the existing `M8.5.25` chain.

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

- square-bracket exact-tag hits such as `[query] text` outrank other wrapper exact-tag hits such as `(query) text`
- when square-bracket exact-tag counts tie, earlier `first_line_start_square_bracket_exact_tag_offset` wins
- when no square-bracket exact-tag hit exists, ordering falls back to the existing `M8.5.25` chain
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

