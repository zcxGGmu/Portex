# Terminal Relevance Offline Baseline Non-Square Marker Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 24 cases so the landed non-square marker branch behaviors are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 24 to 28 deterministic cases
- add one non-square exact-tag colon-marker pagination case
- add one non-square exact-tag colon-marker offset tie-break case
- add one non-square exact-tag dash-marker pagination case
- add one non-square exact-tag dash-marker offset tie-break case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 24-case baseline already covers:

- raw/wrapper/plain ladders
- square-bracket marker pagination and offset tie-breaks
- plain-wrapper pagination and offset tie-breaks
- separator quality, punctuation-noise, and whitespace-family branches

The next most obvious gap is the non-square marker branch that landed in:

- `M8.5.29`: non-square exact-tag colon-marker priority and offset behavior
- `M8.5.30`: non-square exact-tag dash-marker placement and offset behavior

These are currently present in service tests but absent from the offline benchmark.

## Recommended Cases

1. `non-square-colon-marker-pagination`
   - cover `(error): ...` outranking `(error) - ...` once shared `[error]: ...` stronger signals already tie

2. `non-square-colon-marker-offset-tie-break`
   - cover earlier vs later `(error): ...` placement once stronger signals already tie

3. `non-square-dash-marker-pagination`
   - cover `(error) - ...` outranking `(error) ...` once shared `[error] - ...` stronger signals already tie

4. `non-square-dash-marker-offset-tie-break`
   - cover earlier vs later `(error) - ...` placement once stronger signals already tie

## Approaches Considered

### 1. Expand the fixture with four targeted non-square marker cases (recommended)

Pros:

- closes a clear offline coverage gap without touching production code
- directly matches the current restart guidance
- keeps the benchmark readable and deterministic

Cons:

- still hand-curated rather than exhaustive

### 2. Jump to a new production tie-break

Pros:

- faster route to behavior change

Cons:

- weak evidence base for deciding whether a new tie-break is justified

## Recommended Approach

Use approach 1 and expand the fixture from 24 to 28 cases with the four non-square marker scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: a case accidentally mixes too many unrelated signals.
  - Mitigation: derive each new case directly from a landed service-level test and keep the smallest comparator set needed.
- Risk: fixture growth adds noise instead of decision value.
  - Mitigation: only add cases that cover a specific branch not yet present in the current 24-case baseline.
