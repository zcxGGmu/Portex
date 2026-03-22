# M8.5.46 Terminal Plain Exact-Tag Multi-Space Payload Offset Tie-Break Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already tie on stronger signals and multi-space payload count prefer multi-space payload separators appearing later in output, while preserving existing marker/wrapper priorities and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal conditional offset signal:
  - `conditional_first_line_start_plain_exact_tag_multi_space_payload_offset`
- preserve existing `M8.5.45` signals and ordering semantics outside the new tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer/parser/full-text index work
- no broader whitespace scoring model

## Context

`M8.5.45` added conditional multi-space payload count demotion. A narrow gap remains: when multi-space payload counts tie, results can still be decided by weaker downstream signals, even if one snapshot delays those multi-space payload separators and keeps earlier regions cleaner.

A minimal follow-up is to keep the `M8.5.45` count tie-break, then add a conditional earliest multi-space payload offset tie-break where later is better.

## Approaches Considered

### 1. Conditional earliest multi-space payload offset (recommended)

Add `conditional_first_line_start_plain_exact_tag_multi_space_payload_offset` and sort by later offset first.

Pros:

- minimal delta on top of `M8.5.45`
- independent tie-break when multi-space payload counts are equal
- neutral when no single-space plain exact-tag exists

Cons:

- adds one more derived candidate field

### 2. Multi-space payload last-offset tie-break

Track last multi-space payload offset instead of earliest.

Pros:

- directly emphasizes tail cleanliness

Cons:

- less aligned with the existing earliest-offset pattern in this ranking chain

### 3. Broader space-prefixed payload scoring

Compute a broader score across multiple space-prefixed payload families.

Pros:

- can model more payloadful separator cases

Cons:

- broader than current milestone scope
- harder to keep explainable and regression-safe

## Recommended Approach

Use approach 1: add one conditional earliest multi-space payload offset tie-break and prefer later offsets.

## Multi-Space Payload Offset Rule

Reuse `M8.5.45` multi-space payload predicate:

- line-start exact-tag hit
- non-marker exact-tag hit
- not single-space
- not payloadless
- not tab-prefixed payload
- first two separator positions after the closing wrapper are ASCII spaces
- at least one non-whitespace payload character appears before newline/end

New conditional signal:

- `conditional_first_line_start_plain_exact_tag_multi_space_payload_offset`

Computation:

- if `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use earliest multi-space payload offset
- otherwise force sentinel to keep fallback neutral in the no-single-space path

Ordering direction:

- later multi-space payload offset is better (descending by offset)

## Relevance Model Update

For `sort="relevance"`, keep existing keys and insert:

1. `conditional_first_line_start_plain_exact_tag_multi_space_payload_offset` (later is better)

Placement:

- after `conditional_line_start_plain_exact_tag_multi_space_payload_match_count`
- before `conditional_non_exact_tag_punctuation_wrap_match_count`

This preserves the `M8.5.39` -> `M8.5.40` -> `M8.5.41` -> `M8.5.42` -> `M8.5.43` -> `M8.5.44` -> `M8.5.45` chain and only resolves this additional tie-break gap.

## Backend Design

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_first_line_start_plain_exact_tag_multi_space_payload_offset`
- add multi-space payload offset helper:
  - `_first_line_start_plain_exact_tag_multi_space_payload_offset(...)`
- compute and wire the conditional multi-space payload offset in `_build_search_candidate(...)`
- update `relevance` tuple with the new key at the placement above

No route, schema, or persistence contract change is required.

## Testing Strategy

Focused service TDD in `tests/services/test_terminal_sessions.py`:

- when stronger signals and multi-space payload count tie, later multi-space payload separator offset outranks earlier multi-space payload separator offset
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.45` behavior
- pagination still slices globally ordered results after the new tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route/API suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, web lint/build, `git diff --check`)

## Risks And Mitigations

- Risk: changing ordering in no-single-space paths.
  - Mitigation: keep the new signal conditional on the existing single-space guard and assert fallback behavior in tests.
- Risk: misranking multi-space payload ties due to wrong direction.
  - Mitigation: add an explicit test where only earliest multi-space payload offset differs and the expected winner is the snapshot whose multi-space payload appears later.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
