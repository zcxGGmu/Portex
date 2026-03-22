# M8.5.51 Terminal Plain Exact-Tag Other-Leading Mixed-Whitespace Payload Offset Tie-Break Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already tie on stronger signals and `M8.5.50` other-leading mixed-whitespace payload count prefer those separators appearing later in output, while preserving existing marker/wrapper priorities and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal conditional offset signal:
  - `conditional_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset`
- preserve existing `M8.5.50` signals and ordering semantics outside the new tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer/parser/full-text index work
- no broader whitespace scoring model

## Context

`M8.5.50` already adds a conditional count demotion for other-leading mixed-whitespace payload separators (for example `\v\tbb`, `\f bb`, `\v\fbb`). A narrow residual gap remains when that count ties: ordering still falls through to the broader `M8.5.49` other-leading-whitespace offset key instead of preferring later offsets within the mixed-whitespace sub-family first.

The smallest safe follow-up is a conditional earliest mixed-whitespace payload offset tie-break that activates under the existing single-space plain exact-tag guard.

## Approaches Considered

### 1. Conditional earliest mixed-whitespace payload offset (recommended)

Add `conditional_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset` and sort by later offset first.

Pros:

- minimal delta on top of `M8.5.50`
- preserves existing count-first then offset pattern used in prior refinements
- keeps no-single-space paths neutral

Cons:

- adds one more derived candidate field

### 2. Reuse only existing broader other-leading offset

Do not add a mixed-family offset tie-break and continue using `M8.5.49` broad residual-family offset.

Pros:

- zero code changes

Cons:

- mixed-family ties remain unresolved at their own granularity
- weaker explainability for the `M8.5.50` family-specific chain

### 3. Broader residual-family rescore

Introduce a unified weighted model for all remaining payload separator families.

Pros:

- could cover more edge cases

Cons:

- broader than the current milestone boundary
- harder to regression-test and reason about

## Recommended Approach

Use approach 1: add one conditional other-leading mixed-whitespace payload earliest-offset tie-break and prefer later offsets.

## Other-Leading Mixed-Whitespace Payload Offset Rule

Reuse the existing `M8.5.50` mixed-family predicate:

- line-start exact-tag hit
- non-marker exact-tag hit
- belongs to the residual other-leading-whitespace payload family
- second separator character exists and is whitespace
- payload still exists before newline/end

New conditional signal:

- `conditional_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset`

Computation:

- if `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use earliest mixed-family offset
- otherwise force sentinel to keep fallback neutral in the no-single-space path

Ordering direction:

- later mixed-family offset is better (descending by offset)

## Relevance Model Update

For `sort="relevance"`, keep existing keys and insert:

1. `conditional_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset` (later is better)

Placement:

- after `conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count`
- before `conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset`

This preserves the current `M8.5.39` -> `M8.5.50` chain and only resolves the remaining tie-break gap inside the mixed-family branch.

## Backend Design

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset`
- add helper:
  - `_first_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_offset(...)`
- reuse the existing mixed-family predicate for detection
- compute and wire the conditional offset in `_build_search_candidate(...)`
- update the `relevance` tuple with the new key at the placement above

No route, schema, or persistence contract change is required.

## Testing Strategy

Focused service TDD in `tests/services/test_terminal_sessions.py`:

- when stronger signals tie and mixed-family count ties, later mixed-family separator offset outranks earlier offset
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.50` behavior
- pagination still slices globally ordered results after the new tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route/API suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, web lint/build, `git diff --check`)

## Risks And Mitigations

- Risk: accidental behavior change in no-single-space paths.
  - Mitigation: keep the new offset conditional on the existing single-space guard and assert fallback behavior in tests.
- Risk: wrong offset direction in ranking.
  - Mitigation: add explicit test where only mixed-family earliest offset differs and expected winner is the later one.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
