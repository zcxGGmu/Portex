# Terminal Relevance Offline Baseline Direct Whitespace-Family Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 70 cases so the remaining direct whitespace-family service behaviors are represented before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 70 to 77 deterministic cases
- add direct separator-quality cases for the tab-prefixed, multi-space, and space-prefixed mixed-whitespace families
- add direct separator-offset tie-break cases for the tab-prefixed, multi-space, space-prefixed mixed-whitespace, and other-leading whitespace families
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 70-case baseline already covers the recent whitespace-family pagination and no-single-space fallback gaps:

- tab-prefixed, multi-space, and space-prefixed mixed-whitespace pagination
- tab-prefixed, multi-space, space-prefixed mixed-whitespace, and other-leading whitespace no-single-space fallback
- mixed-other direct count, mixed-other direct offset tie-break, and their pagination/fallback variants

What still has not been fixed into the offline benchmark are the remaining direct service-level whitespace-family comparisons:

- `M8.5.43` tab-prefixed payload separator-quality
- `M8.5.44` tab-prefixed payload offset tie-break
- `M8.5.45` multi-space payload separator-quality
- `M8.5.46` multi-space payload offset tie-break
- `M8.5.47` space-prefixed mixed-whitespace payload separator-quality
- `M8.5.48` space-prefixed mixed-whitespace payload offset tie-break
- `M8.5.49` other-leading whitespace payload offset tie-break

These are not duplicates of the existing pagination samples because the pagination cases only validate the paginated slice after the global ranking is already computed. They do not pin the top-of-list ordering for the direct two-entry service comparisons.

## Recommended Cases

1. `tab-prefixed-payload-separator-quality`
   - cover the direct cleaner-vs-tab-prefixed ordering for `M8.5.43`

2. `tab-prefixed-payload-offset-tie-break`
   - cover the direct later-vs-earlier separator-offset ordering for `M8.5.44`

3. `multi-space-payload-separator-quality`
   - cover the direct fewer-vs-more multi-space separator ordering for `M8.5.45`

4. `multi-space-payload-offset-tie-break`
   - cover the direct later-vs-earlier multi-space separator-offset ordering for `M8.5.46`

5. `space-prefixed-mixed-whitespace-separator-quality`
   - cover the direct cleaner-vs-noisier mixed-whitespace separator ordering for `M8.5.47`

6. `space-prefixed-mixed-whitespace-offset-tie-break`
   - cover the direct later-vs-earlier mixed-whitespace separator-offset ordering for `M8.5.48`

7. `other-leading-whitespace-offset-tie-break`
   - cover the direct later-vs-earlier other-leading whitespace separator-offset ordering for `M8.5.49`

## Approaches Considered

### 1. Add all remaining direct whitespace-family cases in one batch (recommended)

Pros:

- exhausts the known direct whitespace-family gaps cleanly
- keeps the offline baseline aligned with the full landed service-test chain
- gives the next tie-break decision a clearer stop/go point

Cons:

- slightly larger fixture bump than the recent 2-case or 4-case batches

### 2. Split direct count and direct offset gaps into separate batches

Pros:

- smaller per-batch diffs

Cons:

- prolongs the same baseline gap across multiple sessions
- adds more planning/handoff churn for one coherent remaining scope

### 3. Stop baseline expansion now and move to new ranking work

Pros:

- faster path to new behavior

Cons:

- leaves known direct service semantics unpinned in the offline harness
- weakens the baseline-first workflow that has guided the recent terminal work

## Recommended Approach

Use approach 1 and expand the fixture from 70 to 77 cases with all seven remaining direct whitespace-family scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: some direct cases may look superficially similar to the existing pagination cases.
  - Mitigation: derive each case directly from the landed two-entry service tests so the semantics stay distinct.
- Risk: restart docs could still imply more whitespace-family direct gaps remain after this batch.
  - Mitigation: update `docs/progress.md` and `AGENTS.md` to say the direct whitespace-family gaps are exhausted once this batch lands.
