# M8.5.37 Terminal Angle-Wrapper Plain Exact-Tag Offset Tie-Break Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, angle-wrapper plain exact-tag hits such as `<query> text` gain an explicit earliest-offset tie-break when angle plain counts are tied, while preserving existing marker-family priority, square-bracket preference, paren/brace plain-wrapper ordering, and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add one narrow internal signal for angle-wrapper plain exact-tag quality:
  - `first_line_start_angle_wrapper_plain_exact_tag_offset`
- preserve existing `M8.5.36` signals and ordering semantics outside the new angle plain offset tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer, parser, or full-text index work

## Context

`M8.5.33` introduced a narrow angle-wrapper plain exact-tag demotion by count so `<query> text` falls behind the stronger plain exact-tag families. `M8.5.34` and `M8.5.36` then made the paren and brace plain-wrapper branches explicit with count + earliest-offset tie-breaks, and `M8.5.35` added conditional punctuation-noise demotion for exact-tag snapshots.

That leaves the angle plain branch as the only plain-wrapper signal without its own explicit earliest-offset behavior. Today, when stronger signals and `line_start_angle_wrapper_plain_exact_tag_match_count` are tied, ordering falls through to broader exact-tag or punctuation offsets instead of first using a narrow angle-plain tie-break. The smallest next step is to make that offset behavior explicit without widening wrapper-family precedence or changing the public search contract.

## Approaches Considered

### 1. Explicit angle plain offset tie-break (recommended)

Keep the existing angle plain count demotion and add one earliest-offset tie-break dedicated to the same narrow branch.

Pros:

- minimal additive change
- makes the plain-wrapper family more internally consistent
- avoids widening the wrapper hierarchy beyond the already-approved `M8.5.33` demotion

Cons:

- introduces one additional internal metadata field and sentinel constant

### 2. Angle-specific extra cleanliness demotion

Add another angle-only cleanliness or noise penalty on top of the existing count demotion.

Pros:

- could separate more edge cases

Cons:

- overlaps with `M8.5.35` exact-tag punctuation-noise demotion
- increases regression surface without evidence that more than offset stability is needed

### 3. Broader plain-wrapper offset model

Rework the whole non-marker wrapper family with a wider composite offset model.

Pros:

- potentially more uniform on paper

Cons:

- wider than the immediate gap
- unnecessary for the current backend-only incremental milestone

## Recommended Approach

Use approach 1: add an explicit angle-wrapper plain exact-tag earliest-offset tie-break.

## Relevance Model Update

For `sort="relevance"`, keep all existing sort keys and insert:

1. `first_line_start_angle_wrapper_plain_exact_tag_offset` (ascending)

Placement:

- keep existing `line_start_angle_wrapper_plain_exact_tag_match_count` in its current ascending position
- place the new offset key after `first_line_start_brace_wrapper_plain_exact_tag_offset`
- place it before `first_line_start_exact_tag_marker_offset`

This preserves the current branch shape while making angle plain tie-break behavior explicit before control falls back to broader exact-tag offsets.

## Backend Design

### Service

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with:
  - `first_line_start_angle_wrapper_plain_exact_tag_offset`
- add `_NO_LINE_START_ANGLE_WRAPPER_PLAIN_EXACT_TAG_MATCH_OFFSET`
- update `_count_line_start_angle_wrapper_plain_exact_tag_hits(...)` to return:
  - count
  - first matching offset
- keep `_is_line_start_angle_wrapper_plain_exact_tag_match(...)` semantics unchanged:
  - must satisfy line-start exact-tag
  - must be non-marker exact-tag
  - wrapper pair must be `<>`
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

- angle plain earlier-offset tie-break when stronger signals and angle plain counts tie
- fallback to `M8.5.36` chain when no angle plain exact-tag exists
- pagination still slices globally ordered relevance results after the new angle plain tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, `web lint`, `web build`, `git diff --check`)

## Risks And Mitigations

- Risk: accidental reordering outside the target branch.
  - Mitigation: keep the new sort-key insertion narrow and cover fallback behavior explicitly.
- Risk: changing angle plain match semantics instead of only the tie-break.
  - Mitigation: reuse the existing helper predicate unchanged and only extend the count helper to capture first offset.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
