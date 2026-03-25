# Terminal Relevance Offline Baseline Payload And Offset Pagination Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 60 cases so the next uncovered payload-family and remaining plain exact-tag offset pagination branches are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 60 to 64 deterministic cases
- add one payloadless plain exact-tag separator pagination case
- add one payloadless offset tie-break pagination case
- add one tab-prefixed payload pagination case
- add one square-bracket plain exact-tag offset pagination case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 60-case baseline already covers:

- early, mid, and later quality-family pagination through separator-noise
- exact-tag and marker-family pagination through the middle of the ranking chain

The next obvious holes still living only in service tests are:

- `M8.5.41` payloadless plain exact-tag separator pagination
- `M8.5.42` payloadless offset tie-break pagination
- `M8.5.43` tab-prefixed payload pagination
- `M8.5.38` square-bracket plain exact-tag offset pagination

This is a pragmatic batch because three cases belong to the same payload-family chain and the remaining square-bracket plain-offset pagination is still explicitly called out in current handoff notes as uncovered.

## Recommended Cases

1. `payloadless-plain-exact-tag-separator-pagination`
   - cover the paginated slice after payloadful non-single separators outrank payloadless separators

2. `payloadless-offset-tie-break-pagination`
   - cover the paginated slice after later payloadless separator offsets outrank earlier payloadless offsets under stronger-signal ties

3. `tab-prefixed-payload-pagination`
   - cover the paginated slice after non-tab payloadful separators outrank tab-prefixed payload separators

4. `square-bracket-plain-exact-tag-offset-pagination`
   - cover the paginated slice after later square-bracket plain exact-tag offsets outrank lower-ranked entries

## Approaches Considered

### 1. Expand the fixture with the four payload/offset pagination cases above (recommended)

Pros:

- follows the current handoff guidance directly
- captures the next uncovered payload-family pagination behavior in one coherent batch
- clears one remaining non-payload pagination gap without re-opening already-covered family ladders

Cons:

- leaves later payload-family offset-pagination branches for a future batch

### 2. Keep focusing only on one family and defer square-bracket plain offset again

Pros:

- slightly tighter thematic scope

Cons:

- ignores a specifically documented remaining gap
- creates more handoff churn than necessary

## Recommended Approach

Use approach 1 and expand the fixture from 60 to 64 cases with the four payload/offset pagination scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: some payload-family pagination cases could look too similar to existing offset-pagination samples.
  - Mitigation: use the exact service-test-derived three-entry slices with explicit `limit` / `offset`, so the new evidence is about pagination after the payload-family rules, not the earlier pairwise branches.
- Risk: square-bracket plain exact-tag offset pagination could be mistaken for the already-covered offset tie-break case.
  - Mitigation: keep the paginated three-entry shape and explicit lower-ranked third entry, which makes this case about global ordering under pagination rather than the raw pairwise tie-break.
