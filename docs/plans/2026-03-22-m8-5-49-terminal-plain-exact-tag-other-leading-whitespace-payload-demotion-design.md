# M8.5.49 Terminal Plain Exact-Tag Other-Leading-Whitespace Payload Demotion Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already contain clean single-space plain exact-tag hits prefer fewer other-leading-whitespace payload plain exact-tag separators, while preserving existing marker/wrapper priorities and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal conditional count signal:
  - `conditional_line_start_plain_exact_tag_other_leading_whitespace_payload_match_count`
- preserve existing `M8.5.48` signals and ordering semantics outside the new tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer/parser/full-text index work
- no broader whitespace scoring model

## Context

`M8.5.39` through `M8.5.48` already establish a narrow cleanliness chain for plain exact-tag snapshots:

- single-space payload is preferred
- generic non-single-space noise appearing later is preferred
- payloadless separators are demoted by count, then by offset
- tab-prefixed payload separators are demoted by count, then by offset
- multi-space payload separators are demoted by count, then by offset
- space-prefixed mixed-whitespace payload separators are demoted by count, then by offset

A smaller gap still remains for residual payloadful non-single-space separators whose first separator character is whitespace but is neither ASCII space nor tab, such as form-feed or vertical-tab prefixed payload. Those results currently inherit only the broader non-single-space noise signal and have no family-specific demotion.

The smallest safe follow-up is a conditional count that only activates once a snapshot already proves it has at least one clean single-space plain exact-tag hit.

## Approaches Considered

### 1. Conditional other-leading-whitespace payload count (recommended)

Add a conditional count for plain exact-tag hits whose separator starts with a whitespace character that is neither ASCII space nor tab while still carrying payload text.

Pros:

- minimal delta on top of `M8.5.48`
- keeps the rule explainable and narrow
- leaves no-single-space paths neutral

Cons:

- adds one more derived candidate field

### 2. Other-leading-whitespace payload offset tie-break

Track earliest other-leading-whitespace payload offset instead of count.

Pros:

- aligns with existing offset-based refinements

Cons:

- weaker when multiple such separators exist

### 3. Broader residual payloadful separator scoring

Merge all remaining residual payloadful separator families into one score.

Pros:

- can cover more cases at once

Cons:

- broader than the current milestone boundary
- harder to regression-test and explain

## Recommended Approach

Use approach 1: add a conditional other-leading-whitespace payload count tie-break.

## Other-Leading-Whitespace Payload Rule

A line-start plain exact-tag hit is counted by the new signal when:

- it is a non-marker exact-tag hit
- it is not a single-space plain exact-tag hit
- it is not payloadless
- it is not tab-prefixed payload
- it is not multi-space payload
- it is not space-prefixed mixed-whitespace payload
- the first separator character after the closing wrapper is whitespace
- that first separator character is neither ASCII space nor tab
- before newline/end-of-output there is at least one non-whitespace payload character

Examples counted by the new signal:

- `[error]\fbb`
- `[error]\vbb`
- `[error]\f bb`

Examples not counted:

- `[error] bb`
- `[error]  bb`
- `[error]\tbb`
- `[error] \tbb`
- `[error]\t  `
- `[error]: bb`
- `[error] - bb`

The new conditional signal:

- `conditional_line_start_plain_exact_tag_other_leading_whitespace_payload_match_count`

Computation:

- if `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use the other-leading-whitespace payload count
- otherwise force `0` to keep fallback neutral

## Relevance Model Update

For `sort="relevance"`, keep existing keys and insert:

1. `conditional_line_start_plain_exact_tag_other_leading_whitespace_payload_match_count` (fewer is better)

Placement:

- after `conditional_first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset`
- before `conditional_non_exact_tag_punctuation_wrap_match_count`

This preserves the `M8.5.39` -> `M8.5.40` -> `M8.5.41` -> `M8.5.42` -> `M8.5.43` -> `M8.5.44` -> `M8.5.45` -> `M8.5.46` -> `M8.5.47` -> `M8.5.48` chain and only resolves this additional narrow residual-family cleanliness gap.

## Backend Design

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_line_start_plain_exact_tag_other_leading_whitespace_payload_match_count`
- add helpers:
  - `_is_line_start_plain_exact_tag_other_leading_whitespace_payload_match(...)`
  - `_count_line_start_plain_exact_tag_other_leading_whitespace_payload_hits(...)`
- compute and wire the conditional other-leading-whitespace payload count in `_build_search_candidate(...)`
- update the `relevance` tuple with the new key at the placement above

No route, schema, or persistence contract change is required.

## Testing Strategy

Focused service TDD in `tests/services/test_terminal_sessions.py`:

- when stronger signals tie, snapshots with fewer other-leading-whitespace payload plain exact-tag separators rank ahead
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.48` behavior
- pagination still slices globally ordered results after the new tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route/API suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, web lint/build, `git diff --check`)

## Risks And Mitigations

- Risk: accidentally counting already-modeled space/tab families as other-leading-whitespace payload.
  - Mitigation: explicitly exclude single-space, tab-prefixed, multi-space, and space-prefixed mixed-whitespace predicates before checking the leading whitespace class.
- Risk: changing no-single-space paths.
  - Mitigation: keep the signal conditional on the existing single-space guard and assert fallback behavior in tests.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
