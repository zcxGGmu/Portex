# M8.5.43 Terminal Plain Exact-Tag Tab-Prefixed Payload Demotion Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already contain clean single-space plain exact-tag hits prefer fewer tab-prefixed payload-bearing plain exact-tag separators, while preserving existing marker/wrapper priorities and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal conditional count signal:
  - `conditional_line_start_plain_exact_tag_tab_prefixed_payload_match_count`
- preserve existing `M8.5.42` signals and ordering semantics outside the new tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer/parser/full-text index work
- no broader whitespace scoring model

## Context

`M8.5.39` through `M8.5.42` already establish a narrow cleanliness chain for plain exact-tag snapshots:

- single-space payload is preferred
- non-single-space noise appearing later is preferred
- payloadless separators are demoted by count, then by offset

A smaller gap still remains when stronger signals, non-single-space noise offset, payloadless count, and payloadless offset all tie. In that case snapshots such as `[error]  ok` and `[error]\tok` still fall through to weaker downstream signals, even though tab-prefixed payload-bearing separators are usually less readable than space-prefixed payload-bearing separators.

The smallest safe follow-up is a conditional count that only activates once a snapshot already proves it has at least one clean single-space plain exact-tag hit.

## Approaches Considered

### 1. Conditional tab-prefixed payload count (recommended)

Add a conditional count for plain exact-tag hits whose separator starts with a tab and still carries payload text.

Pros:

- minimal delta on top of `M8.5.42`
- keeps the rule explainable and narrow
- leaves no-single-space paths neutral

Cons:

- adds one more derived candidate field

### 2. Tab-prefixed payload offset tie-break

Track earliest tab-prefixed payload offset instead of count.

Pros:

- aligns with existing offset-based refinements

Cons:

- weaker when multiple tab-prefixed payload separators exist

### 3. Broader separator-family weighting

Explicitly weight single-space, multi-space, tab, and mixed separator families.

Pros:

- can model more cases

Cons:

- broader than the current milestone boundary
- harder to regression-test and explain

## Recommended Approach

Use approach 1: add a conditional tab-prefixed payload count tie-break.

## Tab-Prefixed Payload Rule

A line-start plain exact-tag hit is counted by the new signal when:

- it is a non-marker exact-tag hit
- it is not a single-space plain exact-tag hit
- it is not payloadless
- the first separator character after the closing wrapper is `\t`
- before newline/end-of-output there is at least one non-whitespace payload character

Examples counted by the new signal:

- `[error]\tok`
- `[error]\t\tok`
- `[error]\t ok`

Examples not counted:

- `[error] ok`
- `[error]  ok`
- `[error]\t   `
- `[error]: ok`
- `[error] - ok`

The new conditional signal:

- `conditional_line_start_plain_exact_tag_tab_prefixed_payload_match_count`

Computation:

- if `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use the tab-prefixed payload count
- otherwise force `0` to keep fallback neutral

## Relevance Model Update

For `sort="relevance"`, keep existing keys and insert:

1. `conditional_line_start_plain_exact_tag_tab_prefixed_payload_match_count` (fewer is better)

Placement:

- after `conditional_first_line_start_plain_exact_tag_payloadless_separator_offset`
- before `conditional_non_exact_tag_punctuation_wrap_match_count`

This preserves the `M8.5.39` -> `M8.5.40` -> `M8.5.41` -> `M8.5.42` chain and only resolves this additional narrow cleanliness gap.

## Backend Design

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_line_start_plain_exact_tag_tab_prefixed_payload_match_count`
- add helpers:
  - `_is_line_start_plain_exact_tag_tab_prefixed_payload_match(...)`
  - `_count_line_start_plain_exact_tag_tab_prefixed_payload_hits(...)`
- compute and wire the conditional tab-prefixed payload count in `_build_search_candidate(...)`
- update the `relevance` tuple with the new key at the placement above

No route, schema, or persistence contract change is required.

## Testing Strategy

Focused service TDD in `tests/services/test_terminal_sessions.py`:

- when stronger signals tie, snapshots with fewer tab-prefixed payload plain exact-tag separators rank ahead
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.42` behavior
- pagination still slices globally ordered results after the new tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route/API suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, web lint/build, `git diff --check`)

## Risks And Mitigations

- Risk: accidentally counting payloadless tab-only separators as payload-bearing noise.
  - Mitigation: explicitly exclude the existing payloadless predicate and require a non-whitespace payload character before newline/end.
- Risk: changing no-single-space paths.
  - Mitigation: keep the signal conditional on the existing single-space guard and assert fallback behavior in tests.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
