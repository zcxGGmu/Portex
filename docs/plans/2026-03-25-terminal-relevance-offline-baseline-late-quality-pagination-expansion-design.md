# Terminal Relevance Offline Baseline Late Quality Pagination Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 56 cases so the next uncovered later-stage quality-family pagination branches are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 56 to 60 deterministic cases
- add one delimited-log-marker pagination case
- add one exact-tag-punctuation-noise pagination case
- add one single-space plain exact-tag pagination case
- add one separator-noise pagination case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 56-case baseline already covers:

- early and mid-chain pagination through `M8.5.25`
- exact-tag wrapper delimiter quality
- early whole-word and line-start quality chains

The next obvious holes still living only in service tests are the later quality-family pagination slices:

- `M8.5.24` delimited log-marker pagination
- `M8.5.35` exact-tag punctuation-noise pagination
- `M8.5.39` single-space plain exact-tag pagination
- `M8.5.40` separator-noise pagination

These are all “quality inside a family” checks rather than new family-precedence branches, so they fit well as one coherent batch.

## Recommended Cases

1. `delimited-log-marker-pagination`
   - cover the paginated slice after delimited raw markers outrank glued markers and exact-tag wrappers

2. `exact-tag-punctuation-noise-pagination`
   - cover the paginated slice after cleaner exact tags outrank noisier exact tags and tighter wrappers

3. `single-space-plain-exact-tag-pagination`
   - cover the paginated slice after single-space exact-tag separators outrank noisier non-single-space separators

4. `separator-noise-pagination`
   - cover the paginated slice after later non-single-space noise placement outranks earlier noise under stronger-signal ties

## Approaches Considered

### 1. Expand the fixture with the four later quality-family pagination cases above (recommended)

Pros:

- keeps the batch coherent around one part of the ranking chain
- extends offline evidence deeper into already-landed quality refinements
- avoids re-adding family-precedence samples already represented elsewhere

Cons:

- leaves payloadless and later whitespace-family pagination for a later batch

### 2. Mix later quality pagination with unrelated wrapper-family pagination

Pros:

- broader apparent coverage in one batch

Cons:

- makes the batch less reviewable
- weakens the “one chain at a time” baseline-first strategy that has kept the fixture understandable

## Recommended Approach

Use approach 1 and expand the fixture from 56 to 60 cases with the four later quality-family pagination scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: later quality pagination samples could overlap with existing non-paginated quality cases.
  - Mitigation: use the service-test-derived three-entry `limit=2` / `offset=1` slices so the new evidence is specifically about pagination stability.
- Risk: batch naming could imply a broader refactor.
  - Mitigation: keep both the docs and implementation limited to fixture/test expansion only.
