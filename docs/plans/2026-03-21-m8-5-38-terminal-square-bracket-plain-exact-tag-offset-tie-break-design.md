# M8.5.38 Terminal Square-Bracket Plain Exact-Tag Offset Tie-Break Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, plain square-bracket exact-tag hits such as `[query] text` gain an explicit earliest-offset tie-break when stronger signals are tied, while preserving existing marker-family priority, square-bracket family preference, paren/brace/angle plain-wrapper ordering, and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal signal for square-bracket plain exact-tag quality:
  - `first_line_start_square_bracket_plain_exact_tag_offset`
- preserve existing `M8.5.37` signals and ordering semantics outside the new square-bracket plain offset tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer, parser, or full-text index work
- no changes to the existing `M8.5.26` square-bracket exact-tag family count semantics

## Context

`M8.5.26` introduced square-bracket exact-tag family preference so `[query] text`, `[query]: text`, and `[query] - text` collectively outrank other wrapper exact-tag families. `M8.5.34`, `M8.5.36`, and `M8.5.37` then made the non-square plain-wrapper branches more explicit by adding narrow count/offset or offset-only tie-breaks for `()`, `{}`, and `<>`.

That leaves plain square-bracket exact-tag hits as the only important plain-wrapper slice still relying on the broader `first_line_start_square_bracket_exact_tag_offset` family signal. Today, when stronger signals are tied, `[query] text` falls back to a family-level offset that also covers marker forms, rather than first using a plain-only square-bracket tie-break. The smallest next step is to make the plain `[query] text` offset behavior explicit without widening wrapper precedence or changing the public search contract.

## Approaches Considered

### 1. Explicit square-bracket plain offset tie-break (recommended)

Keep the existing square-bracket exact-tag family preference and add one earliest-offset tie-break dedicated to the plain `[query] text` branch.

Pros:

- minimal additive change
- keeps the plain exact-tag branch more internally consistent
- avoids reworking the broader `M8.5.26` square-bracket family rule

Cons:

- introduces one additional internal metadata field and sentinel constant

### 2. Reorder the existing square-bracket exact-tag family offset

Reuse only `first_line_start_square_bracket_exact_tag_offset` and move it earlier in the tuple.

Pros:

- no new helper or metadata field

Cons:

- mixes marker and plain square-bracket forms
- wider semantic change than the actual gap

### 3. Broader plain exact-tag cleanliness model

Add a new shared cleanliness or noise model across all plain exact-tag wrappers.

Pros:

- potentially more uniform on paper

Cons:

- wider than the immediate gap
- overlaps with `M8.5.35` exact-tag punctuation-noise demotion

## Recommended Approach

Use approach 1: add an explicit square-bracket plain exact-tag earliest-offset tie-break.

## Relevance Model Update

For `sort="relevance"`, keep all existing sort keys and insert:

1. `first_line_start_square_bracket_plain_exact_tag_offset` (ascending)

Placement:

- keep existing `line_start_square_bracket_exact_tag_match_count` in its current descending position
- place the new offset key after `first_line_start_non_square_bracket_exact_tag_dash_marker_offset`
- place it before `first_line_start_paren_wrapper_plain_exact_tag_offset`

This preserves the current branch shape while making plain square-bracket tie-break behavior explicit before control falls back to other plain-wrapper offsets.

## Backend Design

### Service

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `first_line_start_square_bracket_plain_exact_tag_offset`
- add `_NO_LINE_START_SQUARE_BRACKET_PLAIN_EXACT_TAG_MATCH_OFFSET`
- add a narrow helper `_is_line_start_square_bracket_plain_exact_tag_match(...)`:
  - must satisfy line-start exact-tag
  - must be non-marker exact-tag
  - wrapper pair must be `[]`
- add `_count_line_start_square_bracket_plain_exact_tag_hits(...)` returning:
  - count
  - first matching offset
- wire the count + first-offset result in `_build_search_candidate(...)`
- update the `relevance` sort tuple with the new offset key at the placement above

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

- plain square-bracket earlier-offset tie-break when stronger signals are tied
- fallback to `M8.5.37` chain when no plain square-bracket exact-tag exists
- pagination still slices globally ordered relevance results after the new plain square-bracket tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, `web lint`, `web build`, `git diff --check`)

## Risks And Mitigations

- Risk: accidental over-match of square-bracket marker forms.
  - Mitigation: explicitly gate on the existing non-marker exact-tag condition in the new helper.
- Risk: accidental reordering outside the target branch.
  - Mitigation: keep the new sort-key insertion narrow and cover fallback behavior explicitly.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
