# Terminal Relevance Offline Baseline Additive Fallback And Early Pagination Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 48 cases so one remaining non-duplicate additive fallback and the next uncovered early pagination branches are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 48 to 52 deterministic cases
- add one no-exact-tag-wrapper fallback case
- add one whole-word pagination case
- add one line-boundary pagination case
- add one line-start-quality pagination case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 48-case baseline already covers:

- early whole-word and line-start-whole-word positive branches
- the corresponding no-whole-word and no-line-start-whole-word fallback branches
- later wrapper-family, marker-family, brace/angle, separator-quality, and whitespace-family branches

The next high-signal gaps still living only in service tests are:

- fallback from exact-tag-wrapper delimiter quality back to the earlier exact-tag offset behavior when no exact-tag wrapper exists
- pagination behavior for the early `M8.5.18`, `M8.5.19`, and `M8.5.20` layers

This batch is intentionally non-duplicative:

- `no delimited log marker` fallback is not included because its transcript and ordering semantics are already represented by the existing `exact-tag-wrapper-delimiter-quality` case
- `no exact-tag-wrapper` fallback is still worth adding because it exercises a different additive boundary inside the exact-tag-wrapper family

## Recommended Cases

1. `no-exact-tag-wrapper-fallback`
   - cover `M8.5.22` falling back to the earlier exact-tag offset behavior when only tight wrappers remain

2. `whole-word-pagination`
   - cover the global ordering slice after the whole-word layer is applied

3. `line-boundary-pagination`
   - cover the global ordering slice after line-start-whole-word vs mid-line-whole-word behavior is applied

4. `line-start-quality-pagination`
   - cover the global ordering slice after the line-start-quality cleanliness layer is applied

## Approaches Considered

### 1. Expand the fixture with one fallback and three early pagination cases (recommended)

Pros:

- follows the current handoff guidance directly
- adds new evidence without re-testing already-covered pairwise semantics
- keeps the batch coherent around additive fallback and pagination correctness

Cons:

- leaves some later-family pagination and fallback cases for a later batch

### 2. Keep prioritizing only pairwise positive cases

Pros:

- simpler fixture entries

Cons:

- ignores the “global ordering survives slicing” contract that the service tests already protect
- leaves one meaningful additive fallback gap open

## Recommended Approach

Use approach 1 and expand the fixture from 48 to 52 cases with the one fallback and three pagination scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: pagination cases could accidentally duplicate already-covered pairwise semantics.
  - Mitigation: use service-test-derived three-entry slices with explicit `limit` / `offset` so the new evidence is about global ordering under pagination.
- Risk: fallback case could overlap with delimiter-quality evidence.
  - Mitigation: use the landed `M8.5.22` fallback transcript where no exact-tag wrapper exists at all, which is distinct from the positive delimiter-quality branch.
