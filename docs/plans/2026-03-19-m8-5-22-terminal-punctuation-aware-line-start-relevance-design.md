# M8.5.22 Terminal Punctuation-Aware Line-Start Relevance Design

## Goal

Improve the default `relevance` ordering for `/terminals` history search so narrow line-start punctuation-wrapped markers such as `[query]` and `(query)` outrank plain line-start whole-word hits, while preserving the stronger `M8.5.21` preference for line-start `query:` and strict `query -` markers. Keep the current search API, UI surface, RBAC, pagination model, and history compatibility boundaries unchanged.

## Scope

- refine the backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep the existing match set unchanged:
  - substring matches still remain searchable and returnable
  - whole-word detection still remains ordering-only
  - line-start detection still remains ordering-only
  - the new punctuation-aware signal only improves ordering among already matched snapshots
- add two lightweight ranking signals derived from already available search data:
  - `line_start_punctuation_wrap_match_count`
  - `first_line_start_punctuation_wrap_offset`
- preserve the existing `M8.5.21` relevance signals after the new punctuation-aware signals:
  - `line_start_log_marker_match_count`
  - `line_start_whole_word_match_count`
  - `conditional_non_line_start_whole_word_match_count`
  - `whole_word_match_count`
  - `first_line_start_log_marker_offset`
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
- no generic punctuation scoring model
- no tokenizer, full-text index, or syntax parser
- no snippet-generation or deep-link changes
- no frontend control changes
- no changes to `latest.json`, archived snapshots, or `GET /terminals/{group_id}/sessions/current/history`
- no RBAC or workspace-access changes
- no attempt to normalize arbitrary nested punctuation or multi-character wrappers

## Context

`M8.5.19` made line-start whole-word hits outrank later-in-line hits. `M8.5.20` made cleaner line-start results outrank noisier ones. `M8.5.21` then made line-start `query:` and strict `query -` markers outrank plain line-start hits.

The next remaining rough edge is that many terminal logs also use lightweight punctuation wrappers at line start, such as `[ERROR]`, `(warn)`, or `<info>`. These are often more operator-meaningful than a plain line-start word, but today they fall back to ordinary whole-word and line-start signals because the current marker rule intentionally excludes `[query]` and broader punctuation heuristics.

The next step should stay backend-only and add one more small deterministic signal family rather than redefining the broader search contract.

## Approaches Considered

### 1. General punctuation bonus

Promote any line-start hit followed or surrounded by punctuation.

Pros:

- broad coverage
- small code surface

Cons:

- semantics are too blurry
- likely to over-promote ordinary prose
- harder to defend in regressions

### 2. Narrow punctuation-wrapper ranking tuple

Add a dedicated signal for a small set of matching single-character wrappers at line start, then fall back to the existing `M8.5.21` signals.

Pros:

- directly covers the explicit `[query]` gap left by `M8.5.21`
- stays deterministic and easy to regression test
- avoids changing existing whole-word and log-marker semantics

Cons:

- requires a few more focused service tests than approach 1

### 3. Full marker grammar

Introduce a more complete parser for log-level prefixes and bracketed tags.

Pros:

- more expressive

Cons:

- too large for the next additive milestone
- unnecessary complexity for a backend-only ranking tweak

## Recommended Approach

Use approach 2: a narrow punctuation-wrapper ranking tuple for default `relevance`.

This is the smallest change that covers the explicit bracketed-tag gap left by `M8.5.21` while keeping the ranking rules explainable and testable. It also preserves the stronger priority of the existing `query:` and strict `query -` marker shapes.

## Punctuation-Aware Model

### Wrapper Rule

A match counts as a line-start punctuation-wrapper hit when:

- it already satisfies the current whole-word rule
- the query is immediately preceded by one opening punctuation character
- that opening punctuation itself is at the start of the transcript or immediately after `\n`
- the character immediately after the query is the matching closing punctuation

Supported matching wrapper pairs in this milestone:

- `[` + `]`
- `(` + `)`
- `{` + `}`
- `<` + `>`

The search match itself remains case-insensitive because the existing search offsets are already case-insensitive. Punctuation matching remains exact.

### Examples

- count as punctuation-wrapper hits:
  - `[error] failed to attach`
  - `(error) failed to attach`
  - `<error> detached`
  - `{error} detached`
- do not count as punctuation-wrapper hits:
  - `prefix [error] failed`
  - `[[error]] failed`
  - `[error failed`
  - `error] failed`
  - `"error" failed`

### Relative Strength

The new punctuation-wrapper signal is additive but weaker than the existing `M8.5.21` line-start log-marker signal.

Examples under `sort="relevance"`:

- `error: failed` still outranks `[error] failed`
- `[error] failed` outranks `error failed`
- plain substring-only matches still remain searchable, but rank below these stronger line-start forms

### Match Set Stability

The new rule does not change which snapshots match the query.

Examples:

- searching `error` still returns `[error] failed`, `error: failed`, and `plain error failed`
- under `sort="relevance"`, punctuation-wrapped line-start results simply rank ahead of plain line-start results when broader strength is otherwise similar

## Relevance Model

### Ranking Tuple

For `sort="relevance"`, order matches by:

1. `match_count` descending
2. `line_start_log_marker_match_count` descending
3. `line_start_punctuation_wrap_match_count` descending
4. `line_start_whole_word_match_count` descending
5. `conditional_non_line_start_whole_word_match_count` ascending
6. `whole_word_match_count` descending
7. `first_line_start_log_marker_offset` ascending
8. `first_line_start_punctuation_wrap_offset` ascending
9. `first_line_start_whole_word_offset` ascending
10. `first_whole_word_offset` ascending
11. `cluster_span` ascending
12. `first_match_offset` ascending
13. `match_density` descending
14. `snapshot_at` descending
15. `session_id` ascending

### Metric Semantics

- `line_start_log_marker_match_count`
  - number of line-start whole-word hits immediately followed by `:` or strict ` -`
- `line_start_punctuation_wrap_match_count`
  - number of whole-word hits wrapped by one supported punctuation pair whose opening punctuation is itself at transcript start or immediately after `\n`
- `first_line_start_punctuation_wrap_offset`
  - earliest query offset among punctuation-wrapper hits
  - when no such hit exists, use a stable sentinel so ordering falls back cleanly

All other metric semantics remain identical to `M8.5.21`.

## Backend Design

### Service

Keep `search_history_by_group(...)` and `_search_history_snapshots(...)` as the main entry points. Only the internal `relevance` candidate-building and sorting logic changes.

Extend the internal search candidate metadata in `services/terminal_sessions.py` with the two new punctuation-wrapper fields. Reuse the already-computed match offsets and the current whole-word helper; no new DTO, route field, or extra search pass is needed.

Use a local helper that inspects an already-matched offset and checks for one of the supported line-start wrapper pairs. This helper should not replace the existing whole-word, line-start whole-word, or line-start log-marker helpers; it should only add one more narrow signal family.

Use a stable sentinel for `first_line_start_punctuation_wrap_offset` when no wrapper hit exists, so the order naturally falls back to the existing `M8.5.21` chain.

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

- line-start `query:` and strict `query -` marker results still outrank punctuation-wrapper results
- punctuation-wrapper results such as `[query]` outrank plain line-start whole-word results
- when punctuation-wrapper counts tie, earlier `first_line_start_punctuation_wrap_offset` wins
- when no punctuation-wrapper hit exists, ordering falls back to the existing `M8.5.21` signals
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
