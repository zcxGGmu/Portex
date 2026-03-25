# Terminal Relevance Offline Baseline Mid Chain Pagination Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 52 cases so the next uncovered mid-chain pagination branches are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 52 to 56 deterministic cases
- add one log-marker pagination case
- add one punctuation-wrap pagination case
- add one exact-tag pagination case
- add one exact-tag-marker pagination case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 52-case baseline already covers:

- early whole-word and line-start layers, including positive, fallback, offset, and pagination behavior
- one non-duplicate exact-tag-wrapper-family fallback
- later brace/angle, whitespace-family, and marker-family branches

The next obvious holes still living only in service tests are the global-ordering slices for the next middle section of the relevance chain:

- `M8.5.21` log-marker pagination
- `M8.5.22` punctuation-wrap pagination
- `M8.5.23` exact-tag pagination
- `M8.5.25` exact-tag-marker pagination

These cases are valuable because they verify that the ranking contracts still survive `limit` / `offset` slicing after the scorer has already applied several earlier layers.

## Recommended Cases

1. `log-marker-pagination`
   - cover the global-ordering slice after log markers outrank punctuation wrappers and plain line starts

2. `punctuation-wrap-pagination`
   - cover the global-ordering slice after punctuation wrappers outrank plain line starts

3. `exact-tag-pagination`
   - cover the global-ordering slice after exact-tag wrappers outrank tight wrappers and plain line starts

4. `exact-tag-marker-pagination`
   - cover the global-ordering slice after exact-tag markers outrank plain exact tags and tighter wrappers

## Approaches Considered

### 1. Expand the fixture with the four middle-chain pagination cases above (recommended)

Pros:

- follows the current handoff guidance directly
- extends offline coverage deeper into the already-landed ranking chain without touching code
- keeps the batch coherent around pagination behavior

Cons:

- leaves a few later-family pagination cases for future batches

### 2. Switch back to more fallback cases first

Pros:

- more variety

Cons:

- current handoff already narrowed the highest-value uncovered space to mid-chain pagination
- several fallback candidates in this area are either duplicated or lower-signal than the pagination gaps

## Recommended Approach

Use approach 1 and expand the fixture from 52 to 56 cases with the four mid-chain pagination scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: pagination cases could overlap with existing pairwise or fallback evidence.
  - Mitigation: use service-test-derived three-entry slices with explicit `limit` / `offset`, so the new cases measure global ordering under pagination rather than re-testing direct pairwise precedence.
- Risk: fixture growth could become noisy.
  - Mitigation: restrict this batch to exactly one pagination case for each newly uncovered middle-chain layer.
