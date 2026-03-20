# M8.5.24 Terminal Delimited Log-Marker Relevance Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so delimiter-bounded raw line-start log-marker hits such as `query: text` and strict `query - text` outrank tighter glued marker forms such as `query:text` and `query -text`, while preserving the existing priority of raw log markers over wrapper-based exact tags. Keep the current search API, UI surface, RBAC, pagination model, and history compatibility boundaries unchanged.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep the existing match set unchanged:
  - substring matches still remain searchable and returnable
  - whole-word detection still remains ordering-only
  - line-start detection still remains ordering-only
  - raw log-marker detection still remains ordering-only
  - exact-tag wrapper detection still remains ordering-only
  - the new delimited-marker signal only improves ordering among already matched snapshots
- add two lightweight ranking signals derived from already available search data:
  - `line_start_delimited_log_marker_match_count`
  - `first_line_start_delimited_log_marker_offset`
- preserve the existing `M8.5.23` relevance signals after the new delimited-marker signals:
  - `line_start_log_marker_match_count`
  - `line_start_exact_tag_match_count`
  - `line_start_punctuation_wrap_match_count`
  - `line_start_whole_word_match_count`
  - `conditional_non_line_start_whole_word_match_count`
  - `whole_word_match_count`
  - `first_line_start_log_marker_offset`
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
- no generic delimiter scoring model
- no wrapper-specific delimiter refinement in this milestone
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes

## Context

`M8.5.21` made raw line-start `query:` and strict `query -` markers outrank plain line-start hits. `M8.5.22` then made wrapper forms such as `[query]` outrank plain line-start hits, and `M8.5.23` refined wrapper results so delimiter-aware exact tags such as `[query] text` outrank tighter `[query]text` forms.

The next remaining rough edge is now inside the raw marker family itself. `M8.5.21` treats `error: failed` and `error:failed` as the same marker strength, and likewise `error - failed` and `error -failed`. In operator-facing logs, the separated marker token is usually more meaningful than the glued form.

The next step should stay backend-only and add one more deterministic signal family on top of the existing raw marker logic rather than redefining the broader search contract.

## Approaches Considered

### 1. Minimal colon-only refinement

Only promote `query: text` over `query:text`.

Pros:

- smallest implementation
- easy to test

Cons:

- ignores the existing strict `query -` family from `M8.5.21`
- inconsistent across the current raw marker shapes

### 2. Small delimiter-bounded raw-marker ranking tuple

Add `line_start_delimited_log_marker_match_count` plus `first_line_start_delimited_log_marker_offset`, derived only from existing raw line-start marker hits whose separator is followed by end-of-output or whitespace.

Pros:

- directly covers the remaining rough edge inside the raw marker family
- stays deterministic and easy to regression test
- preserves raw marker priority over wrapper families

Cons:

- requires one more focused helper and test block

### 3. Broad marker tokenization

Introduce a more general parser for marker tokens and trailing delimiters.

Pros:

- broader coverage

Cons:

- semantics become blurrier
- more likely to need follow-up tuning
- too wide for the next additive backend-only milestone

## Recommended Approach

Use approach 2: a small delimiter-bounded raw-marker ranking tuple for default `relevance`.

This is the smallest change that closes the explicit raw-marker gap left by `M8.5.21` while keeping the ranking rules explainable and regression-friendly. It also preserves the current ordering ladder where raw line-start markers stay above wrapper families.

## Delimited Raw-Marker Model

### Delimited Marker Rule

A match counts as a line-start delimited raw-marker hit when:

- it already satisfies the current line-start raw log-marker rule
- and the text immediately after that raw marker separator is one of:
  - end of output
  - any whitespace character

This means:

- for `query:` hits, the character after `:` must be end-of-output or whitespace
- for strict `query -` hits, the character after the `-` must be end-of-output or whitespace

The search match itself remains case-insensitive because the existing search offsets are already case-insensitive. Delimiter matching remains exact.

### Examples

- count as delimited raw-marker hits:
  - `error: failed to attach`
  - `error:\nfailed to attach`
  - `error - failed to attach`
  - `error -\nfailed to attach`
- do not count as delimited raw-marker hits:
  - `error:failed to attach`
  - `error -failed to attach`
  - `prefix error: failed`
  - `[error]: failed`

### Relative Strength

The new delimited raw-marker signal is additive inside the existing raw marker family. It does not change the broader marker-versus-wrapper hierarchy.

Examples under `sort="relevance"`:

- `error: failed` outranks `error:failed`
- `error - failed` outranks `error -failed`
- `error:failed` still outranks `[error] failed` because raw marker priority from `M8.5.21` remains in place

### Match Set Stability

The new rule does not change which snapshots match the query.

Examples:

- searching `error` still returns `error: failed`, `error:failed`, `[error] failed`, and `plain error failed`
- under `sort="relevance"`, delimiter-bounded raw marker results simply rank ahead of glued raw marker results when broader strength is otherwise similar

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `line_start_log_marker_match_count` descending
3. `line_start_delimited_log_marker_match_count` descending
4. `line_start_exact_tag_match_count` descending
5. `line_start_punctuation_wrap_match_count` descending
6. `line_start_whole_word_match_count` descending
7. `conditional_non_line_start_whole_word_match_count` ascending
8. `whole_word_match_count` descending
9. `first_line_start_log_marker_offset` ascending
10. `first_line_start_delimited_log_marker_offset` ascending
11. `first_line_start_exact_tag_offset` ascending
12. `first_line_start_punctuation_wrap_offset` ascending
13. `first_line_start_whole_word_offset` ascending
14. `first_whole_word_offset` ascending
15. `cluster_span` ascending
16. `first_match_offset` ascending
17. `match_density` descending
18. `snapshot_at` descending
19. `session_id` ascending

### Metric Semantics

- `line_start_delimited_log_marker_match_count`
  - number of line-start raw log-marker hits whose separator is followed by end-of-output or whitespace
- `first_line_start_delimited_log_marker_offset`
  - earliest query offset among delimited raw-marker hits
  - when no such hit exists, use a stable sentinel so ordering falls back cleanly

All other metric semantics remain identical to `M8.5.23`.

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the two new delimited-marker fields. Reuse the already-computed match offsets, the current raw log-marker helper, and one new local helper that inspects the character after the marker separator.

Do not change whole-word, line-start whole-word, raw log-marker, wrapper, or exact-tag detection semantics in this milestone. The new helper should be strictly additive.

Use a stable sentinel for `first_line_start_delimited_log_marker_offset` when no delimited raw-marker hit exists, so the order naturally falls back to the existing `M8.5.23` chain.

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

- delimiter-bounded raw marker hits such as `query: text` outrank glued raw marker hits such as `query:text`
- when delimited raw-marker counts tie, earlier `first_line_start_delimited_log_marker_offset` wins
- when no delimited raw-marker hit exists, ordering falls back to the existing `M8.5.23` exact-tag and wrapper signals
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

