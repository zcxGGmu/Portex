# Terminal Relevance Offline Baseline Brace And Angle Fallback Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 32 cases so the remaining landed brace/angle-side fallback and branch-specific samples are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 32 to 36 deterministic cases
- add one brace plain exact-tag offset tie-break case
- add one angle plain exact-tag pagination case
- add one brace-wrapper marker fallback case
- add one angle plain exact-tag fallback case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 32-case baseline already covers:

- non-square and square marker branches
- brace-wrapper marker pagination and offset behavior
- brace plain and angle plain branch samples
- whitespace-family and punctuation-noise branches

The next obvious brace/angle gaps still living only in service tests are:

- brace plain exact-tag earliest-offset tie-break
- angle plain exact-tag pagination
- brace-wrapper marker fallback when no brace marker exists
- angle plain exact-tag fallback when no angle plain hit exists

## Recommended Cases

1. `brace-plain-exact-tag-offset-tie-break`
   - cover earlier vs later `{error} ...` placement once stronger signals already tie

2. `angle-plain-exact-tag-pagination`
   - cover `brace plain > angle plain > lower-rank generic match`

3. `no-brace-wrapper-marker-fallback`
   - cover fallback from `M8.5.32` to `M8.5.31` when only paren and angle wrapper markers exist

4. `no-angle-plain-exact-tag-fallback`
   - cover fallback from `M8.5.37` to `M8.5.36` when only brace plain exact-tag signals remain

## Approaches Considered

### 1. Expand the fixture with four targeted brace/angle fallback cases (recommended)

Pros:

- closes the remaining obvious branch-level gaps without touching production code
- follows directly from current restart guidance
- keeps the benchmark deterministic and reviewable

Cons:

- still hand-curated rather than exhaustive

### 2. Stop at 32 cases and switch to new ranking logic

Pros:

- smaller fixture

Cons:

- leaves landed branch behavior unrepresented in the offline benchmark

## Recommended Approach

Use approach 1 and expand the fixture from 32 to 36 cases with the four brace/angle fallback scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: a fallback case accidentally introduces unrelated stronger signals.
  - Mitigation: derive each new case directly from a landed service-level test and keep the smallest comparator set needed.
- Risk: fixture growth adds noise instead of decision value.
  - Mitigation: only add cases that cover a branch or fallback not yet present in the current 32-case baseline.
