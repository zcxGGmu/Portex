# Terminal Relevance Offline Baseline Offset Tie-Break Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 20 cases so landed offset-specific marker/plain-wrapper tie-break behaviors are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 20 to 24 deterministic cases
- add one exact-tag colon-marker offset tie-break case
- add one square-bracket exact-tag dash-marker offset tie-break case
- add one paren plain exact-tag offset tie-break case
- add one square-bracket plain exact-tag offset tie-break case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 20-case baseline already covers:

- raw/wrapper/plain ladders
- marker-family pagination branches
- plain-wrapper-family pagination branches
- separator quality, punctuation-noise, and whitespace-family branches
- `M8.5.49` / `M8.5.50` / `M8.5.51` pagination branches

The next highest-value blind spot is offset-sensitive ordering inside already-covered families. The strongest next samples are the landed pairwise offset tie-break tests that do not yet appear in the offline fixture:

- `M8.5.27` exact-tag colon-marker earliest-offset tie-break
- `M8.5.28` square-bracket dash-marker earliest-offset tie-break
- `M8.5.34` paren plain exact-tag earliest-offset tie-break
- `M8.5.38` square-bracket plain exact-tag earliest-offset tie-break

## Recommended Cases

1. `exact-tag-colon-marker-offset-tie-break`
   - cover earlier vs later `[error]: ...` placement once stronger signals already tie

2. `square-bracket-dash-marker-offset-tie-break`
   - cover earlier vs later `[error] - ...` placement once stronger signals already tie

3. `paren-plain-wrapper-offset-tie-break`
   - cover earlier vs later `(error) ...` placement after stronger signals already tie

4. `square-bracket-plain-exact-tag-offset-tie-break`
   - cover earlier vs later `[error] ...` placement after stronger signals already tie

## Approaches Considered

### 1. Expand the fixture with four targeted offset cases (recommended)

Pros:

- closes a clear offline coverage gap without touching production code
- keeps the benchmark readable
- matches the baseline-first workflow already established in `docs/progress.md`

Cons:

- still hand-curated rather than exhaustive

### 2. Keep only ladder/pagination cases and skip offset tie-breaks

Pros:

- smaller fixture

Cons:

- underrepresents the actual reasons many `M8.5.x` refinements landed

## Recommended Approach

Use approach 1 and expand the fixture from 20 to 24 cases with the four offset tie-break scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: an offset case accidentally introduces extra competing signals.
  - Mitigation: derive each new case directly from a landed service-level offset test and keep the smallest comparator set needed.
- Risk: fixture growth adds noise instead of decision value.
  - Mitigation: only add cases that cover a specific tie-break class not yet present in the current 20-case baseline.
