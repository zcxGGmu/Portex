# Terminal Relevance Offline Baseline Whitespace Family Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 12 cases so the remaining landed plain exact-tag whitespace-family branches are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 12 to 16 deterministic cases
- add one payloadless separator quality case
- add one tab-prefixed payload offset pagination case
- add one multi-space payload offset pagination case
- add one space-prefixed mixed-whitespace payload offset pagination case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Constraints

- all new cases must be repo-local, offline, deterministic, and reviewable
- expected ordering must come from already-landed service behavior rather than new speculative semantics
- fixture expansion must preserve the existing benchmark harness and failure contract

## Why These Cases

The current 12-case baseline already covers:

- raw/wrapper/plain ladders
- non-square wrapper marker family precedence
- exact-tag punctuation-noise cleanliness
- single-space separator quality
- `M8.5.49` / `M8.5.50` / `M8.5.51` other-leading whitespace paths

The most obvious remaining blind spot is the earlier plain exact-tag whitespace-family chain that was already landed in service tests but is still absent from the offline benchmark:

- `M8.5.41` / `M8.5.42`: payloadless separator family
- `M8.5.43` / `M8.5.44`: tab-prefixed payload family
- `M8.5.45` / `M8.5.46`: multi-space payload family
- `M8.5.47` / `M8.5.48`: space-prefixed mixed-whitespace payload family

## Recommended Cases

1. `payloadless-separator-quality`
   - cover payloadful non-single-space exact-tag output outranking payloadless exact-tag output
   - purpose: bring the payloadless demotion branch into offline coverage

2. `tab-prefixed-payload-offset-pagination`
   - cover later-vs-earlier tab-prefixed payload ordering with sliced pagination
   - purpose: bring the tab-prefixed payload offset branch into offline coverage

3. `multi-space-payload-offset-pagination`
   - cover later-vs-earlier multi-space payload ordering with sliced pagination
   - purpose: bring the multi-space payload offset branch into offline coverage

4. `space-prefixed-mixed-whitespace-offset-pagination`
   - cover later-vs-earlier space-prefixed mixed-whitespace payload ordering with sliced pagination
   - purpose: bring the `M8.5.48` branch into offline coverage

## Approaches Considered

### 1. Expand the fixture with a few targeted whitespace-family cases (recommended)

Pros:

- closes a clear offline coverage gap without touching production code
- keeps the benchmark readable
- matches the baseline-first workflow already established in `docs/progress.md`

Cons:

- still hand-curated rather than exhaustive

### 2. Skip ahead to new ranking changes

Pros:

- faster path to potential new behavior

Cons:

- weakens the evidence base for deciding whether a new tie-break is actually needed

## Recommended Approach

Use approach 1 and expand the fixture from 12 to 16 cases with the four whitespace-family scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: one case accidentally mixes too many signals and becomes hard to reason about.
  - Mitigation: derive each case directly from already-landed service tests and keep only the minimum comparator set needed.
- Risk: fixture size grows without improving decision quality.
  - Mitigation: add only cases that cover specific signal families absent from the current 12-case baseline.
