# Terminal Relevance Offline Baseline Whitespace Fallback Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 66 cases so the remaining whitespace-family no-single-space fallback branches are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 66 to 70 deterministic cases
- add one tab-prefixed payload no-single-space fallback case
- add one multi-space payload no-single-space fallback case
- add one space-prefixed mixed-whitespace payload no-single-space fallback case
- add one other-leading whitespace payload no-single-space fallback case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 66-case baseline has already consumed the last planned payload/whitespace pagination gaps:

- `multi-space-payload-pagination`
- `space-prefixed-mixed-whitespace-payload-pagination`
- the earlier payload/offset pagination samples for payloadless, tab-prefixed, other-leading whitespace, and mixed-other families

What is still missing is the fallback behavior when the stronger single-space plain exact-tag signal does not exist. The fixture currently keeps only one such fallback sample:

- `no-single-space-fallback` for the `M8.5.51` mixed-other family

The earlier whitespace families still lack direct offline evidence for the same fallback boundary:

- `M8.5.44` tab-prefixed payload fallback
- `M8.5.46` multi-space payload fallback
- `M8.5.48` space-prefixed mixed-whitespace payload fallback
- `M8.5.49` other-leading whitespace payload fallback

These cases are not duplicates of the existing pagination samples because they verify the fallback ordering when the higher-priority single-space branch is absent, not merely the paginated slice of an already-ranked result set.

## Recommended Cases

1. `tab-prefixed-payload-no-single-space-fallback`
   - cover the earlier-vs-later tab-prefixed payload ordering when no single-space plain exact-tag signal exists

2. `multi-space-payload-no-single-space-fallback`
   - cover the earlier-vs-later multi-space payload ordering when the search must fall back past the single-space branch

3. `space-prefixed-mixed-whitespace-no-single-space-fallback`
   - cover the earlier-vs-later mixed-whitespace payload ordering when the fallback skips the stronger single-space separator

4. `other-leading-whitespace-no-single-space-fallback`
   - cover the earlier-vs-later other-leading whitespace payload ordering without any single-space plain exact-tag evidence

## Approaches Considered

### 1. Add the four missing whitespace-family fallback cases only (recommended)

Pros:

- closes a real coverage gap without duplicating pagination evidence
- keeps the benchmark tied to already-landed service behavior
- gives the next tie-break decision a better offline evidence base

Cons:

- adds another targeted batch instead of declaring the baseline “done”

### 2. Add more pagination samples from the same families

Pros:

- follows the recent pagination-expansion pattern

Cons:

- duplicates already-covered global-ordering evidence
- does not improve visibility into fallback behavior

### 3. Skip directly to post-`M8.5.51` ranking changes

Pros:

- faster path to new behavior

Cons:

- weakens the baseline-first workflow that has guided the recent terminal work

## Recommended Approach

Use approach 1 and expand the fixture from 66 to 70 cases with the four missing whitespace-family fallback scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: fallback cases may look too similar to existing offset-pagination samples.
  - Mitigation: derive each case from the service tests that explicitly omit the single-space branch so the semantics stay distinct.
- Risk: restart docs could remain stale about what gaps are actually left.
  - Mitigation: update `docs/progress.md` and `AGENTS.md` to say pagination coverage is exhausted and this batch targets fallback coverage instead.
