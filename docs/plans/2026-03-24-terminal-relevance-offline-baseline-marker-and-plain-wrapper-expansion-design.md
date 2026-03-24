# Terminal Relevance Offline Baseline Marker And Plain Wrapper Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 16 cases so the landed marker-family and plain-wrapper-family pagination behaviors are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 16 to 20 deterministic cases
- add one exact-tag colon-marker pagination case
- add one square-bracket exact-tag dash-marker pagination case
- add one square-bracket exact-tag pagination case
- add one paren plain-wrapper pagination case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 16-case baseline already covers:

- raw/wrapper/plain ladders
- non-square wrapper marker family precedence
- separator quality and punctuation-noise branches
- payloadless/tab/multi-space/mixed-whitespace families
- `M8.5.49` / `M8.5.50` / `M8.5.51` other-leading whitespace branches

The most obvious remaining high-signal gaps are:

- exact-tag marker family pagination (`[error]: ...` vs `[error] - ...` vs plain exact tag)
- square-bracket dash-marker family pagination (`[error] - ...` vs weaker generic exact-tag competitors)
- square-bracket exact-tag family pagination (`[error] ...` vs other wrapper exact tags)
- non-marker plain-wrapper family pagination (`(error) ...` vs `{error} ...` vs `<error> ...`)

## Recommended Cases

1. `exact-tag-colon-marker-pagination`
   - cover `colon marker > dash marker > plain exact tag`
   - purpose: bring the exact-tag marker family branch into offline coverage

2. `square-bracket-dash-marker-pagination`
   - cover `square-bracket dash marker > weaker generic exact-tag noise > lower-rank plain exact tag`
   - purpose: represent the square-bracket dash-marker branch in the offline benchmark

3. `square-bracket-exact-tag-pagination`
   - cover `square-bracket exact tag > paren exact tag > tighter wrapper noise`
   - purpose: represent the square-bracket exact-tag family in the offline benchmark

4. `paren-plain-wrapper-pagination`
   - cover `paren plain exact tag > brace plain exact tag > angle plain exact tag`
   - purpose: represent the landed non-marker wrapper ordering in the offline benchmark

## Approaches Considered

### 1. Expand the fixture with four targeted marker/plain-wrapper cases (recommended)

Pros:

- closes a clear offline coverage gap without touching production code
- keeps the benchmark readable
- matches the baseline-first workflow already established in `docs/progress.md`

Cons:

- still hand-curated rather than exhaustive

### 2. Jump directly to new ranking work

Pros:

- faster path to possible behavior changes

Cons:

- weak evidence for deciding whether a new tie-break is actually needed

## Recommended Approach

Use approach 1 and expand the fixture from 16 to 20 cases with the four marker/plain-wrapper scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: a case mixes too many signals and becomes hard to audit.
  - Mitigation: derive each new case directly from a landed service-level pagination test and keep the smallest comparator set needed.
- Risk: fixture growth adds noise instead of decision value.
  - Mitigation: only add cases that cover signal families not yet present in the current 16-case baseline.
