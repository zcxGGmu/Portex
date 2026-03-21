# M8.5.39 Terminal Plain Exact-Tag Single-Space Separator Preference Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, plain exact-tag hits that use a single-space separator after the closing wrapper such as `[query] text`, `(query) text`, `{query} text`, and `<query> text` gain an explicit quality preference over otherwise similar plain exact-tag hits that use looser whitespace separators, while preserving existing marker-family priority, wrapper-family ordering, and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal signal for plain exact-tag separator quality:
  - `line_start_plain_exact_tag_single_space_separator_match_count`
- optionally track earliest offset for the same narrow branch only if needed to keep ordering deterministic:
  - `first_line_start_plain_exact_tag_single_space_separator_offset`
- preserve existing `M8.5.38` signals and ordering semantics outside the new single-space separator preference
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer, parser, or full-text index work
- no broader whitespace-normalization model outside the narrow plain exact-tag branch

## Context

`M8.5.34`, `M8.5.36`, `M8.5.37`, and `M8.5.38` progressively made the plain exact-tag wrapper families more explicit with wrapper-specific count and offset tie-breaks. `M8.5.35` also introduced a narrow punctuation-noise demotion so exact-tag snapshots stop getting extra credit from tighter wrapper noise.

The next remaining rough edge is no longer wrapper-family precedence. It is separator cleanliness inside already-valid plain exact-tag forms. Today `[error] text`, `[error]  text`, and `[error]\ttext` all continue to rely on broader wrapper and offset signals once stronger signals tie, even though the single-space form is the cleanest and most common operator-facing shape. The smallest next step is to add one narrow quality signal that prefers `closing-wrapper + single ASCII space + non-whitespace text` while leaving the public search contract unchanged.

## Approaches Considered

### 1. Plain exact-tag single-space separator preference (recommended)

Add a narrow signal that rewards only plain exact-tag hits whose separator is exactly one ASCII space.

Pros:

- minimal additive change
- wrapper-agnostic inside the plain exact-tag branch
- easier to explain than a broader whitespace cleanliness model

Cons:

- introduces one additional internal helper and metadata field(s)

### 2. General whitespace cleanliness scoring

Add a wider signal that counts and ranks multiple whitespace shapes after plain exact-tags.

Pros:

- could separate more edge cases

Cons:

- broader than the immediate gap
- harder to reason about and regression test

### 3. Continue wrapper-specific micro-tie-breaks

Add another wrapper-pair-specific signal instead of a separator-quality signal.

Pros:

- matches the recent wrapper-specific cadence

Cons:

- the wrapper families already have explicit coverage
- does not address the actual remaining gap

## Recommended Approach

Use approach 1: add a plain exact-tag single-space separator preference.

## Relevance Model Update

For `sort="relevance"`, keep all existing sort keys and insert:

1. `line_start_plain_exact_tag_single_space_separator_match_count` (descending)
2. `first_line_start_plain_exact_tag_single_space_separator_offset` (ascending), if implemented

Placement:

- place the new count key after the existing plain wrapper-specific count chain:
  - after `line_start_angle_wrapper_plain_exact_tag_match_count`
- place it before `conditional_non_exact_tag_punctuation_wrap_match_count`
- place the new offset key, if used, after `first_line_start_angle_wrapper_plain_exact_tag_offset`
- place it before `first_line_start_exact_tag_marker_offset`

This preserves the existing wrapper-family structure while making separator cleanliness explicit before control falls back to broader punctuation-noise and exact-tag offsets.

## Backend Design

### Service

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `line_start_plain_exact_tag_single_space_separator_match_count`
  - `first_line_start_plain_exact_tag_single_space_separator_offset`
- add `_NO_LINE_START_PLAIN_EXACT_TAG_SINGLE_SPACE_SEPARATOR_MATCH_OFFSET`
- add a narrow helper `_is_line_start_plain_exact_tag_single_space_separator_match(...)`:
  - must satisfy line-start exact-tag
  - must be non-marker exact-tag
  - the character immediately after the closing wrapper must be `" "`
  - the following character must exist and must not be whitespace
- add `_count_line_start_plain_exact_tag_single_space_separator_hits(...)` returning:
  - count
  - first matching offset
- wire the count + first-offset result in `_build_search_candidate(...)`
- update the `relevance` sort tuple with the new key(s) at the placement above

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

- single-space plain exact-tag outranks multi-space or tab-separated plain exact-tag when stronger signals are tied
- fallback to `M8.5.38` chain when no single-space plain exact-tag exists
- pagination still slices globally ordered relevance results after the new single-space separator preference

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, `web lint`, `web build`, `git diff --check`)

## Risks And Mitigations

- Risk: accidentally matching marker forms.
  - Mitigation: explicitly gate on the existing non-marker exact-tag condition in the new helper.
- Risk: placing the signal too early and overriding wrapper-family ordering.
  - Mitigation: place the new signal after the existing plain wrapper-specific chain and cover fallback behavior explicitly.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
