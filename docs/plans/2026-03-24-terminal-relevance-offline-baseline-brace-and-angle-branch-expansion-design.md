# Terminal Relevance Offline Baseline Brace And Angle Branch Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 28 cases so the landed brace/angle-side marker and plain-wrapper branch behaviors are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 28 to 32 deterministic cases
- add one brace-wrapper marker pagination case
- add one brace-wrapper marker offset tie-break case
- add one brace plain exact-tag pagination case
- add one angle plain exact-tag offset pagination case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 28-case baseline already covers:

- raw/wrapper/plain ladders
- square-bracket and non-square marker pagination/offset samples
- paren and square-bracket plain-wrapper pagination/offset samples
- whitespace-family and punctuation-noise branches

The next obvious gaps are the brace/angle-side branch-specific samples that still live only in service tests:

- `M8.5.32` brace-wrapper marker branch
- `M8.5.36` brace plain exact-tag branch
- `M8.5.37` angle plain exact-tag branch

## Recommended Cases

1. `brace-wrapper-marker-pagination`
   - cover `{error}: ...` outranking `<error>: ...` with a lower-rank plain exact-tag comparator

2. `brace-wrapper-marker-offset-tie-break`
   - cover earlier vs later `{error}: ...` placement once stronger signals already tie

3. `brace-plain-exact-tag-pagination`
   - cover brace plain exact-tag branch behavior against later brace placement and tighter-wrapper noise

4. `angle-plain-exact-tag-offset-pagination`
   - cover earlier vs later `<error> ...` placement with a lower-rank generic match comparator

## Approaches Considered

### 1. Expand the fixture with four targeted brace/angle branch cases (recommended)

Pros:

- closes a clear offline coverage gap without touching production code
- follows directly from the current restart guidance
- keeps the benchmark deterministic and reviewable

Cons:

- still hand-curated rather than exhaustive

### 2. Skip ahead to new ranking work

Pros:

- faster route to possible behavior changes

Cons:

- weak evidence base for deciding whether a new tie-break is justified

## Recommended Approach

Use approach 1 and expand the fixture from 28 to 32 cases with the four brace/angle branch scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: a case accidentally mixes too many unrelated signals.
  - Mitigation: derive each new case directly from a landed service-level test and keep the smallest comparator set needed.
- Risk: fixture growth adds noise instead of decision value.
  - Mitigation: only add cases that cover a specific branch not yet present in the current 28-case baseline.
