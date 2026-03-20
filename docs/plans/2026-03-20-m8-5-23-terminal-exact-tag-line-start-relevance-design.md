# M8.5.23 Terminal Exact-Tag Line-Start Relevance Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so delimiter-aware line-start exact-tag wrapper hits such as `[query] text`, `[query]: text`, and `[query] - text` outrank tighter non-delimited wrapper hits such as `[query]text`, while preserving the stronger `M8.5.21` priority for raw line-start `query:` and strict `query -` markers. Keep the current search API, UI surface, RBAC, pagination model, and history compatibility boundaries unchanged.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep the existing match set unchanged:
  - substring matches still remain searchable and returnable
  - whole-word detection still remains ordering-only
  - line-start detection still remains ordering-only
  - punctuation-wrapper detection still remains ordering-only
  - the new exact-tag signal only improves ordering among already matched snapshots
- add two lightweight ranking signals derived from already available search data:
  - `line_start_exact_tag_match_count`
  - `first_line_start_exact_tag_offset`
- preserve the existing `M8.5.22` relevance signals after the new exact-tag signals:
  - `line_start_log_marker_match_count`
  - `line_start_punctuation_wrap_match_count`
  - `line_start_whole_word_match_count`
  - `conditional_non_line_start_whole_word_match_count`
  - `whole_word_match_count`
  - `first_line_start_log_marker_offset`
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
- no raw `query:` versus `query:text` delimiter refinement in this milestone
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes

## Context

`M8.5.21` made raw line-start `query:` and strict `query -` markers outrank plain line-start hits. `M8.5.22` then made narrow line-start wrapper hits such as `[query]` outrank plain line-start whole-word hits.

The next remaining rough edge is that `M8.5.22` treats delimiter-aware exact tags such as `[error] failed` and tighter non-delimited wrapper forms such as `[error]failed` as equally strong wrapper hits. In operator-facing logs, the separated tag token is usually more meaningful than the visually similar but tighter inline form.

The next step should stay backend-only and add one more deterministic signal family on top of the existing wrapper logic rather than redefining the broader search contract.

## Approaches Considered

### 1. Wrapper-whitespace-only tie-break

Only promote wrapper hits followed by whitespace.

Pros:

- very small implementation
- easy to reason about

Cons:

- misses common `[query]: ...` and `[query] - ...` tag shapes
- too narrow for the next standalone milestone

### 2. Small exact-tag wrapper ranking tuple

Add `line_start_exact_tag_match_count` plus `first_line_start_exact_tag_offset`, derived only from existing line-start punctuation-wrapper hits whose closing wrapper is followed by a narrow delimiter set.

Pros:

- directly covers the `M8.5.22` gap without changing the search surface
- stays deterministic and easy to regression test
- preserves the stronger `M8.5.21` raw marker priority

Cons:

- requires one more focused helper and test block

### 3. Broad delimiter-aware ranking across raw and wrapped markers

Promote any line-start marker-like hit whose trailing characters look like a delimiter boundary.

Pros:

- broader coverage

Cons:

- semantics become blurrier
- more likely to need follow-up tuning
- too wide for the next additive backend-only milestone

## Recommended Approach

Use approach 2: a small exact-tag wrapper ranking tuple for default `relevance`.

This is the smallest change that closes the explicit `M8.5.22` gap while keeping the ranking rules explainable and regression-friendly. It also preserves the stronger priority of the existing raw `query:` / strict `query -` marker family.

## Exact-Tag Model

### Exact-Tag Rule

A match counts as a line-start exact-tag hit when:

- it already satisfies the current line-start punctuation-wrapper rule
- and the text immediately after the closing wrapper is one of:
  - end of output
  - any whitespace character
  - `:` followed by end-of-output or whitespace
  - strict ` -` followed by end-of-output or whitespace

The search match itself remains case-insensitive because the existing search offsets are already case-insensitive. Delimiter matching remains exact.

### Examples

- count as exact-tag hits:
  - `[error] failed to attach`
  - `[error]: failed to attach`
  - `[error] - failed to attach`
  - `<error>\nnext line`
- do not count as exact-tag hits:
  - `[error]failed to attach`
  - `[error]:failed to attach`
  - `[error]- failed to attach`
  - `prefix [error] failed`

### Relative Strength

The new exact-tag signal is additive but weaker than the existing `M8.5.21` raw line-start log-marker signal.

Examples under `sort="relevance"`:

- `error: failed` still outranks `[error] failed`
- `[error] failed` outranks `[error]failed`
- `[error]failed` still outranks plain `error failed` because `M8.5.22` wrapper priority remains in place

### Match Set Stability

The new rule does not change which snapshots match the query.

Examples:

- searching `error` still returns `error: failed`, `[error] failed`, `[error]failed`, and `plain error failed`
- under `sort="relevance"`, delimiter-aware exact-tag wrapper results simply rank ahead of tighter non-delimited wrapper results when broader strength is otherwise similar

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `line_start_log_marker_match_count` descending
3. `line_start_exact_tag_match_count` descending
4. `line_start_punctuation_wrap_match_count` descending
5. `line_start_whole_word_match_count` descending
6. `conditional_non_line_start_whole_word_match_count` ascending
7. `whole_word_match_count` descending
8. `first_line_start_log_marker_offset` ascending
9. `first_line_start_exact_tag_offset` ascending
10. `first_line_start_punctuation_wrap_offset` ascending
11. `first_line_start_whole_word_offset` ascending
12. `first_whole_word_offset` ascending
13. `cluster_span` ascending
14. `first_match_offset` ascending
15. `match_density` descending
16. `snapshot_at` descending
17. `session_id` ascending

### Metric Semantics

- `line_start_exact_tag_match_count`
  - number of line-start punctuation-wrapper hits whose closing wrapper is immediately followed by end-of-output, whitespace, `:`, or strict ` -`
- `first_line_start_exact_tag_offset`
  - earliest query offset among exact-tag hits
  - when no such hit exists, use a stable sentinel so ordering falls back cleanly

All other metric semantics remain identical to `M8.5.22`.

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the two new exact-tag fields. Reuse the already-computed match offsets, the current wrapper helper, and one new local helper that inspects the character(s) immediately after the closing wrapper.

Do not change whole-word, line-start whole-word, raw log-marker, or punctuation-wrapper detection semantics in this milestone. The new helper should be strictly additive.

Use a stable sentinel for `first_line_start_exact_tag_offset` when no exact-tag hit exists, so the order naturally falls back to the existing `M8.5.22` chain.

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

- delimiter-aware exact-tag wrapper hits outrank tighter non-delimited wrapper hits
- when exact-tag counts tie, earlier `first_line_start_exact_tag_offset` wins
- when no exact-tag hit exists, ordering falls back to the existing `M8.5.22` punctuation-wrapper signals
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
