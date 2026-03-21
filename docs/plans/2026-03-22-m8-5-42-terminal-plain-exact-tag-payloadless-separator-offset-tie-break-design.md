# M8.5.42 Terminal Plain Exact-Tag Payloadless Separator Offset Tie-Break Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already tie on stronger signals and payloadless-separator count prefer payloadless separators appearing later in output, while preserving existing marker/wrapper priorities and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal conditional offset signal:
  - `conditional_first_line_start_plain_exact_tag_payloadless_separator_offset`
- preserve existing `M8.5.41` signals and ordering semantics outside the new tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer/parser/full-text index work
- no broader wrapper-family weighting change

## Context

`M8.5.41` added conditional payloadless plain exact-tag separator count demotion. A narrow gap remains: when payloadless counts tie, results can still be decided by weaker downstream signals (often recency), even if one snapshot pushes payloadless separators later and keeps earlier regions cleaner.

A minimal follow-up is to keep the `M8.5.41` count tie-break, then add a conditional earliest payloadless offset tie-break where later is better.

## Approaches Considered

### 1. Conditional earliest payloadless offset (recommended)

Add `conditional_first_line_start_plain_exact_tag_payloadless_separator_offset` and sort by later offset first.

Pros:

- minimal delta on top of `M8.5.41`
- independent tie-break when payloadless counts are equal
- neutral when no single-space plain exact-tag exists

Cons:

- adds one more derived candidate field

### 2. Payloadless last-offset tie-break

Track last payloadless offset instead of earliest.

Pros:

- directly emphasizes tail cleanliness

Cons:

- less aligned with existing earliest-offset pattern in this ranking chain

### 3. Multi-offset distribution scoring

Compute weighted score from all payloadless offsets.

Pros:

- can capture richer cleanliness distribution

Cons:

- broader than current milestone scope
- harder to keep explainable and regression-safe

## Recommended Approach

Use approach 1: add one conditional earliest payloadless offset tie-break and prefer later offsets.

## Payloadless Offset Rule

Reuse `M8.5.41` payloadless predicate:

- line-start exact-tag hit
- non-marker exact-tag hit
- from separator position after closing wrapper to newline/end, all whitespace

New conditional signal:

- `conditional_first_line_start_plain_exact_tag_payloadless_separator_offset`

Computation:

- if `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use earliest payloadless offset
- otherwise force sentinel to keep fallback neutral in the no-single-space path

Ordering direction:

- later payloadless offset is better (descending by offset)

## Relevance Model Update

For `sort="relevance"`, keep existing keys and insert:

1. `conditional_first_line_start_plain_exact_tag_payloadless_separator_offset` (later is better)

Placement:

- after `conditional_line_start_plain_exact_tag_payloadless_separator_match_count`
- before `conditional_non_exact_tag_punctuation_wrap_match_count`

This preserves the `M8.5.39` -> `M8.5.40` -> `M8.5.41` chain and only resolves this additional tie-break gap.

## Backend Design

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_first_line_start_plain_exact_tag_payloadless_separator_offset`
- add payloadless-offset helper:
  - `_first_line_start_plain_exact_tag_payloadless_separator_offset(...)`
- compute and wire the conditional payloadless offset in `_build_search_candidate(...)`
- update `relevance` tuple with the new key at the placement above

No route, schema, or persistence contract change is required.

## Testing Strategy

Focused service TDD in `tests/services/test_terminal_sessions.py`:

- when stronger signals and payloadless count tie, later payloadless separator offset outranks earlier payloadless separator offset
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.41` behavior
- pagination still slices globally ordered results after the new tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route/API suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, web lint/build, `git diff --check`)

## Risks And Mitigations

- Risk: changing ordering in no-single-space paths.
  - Mitigation: keep new signal conditional on existing single-space guard and assert fallback behavior in tests.
- Risk: misranking payloadless ties due wrong direction.
  - Mitigation: explicit test where only payloadless earliest offset differs and expected winner is older snapshot with later payloadless offset.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
