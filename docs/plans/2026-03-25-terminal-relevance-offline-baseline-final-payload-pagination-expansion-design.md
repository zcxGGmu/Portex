# Terminal Relevance Offline Baseline Final Payload Pagination Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 64 cases so the last uncovered payload/whitespace-family pagination branches are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 64 to 66 deterministic cases
- add one multi-space payload pagination case
- add one space-prefixed mixed-whitespace payload pagination case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

After the latest payload/offset batch, the remaining uncovered pagination gaps in the payload/whitespace families have narrowed to just two non-duplicate service-level cases:

- `M8.5.45` multi-space payload pagination
- `M8.5.47` space-prefixed mixed-whitespace payload pagination

The nearby candidates are already represented in the fixture:

- tab-prefixed payload pagination and offset pagination
- payloadless separator and payloadless offset pagination
- square-bracket plain exact-tag offset pagination
- other-leading whitespace and mixed-other pagination

Trying to force a 4-case batch here would only duplicate existing evidence, so the clean move is to close the last two real gaps instead.

## Recommended Cases

1. `multi-space-payload-pagination`
   - cover the paginated slice after fewer multi-space payload separators outrank noisier multi-space payload separators

2. `space-prefixed-mixed-whitespace-payload-pagination`
   - cover the paginated slice after fewer space-prefixed mixed-whitespace payload separators outrank noisier mixed separators

## Approaches Considered

### 1. Add the final two uncovered payload/whitespace pagination cases only (recommended)

Pros:

- keeps the baseline non-duplicative
- closes the real remaining gaps instead of inflating fixture size
- matches the current baseline-first strategy cleanly

Cons:

- smaller batch than earlier iterations

### 2. Force a 4-case batch by rephrasing already-covered offset pagination samples

Pros:

- superficially keeps the same batch size pattern

Cons:

- duplicates existing evidence
- makes the restart docs less trustworthy

## Recommended Approach

Use approach 1 and expand the fixture from 64 to 66 cases with the two remaining payload/whitespace pagination scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: a smaller batch could look accidental.
  - Mitigation: explicitly document that adjacent payload-family pagination samples are already covered and this batch closes the final non-duplicate gaps.
- Risk: these cases could still overlap semantically with existing offset-pagination evidence.
  - Mitigation: use the service-test-derived three-entry `limit=2` / `offset=1` slices, which verify pagination for the count-quality branch rather than offset tie-break behavior.
