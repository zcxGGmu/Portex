# Terminal Relevance Offline Baseline Early Whole Word Positive Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 44 cases so the remaining early whole-word and line-start-whole-word positive branches are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 44 to 48 deterministic cases
- add one direct whole-word-vs-substring priority case
- add one whole-word earliest-offset tie-break case
- add one direct line-start-whole-word-vs-mid-line-whole-word priority case
- add one line-start-whole-word earliest-offset tie-break case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 44-case baseline already covers:

- `M8.5.18` / `M8.5.19` fallback behavior when stronger whole-word or line-start-whole-word signals are absent
- later-stage marker, wrapper, whitespace-family, and brace/angle branches

The remaining obvious early-stage gaps still living only in service tests are the positive branches that make those fallback checks meaningful:

- whole-word matches outranking substring-only matches
- earlier whole-word offsets winning when whole-word counts tie
- line-start whole-word matches outranking mid-line whole-word matches
- earlier line-start whole-word offsets winning when line-start-whole-word counts tie

These cases sit earlier in the relevance chain than the later wrapper-family or whitespace refinements, so they are the highest-value non-duplicate additions.

## Recommended Cases

1. `whole-word-priority`
   - cover `error` as a whole word outranking substring-only hits such as `terror`

2. `whole-word-offset-tie-break`
   - cover earlier first whole-word offset winning when whole-word counts tie

3. `line-start-whole-word-priority`
   - cover line-start whole-word hits outranking mid-line whole-word hits

4. `line-start-whole-word-offset-tie-break`
   - cover earlier first line-start-whole-word offset winning when stronger counts tie

## Approaches Considered

### 1. Expand the fixture with four early whole-word positive cases (recommended)

Pros:

- closes the most foundational uncovered positive branches
- directly complements the already-landed no-whole-word and no-line-start-whole-word fallback cases
- stays fully baseline-first without touching production code

Cons:

- defers one remaining non-duplicate wrapper-family fallback case to a later batch

### 2. Mix whole-word positives with wrapper-family fallback cases

Pros:

- broader branch variety in one batch

Cons:

- `no delimited log marker` fallback is semantically duplicated by the existing `exact-tag-wrapper-delimiter-quality` fixture case, so a mixed batch risks spending fixture budget on redundant evidence
- produces a less coherent batch than finishing the early whole-word layer first

## Recommended Approach

Use approach 1 and expand the fixture from 44 to 48 cases with the four early whole-word positive scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: newer-created entries could win accidentally on weak recency.
  - Mitigation: use the same service-test-derived transcripts whose stronger whole-word signals already dominate recency in the landed backend tests.
- Risk: this batch could overlap semantically with existing fallback samples.
  - Mitigation: only add direct positive or same-family offset cases not already represented in the 44-case fixture.
