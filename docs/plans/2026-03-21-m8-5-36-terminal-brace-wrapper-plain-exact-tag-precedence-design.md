# M8.5.36 Terminal Brace-Wrapper Plain Exact-Tag Precedence Design

## Goal

Refine terminal history `relevance` ordering so, inside the non-marker exact-tag branch, brace-wrapper plain exact-tag hits such as `{query} text` gain an explicit tie-break (including earliest-offset tie-break) relative to other non-marker wrappers, while preserving existing marker-family priority, square-bracket preference, and API/UI/history compatibility boundaries.

## Scope

- refine backend-only `relevance` ordering used by `GET /terminals/{group_id}/sessions/history/search`
- keep match-set semantics unchanged:
  - substring matching remains unchanged
  - whole-word detection remains ordering-only
  - line-start detection remains ordering-only
  - raw marker and exact-tag marker families remain ordering-only
  - non-marker exact-tag branch remains ordering-only
- add narrow internal signals for brace-wrapper plain exact-tag quality:
  - `line_start_brace_wrapper_plain_exact_tag_match_count`
  - `first_line_start_brace_wrapper_plain_exact_tag_offset`
- preserve existing `M8.5.35` signals and ordering semantics outside the new brace plain tie-break
- keep `newest` / `oldest` behavior unchanged

## Out Of Scope

- no new API parameters, response fields, or `sort` values
- no frontend route or UI changes
- no changes to `latest.json` or `/sessions/current/history`
- no RBAC or workspace-access changes
- no tokenizer, parser, or full-text index work

## Context

`M8.5.33` demoted angle-wrapper plain exact-tag matches and `M8.5.34` promoted paren-wrapper plain exact-tag matches. `M8.5.35` then prevented tighter-wrapper punctuation noise from inflating exact-tag snapshots. The next smallest gap is to make brace-wrapper plain exact-tag ordering explicit and stable inside the same non-marker exact-tag branch, including deterministic earliest-offset tie-break behavior when stronger signals are tied.

## Approaches Considered

### 1. Explicit brace plain exact-tag count + offset tie-break (recommended)

Add brace-wrapper plain exact-tag count and first-offset signals, then place them in the existing non-marker exact-tag ordering chain.

Pros:

- minimal additive change
- deterministic tie-break when stronger signals tie
- keeps the current ranking family boundaries intact

Cons:

- introduces one additional internal helper and metadata fields

### 2. Broader wrapper-family reweighting

Rebalance paren/brace/angle/square at once with new composite weights.

Pros:

- potentially more expressive

Cons:

- wider regression surface
- unnecessary for the immediate gap

### 3. Keep current implicit behavior

Rely on existing angle demotion and generic exact-tag offsets only.

Pros:

- zero code change

Cons:

- brace plain tie-break remains implicit and less deterministic
- harder to reason about future refinements

## Recommended Approach

Use approach 1: add explicit brace-wrapper plain exact-tag count + earliest-offset tie-break as a narrow non-marker exact-tag refinement.

## Relevance Model Update

For `sort="relevance"`, keep all existing sort keys and insert:

1. `line_start_brace_wrapper_plain_exact_tag_match_count` (descending)
2. `first_line_start_brace_wrapper_plain_exact_tag_offset` (ascending)

Placement:

- count key goes after `line_start_paren_wrapper_plain_exact_tag_match_count` and before `line_start_angle_wrapper_plain_exact_tag_match_count`
- offset key goes after `first_line_start_paren_wrapper_plain_exact_tag_offset` and before `first_line_start_exact_tag_marker_offset`

This preserves the existing branch shape while making brace plain tie-break explicit.

## Backend Design

### Service

In `services/terminal_sessions.py`:

- extend `_TerminalSessionHistorySearchCandidate` with two fields:
  - `line_start_brace_wrapper_plain_exact_tag_match_count`
  - `first_line_start_brace_wrapper_plain_exact_tag_offset`
- add `_NO_LINE_START_BRACE_WRAPPER_PLAIN_EXACT_TAG_MATCH_OFFSET`
- add a narrow helper `_is_line_start_brace_wrapper_plain_exact_tag_match(...)`:
  - must satisfy line-start exact-tag
  - must be non-marker exact-tag
  - wrapper pair must be `{}`
- add `_count_line_start_brace_wrapper_plain_exact_tag_hits(...)` returning count + first offset
- wire these signals in `_build_search_candidate(...)`
- update `relevance` sort tuple with the two keys at the placement above

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

- brace plain earliest-offset tie-break when stronger signals tie
- fallback to `M8.5.35` chain when no brace plain exact-tag exists
- pagination still slices globally ordered relevance results after the new brace plain tie-break

Regression verification:

- terminal focused suites (`tests/services/test_terminal_sessions.py` + terminal route suites)
- full backend pytest suite
- lint/build hygiene (`ruff`, `web lint`, `web build`, `git diff --check`)

## Risks And Mitigations

- Risk: accidental reordering outside target branch.
  - Mitigation: keep sort-key insertion narrow and covered by fallback tests.
- Risk: helper over-matching marker cases.
  - Mitigation: explicitly gate on non-marker exact-tag condition.

## Rollout

Backend-only additive ranking refinement; no migration and no client action required.
