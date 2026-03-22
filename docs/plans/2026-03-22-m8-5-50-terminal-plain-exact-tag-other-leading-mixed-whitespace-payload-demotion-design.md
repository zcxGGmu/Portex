# M8.5.50 Terminal Plain Exact-Tag Other-Leading Mixed-Whitespace Payload Demotion Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already tie on stronger signals and other-leading-whitespace payload presence prefer fewer other-leading mixed-whitespace payload separators, while preserving existing marker/wrapper priorities and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal conditional count signal:
  - `conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count`
- preserve existing `M8.5.49` signals and ordering semantics outside the new tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer/parser/full-text index work
- no broader whitespace scoring model

## Context

`M8.5.49` already adds residual other-leading-whitespace payload earliest-offset tie-break. A narrow gap remains inside that residual family: we still do not distinguish cleaner `other-leading + payload` forms (for example `\vbb`) from noisier `other-leading + extra whitespace + payload` forms (for example `\v\tbb` or `\f bb`) when stronger signals tie.

The smallest safe follow-up is a conditional count that only activates when a snapshot already proves it has at least one clean single-space plain exact-tag hit, matching the existing `M8.5.39+` activation guard.

## Approaches Considered

### 1. Conditional other-leading mixed-whitespace payload count (recommended)

Add a conditional count for plain exact-tag hits whose first separator is other-leading whitespace and whose second separator character is also whitespace.

Pros:

- minimal delta on top of `M8.5.49`
- keeps the rule explainable and narrow
- leaves no-single-space paths neutral

Cons:

- adds one more derived candidate field

### 2. Other-leading mixed-whitespace payload offset tie-break

Track earliest other-leading mixed-whitespace payload offset instead of count.

Pros:

- consistent with count-then-offset sequencing

Cons:

- weaker than count for this cleanliness distinction
- broader follow-up can add offset later if needed

### 3. Broader residual family token scoring

Introduce a unified score for all remaining separator cleanliness signals.

Pros:

- can absorb more edge cases

Cons:

- broader than current milestone boundary
- harder to regression-test and explain

## Recommended Approach

Use approach 1: add a conditional other-leading mixed-whitespace payload count tie-break.

## Other-Leading Mixed-Whitespace Payload Rule

A line-start plain exact-tag hit is counted by the new signal when:

- it matches `_is_line_start_plain_exact_tag_other_leading_whitespace_payload_match(...)`
- the second separator character after the closing wrapper exists and is whitespace
- payload still exists before newline/end (already guaranteed by the reused base predicate)

Examples counted by the new signal:

- `[error]\v\tbb`
- `[error]\f bb`
- `[error]\v\fbb`

Examples not counted:

- `[error]\vbb`
- `[error]\fbb`
- `[error] bb`
- `[error]\tbb`
- `[error] \tbb`
- `[error]: bb`
- `[error] - bb`

The new conditional signal:

- `conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count`

Computation:

- if `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use the other-leading mixed-whitespace payload count
- otherwise force `0` to keep fallback neutral

## Relevance Model Update

For `sort="relevance"`, keep existing keys and insert:

1. `conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count` (fewer is better)

Placement:

- after `conditional_first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset`
- before `conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset`

This preserves the `M8.5.39` -> `M8.5.49` chain and only resolves this additional narrow residual-family cleanliness gap.

## Backend Design

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count`
- add helpers:
  - `_is_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match(...)`
  - `_count_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_hits(...)`
- compute and wire the conditional count in `_build_search_candidate(...)`
- update the `relevance` tuple with the new key at the placement above

No route, schema, or persistence contract change is required.

## Testing Strategy

Focused service TDD in `tests/services/test_terminal_sessions.py`:

- when stronger signals tie, snapshots with fewer other-leading mixed-whitespace payload separators rank ahead
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.49` behavior
- pagination still slices globally ordered results after the new tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route/API suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, web lint/build, `git diff --check`)

## Risks And Mitigations

- Risk: accidentally counting plain other-leading payload hits without extra whitespace.
  - Mitigation: the new helper reuses the existing other-leading payload predicate, then requires a second separator character that is whitespace.
- Risk: changing no-single-space paths.
  - Mitigation: keep the signal conditional on the existing single-space guard and assert fallback behavior in tests.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
