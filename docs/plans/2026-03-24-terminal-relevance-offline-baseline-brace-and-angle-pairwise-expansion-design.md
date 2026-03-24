# Terminal Relevance Offline Baseline Brace And Angle Pairwise Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 36 cases so the remaining landed brace/angle direct pairwise and branch-specific fallback/offset behaviors are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 36 to 40 deterministic cases
- add one brace-wrapper direct pairwise marker case
- add one brace-vs-angle plain exact-tag pairwise case
- add one no-brace-plain fallback case
- add one angle-plain exact-tag offset tie-break case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 36-case baseline already covers:

- brace-wrapper marker pagination and offset behavior
- brace plain exact-tag pagination and offset behavior
- angle plain exact-tag pagination and offset behavior
- brace/angle fallback samples

The remaining obvious brace/angle gaps still living only in service tests are the simple direct pairwise comparisons plus one remaining plain fallback and one remaining angle offset pair:

- `M8.5.32` brace-wrapper marker over angle-wrapper marker
- `M8.5.36` brace plain exact-tag over angle plain exact-tag
- `M8.5.35` fallback when no brace plain exact-tag exists
- `M8.5.37` angle plain exact-tag earliest-offset tie-break

## Recommended Cases

1. `brace-wrapper-marker-pairwise`
   - cover `{error}: ...` outranking `<error>: ...` directly, without pagination slicing

2. `brace-plain-exact-tag-pairwise`
   - cover `{error} ...` outranking `<error> ...` directly, without pagination slicing

3. `no-brace-plain-exact-tag-fallback`
   - cover fallback from `M8.5.36` to `M8.5.35` when only tighter wrapper punctuation signals remain

4. `angle-plain-exact-tag-offset-tie-break`
   - cover earlier vs later `<error> ...` placement once stronger signals already tie

## Approaches Considered

### 1. Expand the fixture with four targeted brace/angle pairwise cases (recommended)

Pros:

- closes the remaining obvious branch-level gaps without touching production code
- follows directly from current restart guidance
- keeps the benchmark deterministic and reviewable

Cons:

- still hand-curated rather than exhaustive

### 2. Stop at 36 cases and switch to new ranking logic

Pros:

- smaller fixture

Cons:

- leaves landed branch behavior unrepresented in the offline benchmark

## Recommended Approach

Use approach 1 and expand the fixture from 36 to 40 cases with the four brace/angle pairwise scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: new cases duplicate already-covered pagination behavior.
  - Mitigation: only add direct pairwise or fallback cases that are still absent from the current 36-case fixture.
- Risk: fixture growth adds noise instead of decision value.
  - Mitigation: only add cases tied to a specific landed branch rule not yet represented offline.
