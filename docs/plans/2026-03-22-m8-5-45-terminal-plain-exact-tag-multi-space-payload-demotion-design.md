# M8.5.45 Terminal Plain Exact-Tag Multi-Space Payload Demotion Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already contain clean single-space plain exact-tag hits prefer fewer multi-space payload-bearing plain exact-tag separators, while preserving existing marker/wrapper priorities and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal conditional count signal:
  - `conditional_line_start_plain_exact_tag_multi_space_payload_match_count`
- preserve existing `M8.5.44` signals and ordering semantics outside the new tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer/parser/full-text index work
- no broader whitespace scoring model

## Context

`M8.5.39` through `M8.5.44` already establish a narrow cleanliness chain for plain exact-tag snapshots:

- single-space payload is preferred
- non-single-space noise appearing later is preferred
- payloadless separators are demoted by count, then by offset
- tab-prefixed payload separators are demoted by count, then by offset

A smaller gap still remains when stronger signals tie and payloadful non-single-space separators differ only by family. In that case snapshots such as `[error]  bb` and `[error]\tbb` are no longer peers because `M8.5.43`/`M8.5.44` already isolate the tab family, but multi-space payload forms still have no family-specific demotion and only inherit the broader non-single-space noise signal.

The smallest safe follow-up is a conditional count that only activates once a snapshot already proves it has at least one clean single-space plain exact-tag hit.

## Approaches Considered

### 1. Conditional multi-space payload count (recommended)

Add a conditional count for plain exact-tag hits whose separator starts with multiple ASCII spaces and still carries payload text.

Pros:

- minimal delta on top of `M8.5.44`
- keeps the rule explainable and narrow
- leaves no-single-space paths neutral

Cons:

- adds one more derived candidate field

### 2. Multi-space payload offset tie-break

Track earliest multi-space payload offset instead of count.

Pros:

- aligns with existing offset-based refinements

Cons:

- weaker when multiple multi-space payload separators exist

### 3. Broader space-prefixed payload scoring

Explicitly weight multiple space-prefixed payload forms together.

Pros:

- can model more cases

Cons:

- broader than the current milestone boundary
- harder to regression-test and explain

## Recommended Approach

Use approach 1: add a conditional multi-space payload count tie-break.

## Multi-Space Payload Rule

A line-start plain exact-tag hit is counted by the new signal when:

- it is a non-marker exact-tag hit
- it is not a single-space plain exact-tag hit
- it is not payloadless
- the first separator character after the closing wrapper is ASCII space
- the second separator position is still whitespace
- before newline/end-of-output there is at least one non-whitespace payload character

Examples counted by the new signal:

- `[error]  bb`
- `[error]   bb`
- `[error]    bb`

Examples not counted:

- `[error] bb`
- `[error]\tbb`
- `[error]\t  `
- `[error]: bb`
- `[error] - bb`

The new conditional signal:

- `conditional_line_start_plain_exact_tag_multi_space_payload_match_count`

Computation:

- if `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use the multi-space payload count
- otherwise force `0` to keep fallback neutral

## Relevance Model Update

For `sort="relevance"`, keep existing keys and insert:

1. `conditional_line_start_plain_exact_tag_multi_space_payload_match_count` (fewer is better)

Placement:

- after `conditional_first_line_start_plain_exact_tag_tab_prefixed_payload_offset`
- before `conditional_non_exact_tag_punctuation_wrap_match_count`

This preserves the `M8.5.39` -> `M8.5.40` -> `M8.5.41` -> `M8.5.42` -> `M8.5.43` -> `M8.5.44` chain and only resolves this additional narrow family-level cleanliness gap.

## Backend Design

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_line_start_plain_exact_tag_multi_space_payload_match_count`
- add helpers:
  - `_is_line_start_plain_exact_tag_multi_space_payload_match(...)`
  - `_count_line_start_plain_exact_tag_multi_space_payload_hits(...)`
- compute and wire the conditional multi-space payload count in `_build_search_candidate(...)`
- update the `relevance` tuple with the new key at the placement above

No route, schema, or persistence contract change is required.

## Testing Strategy

Focused service TDD in `tests/services/test_terminal_sessions.py`:

- when stronger signals tie, snapshots with fewer multi-space payload plain exact-tag separators rank ahead
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.44` behavior
- pagination still slices globally ordered results after the new tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route/API suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, web lint/build, `git diff --check`)

## Risks And Mitigations

- Risk: accidentally counting single-space or tab-prefixed payload forms as multi-space payload.
  - Mitigation: explicitly exclude existing single-space and tab-prefixed predicates, and require the second separator position to remain whitespace.
- Risk: changing no-single-space paths.
  - Mitigation: keep the signal conditional on the existing single-space guard and assert fallback behavior in tests.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
