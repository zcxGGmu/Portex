# M8.5.40 Terminal Plain Exact-Tag Separator-Noise Demotion Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, snapshots that already contain clean single-space plain exact-tag hits gain an explicit tie-break against snapshots whose first extra non-single-space plain exact-tag separator noise appears earlier, while preserving existing marker-family priority, wrapper-family ordering, and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal signal for conditional plain exact-tag separator noise:
  - `conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset`
- preserve existing `M8.5.39` signals and ordering semantics outside the new separator-noise tie-break
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

That leaves a smaller but still real gap inside snapshots that already contain at least one clean single-space plain exact-tag hit. Today a snapshot like `[error]: aa\n[error] ok\n[error]\tok\n` and another like `[error]: aa\n[error]\tok\n[error] ok\n` remain peers once stronger signals tie, even though the snapshot whose first noisy separator appears later should be slightly better. A count-based noise field would be redundant with earlier exact-tag counters in the current tuple, so the smallest effective next step is an earliest-noise-offset tie-break that activates only when at least one clean single-space plain exact-tag hit already exists.

## Approaches Considered

### 1. Conditional earliest-noise-offset tie-break (recommended)

Add a conditional signal that records the earliest non-single-space plain exact-tag separator offset, but only when at least one single-space plain exact-tag hit exists.

Pros:

- directly targets the remaining ranking defect
- stays neutral when no clean single-space plain exact-tag exists
- actually affects ordering without duplicating information already present earlier in the tuple

Cons:

- introduces one additional derived metadata field

### 2. Count-based separator-noise demotion

Penalize the number of non-single-space plain exact-tag hits.

Pros:

- easy to describe on paper

Cons:

- redundant with existing exact-tag and single-space counters in the current tuple
- would not change ranking once stronger counters are tied

### 3. Broader separator scoring model

Explicitly weight multiple separator classes such as single-space, multi-space, and tab forms.

Pros:

- potentially more expressive

Cons:

- wider than the immediate gap
- harder to regression test and explain

## Recommended Approach

Use approach 1: add a conditional earliest-noise-offset tie-break.

## Separator-Noise Model

### Noise Rule

The new signal is:

- `conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset`

Calculate it as:

- the earliest offset among non-single-space plain exact-tag hits
  when `line_start_plain_exact_tag_single_space_separator_match_count > 0`
  and at least one non-single-space plain exact-tag hit exists
- a stable sentinel when either:
  - no single-space plain exact-tag hit exists, or
  - no non-single-space plain exact-tag hit exists

Where non-single-space plain exact-tag hits are derived only from the existing non-marker plain exact-tag helper families and the current single-space separator helper.

Higher is better:

- later noise is better than earlier noise
- no noise is best and uses the sentinel

### Examples

- better:
  - `[error]: aa\n[error] ok\npadding\n[error]\tok`
- worse:
  - `[error]: aa\n[error]\tok\n[error] ok`
- neutral fallback:
  - `[error]\tok`
  - `(error)  ok`
  - because there is no single-space plain exact-tag hit in the snapshot

## Relevance Model Update

For `sort="relevance"`, keep all existing sort keys and insert:

1. `conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset` (later is better)

Placement:

- place the new key after `line_start_plain_exact_tag_single_space_separator_match_count`
- place it before `conditional_non_exact_tag_punctuation_wrap_match_count`

Implementation detail:

- sort this key in descending offset order by negating it in the tuple
- use a large sentinel so “no applicable noise” sorts ahead of earlier noise

This preserves the existing wrapper-family and single-space preference chain while explicitly preferring snapshots whose separator noise appears later, or not at all.

## Backend Design

### Service

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset`
- add `_NO_LINE_START_NON_SINGLE_SPACE_PLAIN_EXACT_TAG_SEPARATOR_MATCH_OFFSET`
- derive the earliest non-single-space plain exact-tag offset only from existing non-marker plain exact-tag helper families and the current single-space separator helper
- compute the conditional offset in `_build_search_candidate(...)`
- update the `relevance` sort tuple with the new key at the placement above, using descending offset semantics

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

- when stronger signals tie, snapshots whose first separator-noise hit appears later outrank snapshots whose first noise appears earlier
- fallback to `M8.5.39` chain when no single-space plain exact-tag exists
- pagination still slices globally ordered relevance results after the new separator-noise tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, `web lint`, `web build`, `git diff --check`)

## Risks And Mitigations

- Risk: accidental inclusion of marker-form offsets in the plain separator-noise signal.
  - Mitigation: derive the earliest noise offset only from existing non-marker plain exact-tag helper families.
- Risk: placing the signal too early and overriding wrapper-family ordering.
  - Mitigation: place it after the existing single-space preference and cover fallback behavior explicitly.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
