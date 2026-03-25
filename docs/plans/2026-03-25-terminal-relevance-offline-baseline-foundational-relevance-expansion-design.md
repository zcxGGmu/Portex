# Terminal Relevance Offline Baseline Foundational Relevance Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 77 cases so the remaining foundational `M8.5.17` service behaviors are represented before any new post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 77 to 81 deterministic cases
- add one clustered-vs-sparse direct ordering case
- add one first-match-offset direct tie-break case
- add one weak-recency tie-break case
- add one foundational pagination case over the global relevance ordering
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 77-case baseline now covers the later relevance family tree deeply:

- whole-word and line-start branches
- wrapper/marker families
- whitespace-family pagination, direct comparisons, and fallback branches

What still is not explicitly fixed into the offline benchmark is the original `M8.5.17` foundation that every later fallback ultimately depends on:

- concentrated matches outranking sparser matches
- earlier first-match offsets outranking later first matches when the cluster span ties
- recency acting only as a weak final tie-break
- pagination being taken from the globally ranked base result set

Some later fallback cases indirectly exercise parts of this behavior, but they do so only after newer signals have already been ruled out. That is not the same as pinning the original base ordering semantics directly.

## Recommended Cases

1. `m8-5-17-clustered-match-priority`
   - cover concentrated-vs-sparse base ordering without relying on any later whole-word or wrapper-family signals

2. `m8-5-17-first-match-offset-tie-break`
   - cover the earlier-vs-later first-match ordering when the cluster span is otherwise tied

3. `m8-5-17-weak-recency-tie-break`
   - cover the base recency fallback when the textual signals are equal

4. `m8-5-17-pagination`
   - cover the paginated slice over the globally ranked `M8.5.17` result ordering

## Approaches Considered

### 1. Add the four remaining foundational `M8.5.17` cases only (recommended)

Pros:

- closes a real early-chain baseline gap without mixing themes
- makes later fallback cases easier to interpret because the base chain is fixed explicitly
- keeps the benchmark tied to already-landed service behavior

Cons:

- adds another targeted batch before any new ranking work

### 2. Skip directly to a new ranking refinement

Pros:

- faster path to new behavior

Cons:

- leaves the foundational ranking contract under-specified in the offline harness
- makes future regressions harder to localize

### 3. Broaden the batch to include later uncovered direct/fallback cases too

Pros:

- could reduce the number of future baseline commits

Cons:

- mixes unrelated semantics into one batch
- makes it harder to tell whether the gap is in the base chain or a later refinement family

## Recommended Approach

Use approach 1 and expand the fixture from 77 to 81 cases with the four missing foundational `M8.5.17` scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: the clustered-vs-sparse case may look redundant with later no-whole-word fallback coverage.
  - Mitigation: keep the transcript rooted in the original `M8.5.17` service tests so it fixes the base-chain contract directly.
- Risk: restart docs may still imply the baseline has no uncovered gaps left.
  - Mitigation: update `docs/progress.md` and `AGENTS.md` to distinguish “whitespace-family direct gaps are done” from “foundational base ranking cases are now being fixed.”
