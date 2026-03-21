# M8.5.40 Terminal Plain Exact-Tag Separator-Noise Demotion Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already contain single-space plain exact-tag hits are demoted when they also contain extra multi-space or tab-separated plain exact-tag separator noise, while preserving existing marker-family priority, wrapper-family ordering, and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal signal for conditional plain exact-tag separator noise:
  - `conditional_non_single_space_plain_exact_tag_separator_match_count`
- preserve existing `M8.5.39` signals and ordering semantics outside the new separator-noise demotion
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer, parser, or full-text index work
- no broader whitespace-normalization model outside the narrow plain exact-tag branch

## Context

`M8.5.34`, `M8.5.36`, `M8.5.37`, and `M8.5.38` progressively made the plain exact-tag wrapper families more explicit with wrapper-specific tie-breaks. `M8.5.39` then added a plain exact-tag single-space separator preference so cleaner forms like `[query] text` rank ahead of looser whitespace forms such as `[query]\ttext`.

That leaves a smaller but still real gap inside snapshots that already contain at least one clean single-space plain exact-tag hit. Today a snapshot like `[error] ok\n[error]\tok\n` still keeps the extra tab-separated plain exact-tag hit as a neutral peer once stronger signals tie, even though it should act as noise relative to a snapshot containing only clean single-space exact-tag separators. The smallest next step is to add one conditional demotion signal that only activates when at least one clean single-space plain exact-tag hit already exists.

## Approaches Considered

### 1. Conditional plain exact-tag separator-noise demotion (recommended)

Add a conditional signal that penalizes additional non-single-space plain exact-tag hits, but only when at least one single-space plain exact-tag hit exists.

Pros:

- directly targets the remaining ranking defect
- stays neutral when no clean single-space plain exact-tag exists
- aligns with the narrow conditional-demotion style already used by `M8.5.35`

Cons:

- introduces one additional derived metadata field

### 2. Broader separator scoring model

Explicitly weight multiple separator classes such as single-space, multi-space, and tab forms.

Pros:

- potentially more expressive

Cons:

- wider than the immediate gap
- harder to regression test and explain

### 3. More wrapper-specific micro-tie-breaks

Continue refining each wrapper pair separately instead of modeling separator noise directly.

Pros:

- matches the recent wrapper-specific cadence

Cons:

- the wrapper-family chain is already explicit enough
- does not address the actual separator-noise problem

## Recommended Approach

Use approach 1: add a conditional plain exact-tag separator-noise demotion.

## Separator-Noise Model

### Noise Rule

The new signal is:

- `conditional_non_single_space_plain_exact_tag_separator_match_count`

Calculate it as:

- `line_start_plain_exact_tag_match_count_total - line_start_plain_exact_tag_single_space_separator_match_count`
  when `line_start_plain_exact_tag_single_space_separator_match_count > 0`
- `0` when `line_start_plain_exact_tag_single_space_separator_match_count == 0`

Where `line_start_plain_exact_tag_match_count_total` is derived only from existing non-marker plain exact-tag helper families:

- square-bracket plain exact-tag hits
- paren-wrapper plain exact-tag hits
- brace-wrapper plain exact-tag hits
- angle-wrapper plain exact-tag hits

Lower is better.

### Examples

- noise count is `0`:
  - `[error] ok`
  - `(error) ok`
- noise count is `1`:
  - `[error] ok\n[error]\tok`
  - `(error) ok\n(error)  ok`
- signal stays neutral:
  - `[error]\tok`
  - `(error)  ok`
  - because there is no single-space plain exact-tag hit in the snapshot

## Relevance Model Update

For `sort="relevance"`, keep all existing sort keys and insert:

1. `conditional_non_single_space_plain_exact_tag_separator_match_count` (ascending)

Placement:

- place the new key after `line_start_plain_exact_tag_single_space_separator_match_count`
- place it before `conditional_non_exact_tag_punctuation_wrap_match_count`

This preserves the existing wrapper-family and single-space preference chain while explicitly demoting snapshots that mix clean and noisy plain exact-tag separator forms.

## Backend Design

### Service

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_non_single_space_plain_exact_tag_separator_match_count`
- derive `line_start_plain_exact_tag_match_count_total` from existing helper results:
  - square-bracket plain exact-tag count
  - paren-wrapper plain exact-tag count
  - brace-wrapper plain exact-tag count
  - angle-wrapper plain exact-tag count
- compute the conditional noise count in `_build_search_candidate(...)`
- update the `relevance` sort tuple with the new key at the placement above

No new parser or route contract is required.

### Route/API

No route or DTO changes.

### Compatibility

No change to:

- search snippet generation
- pagination contract (still global rank then slice)
- `latest.json` and persisted history formats
- `/sessions/current/history`
- RBAC boundaries

## Testing Strategy

Focused service TDD in `tests/services/test_terminal_sessions.py`:

- snapshots with fewer separator-noise plain exact-tag hits outrank noisier snapshots when stronger signals tie
- fallback to `M8.5.39` chain when no single-space plain exact-tag exists
- pagination still slices globally ordered relevance results after the new separator-noise demotion

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, `web lint`, `web build`, `git diff --check`)

## Risks And Mitigations

- Risk: accidental inclusion of marker-form counts in the plain separator-noise total.
  - Mitigation: derive the total only from existing non-marker plain exact-tag helper families.
- Risk: placing the signal too early and overriding wrapper-family ordering.
  - Mitigation: place it after the existing single-space preference and cover fallback behavior explicitly.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
