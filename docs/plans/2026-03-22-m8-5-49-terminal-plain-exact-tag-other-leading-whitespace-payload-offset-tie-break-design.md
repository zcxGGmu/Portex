# M8.5.49 Terminal Plain Exact-Tag Other-Leading-Whitespace Payload Offset Tie-Break Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already tie on stronger signals and other-leading-whitespace payload presence prefer those separators appearing later in output, while preserving existing marker/wrapper priorities and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal conditional offset signal:
  - `conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset`
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

An initial `M8.5.49` count-based plan was explored, but root-cause investigation showed that a count signal for other-leading-whitespace payload is redundant in the current chain: the exact-tag total plus already-modeled separator families leave no meaningful room for a family-specific count tie-break to decide ordering. What remains useful is an offset tie-break when this residual family is present.

The smallest correct follow-up is therefore to keep existing signals intact and add a conditional earliest other-leading-whitespace payload offset tie-break where later is better.

## Approaches Considered

### 1. Conditional earliest other-leading-whitespace payload offset (recommended)

Add `conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset` and sort by later offset first.

Pros:

- minimal delta on top of `M8.5.48`
- actually changes ordering where the residual family is present
- neutral when no single-space plain exact-tag exists

Cons:

- adds one more derived candidate field

### 2. Keep count-based demotion

Retain the earlier count-based idea.

Pros:

- superficially consistent with previous count-first milestones

Cons:

- redundant in this ranking chain
- does not create a meaningful discriminating tie-break

### 3. Broader residual payloadful separator scoring

Merge all remaining residual payloadful separator families into one broader score.

Pros:

- can cover more cases at once

Cons:

- broader than current milestone scope
- harder to keep explainable and regression-safe

## Recommended Approach

Use approach 1: add one conditional earliest other-leading-whitespace payload offset tie-break and prefer later offsets.

## Other-Leading-Whitespace Payload Offset Rule

Reuse the residual-family predicate:

- line-start exact-tag hit
- non-marker exact-tag hit
- not single-space
- not payloadless
- not tab-prefixed payload
- not multi-space payload
- not space-prefixed mixed-whitespace payload
- first separator character after the closing wrapper is whitespace
- that first separator character is neither ASCII space nor tab
- at least one non-whitespace payload character appears before newline/end

New conditional signal:

- `conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset`

Computation:

- if `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use earliest other-leading-whitespace payload offset
- otherwise force sentinel to keep fallback neutral in the no-single-space path

Ordering direction:

- later other-leading-whitespace payload offset is better (descending by offset)

## Relevance Model Update

For `sort="relevance"`, keep existing keys and insert:

1. `conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset` (later is better)

Placement:

- after `conditional_first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset`
- before `conditional_non_exact_tag_punctuation_wrap_match_count`

This preserves the `M8.5.39` -> `M8.5.40` -> `M8.5.41` -> `M8.5.42` -> `M8.5.43` -> `M8.5.44` -> `M8.5.45` -> `M8.5.46` -> `M8.5.47` -> `M8.5.48` chain and only resolves this additional residual-family tie-break gap.

## Backend Design

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset`
- add helper:
  - `_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset(...)`
- reuse the residual-family predicate for detection
- compute and wire the conditional offset in `_build_search_candidate(...)`
- update the `relevance` tuple with the new key at the placement above

No route, schema, or persistence contract change is required.

## Testing Strategy

Focused service TDD in `tests/services/test_terminal_sessions.py`:

- when stronger signals tie, later other-leading-whitespace payload separator offset outranks earlier offset
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.48` behavior
- pagination still slices globally ordered results after the new tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route/API suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, web lint/build, `git diff --check`)

## Risks And Mitigations

- Risk: changing ordering in no-single-space paths.
  - Mitigation: keep the new signal conditional on the existing single-space guard and assert fallback behavior in tests.
- Risk: misranking residual-family ties due to wrong direction.
  - Mitigation: add an explicit test where only earliest residual-family offset differs and the expected winner is the snapshot whose other-leading-whitespace payload appears later.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
