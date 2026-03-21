# M8.5.41 Terminal Plain Exact-Tag Payloadless Separator Demotion Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already contain clean single-space plain exact-tag hits prefer fewer payloadless plain exact-tag separators (for example `[error]\t  \n`), while preserving existing marker-family priority, wrapper-family ordering, and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal signal for conditional payloadless separator noise:
  - `conditional_line_start_plain_exact_tag_payloadless_separator_match_count`
- preserve existing `M8.5.40` signals and ordering semantics outside the new payloadless tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer/parser/full-text index work
- no broader wrapper-family weighting change

## Context

`M8.5.39` introduced single-space plain exact-tag preference and `M8.5.40` introduced a conditional earliest non-single-space noise offset. That still leaves a narrow gap: once stronger signals and earliest non-single-space offset are tied, snapshots with payloadless plain exact-tag separators can rank the same as snapshots where every non-single-space separator still carries real payload text.

A minimal follow-up is to count payloadless plain exact-tag separators only when single-space plain exact-tag hits already exist, then prefer fewer such payloadless separators.

## Approaches Considered

### 1. Conditional payloadless-separator count (recommended)

Add a conditional count for payloadless plain exact-tag separators and sort fewer first.

Pros:

- narrow and focused on the remaining quality gap
- complements `M8.5.40` earliest-noise-offset tie-break
- neutral when no single-space plain exact-tag exists

Cons:

- adds one more derived candidate field

### 2. Payloadless earliest-offset only

Use only earliest payloadless offset, not count.

Pros:

- keeps the shape similar to `M8.5.40`

Cons:

- weaker when payloadless separators appear multiple times

### 3. Separator-class weighting model

Create explicit weights for tab/multi-space/payloadless families.

Pros:

- can model more cases

Cons:

- broader than current milestone scope
- harder to regression-test and explain

## Recommended Approach

Use approach 1: add a conditional payloadless-separator count tie-break.

## Payloadless Separator Rule

A line-start plain exact-tag hit is considered payloadless when:

- it is a non-marker exact-tag hit, and
- from the separator position after the closing wrapper to the next newline (or end-of-output), all characters are whitespace

Examples:

- payloadless:
  - `[error]`
  - `[error]   `
  - `[error]\t  `
- not payloadless:
  - `[error] ok`
  - `[error]\tok`
  - `[error]: ok`
  - `[error] - ok`

The new conditional signal:

- `conditional_line_start_plain_exact_tag_payloadless_separator_match_count`

Computation:

- if `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use payloadless count
- otherwise force `0` to keep fallback neutral

## Relevance Model Update

For `sort="relevance"`, keep existing keys and insert:

1. `conditional_line_start_plain_exact_tag_payloadless_separator_match_count` (fewer is better)

Placement:

- after `conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset`
- before `conditional_non_exact_tag_punctuation_wrap_match_count`

This keeps `M8.5.39` + `M8.5.40` chain intact and only resolves this additional tie-break gap.

## Backend Design

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_line_start_plain_exact_tag_payloadless_separator_match_count`
- add payloadless helpers:
  - `_is_line_start_plain_exact_tag_payloadless_separator_match(...)`
  - `_count_line_start_plain_exact_tag_payloadless_separator_hits(...)`
- compute and wire the conditional payloadless count in `_build_search_candidate(...)`
- update the `relevance` tuple with the new key at the placement above

No route, schema, or persistence contract change is required.

## Testing Strategy

Focused service TDD in `tests/services/test_terminal_sessions.py`:

- when stronger signals tie, fewer payloadless plain exact-tag separators outrank more payloadless separators
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.40` behavior
- pagination still slices globally ordered results after the new tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route/API suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, web lint/build, `git diff --check`)

## Risks And Mitigations

- Risk: counting marker forms as payloadless plain exact-tags.
  - Mitigation: explicitly gate payloadless helper behind non-marker exact-tag predicate.
- Risk: changing behavior when no single-space plain exact-tag exists.
  - Mitigation: make the new field conditional and force neutral `0` in no-single-space path; add fallback tests.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
