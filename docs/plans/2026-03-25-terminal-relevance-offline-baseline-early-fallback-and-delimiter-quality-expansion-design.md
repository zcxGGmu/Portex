# Terminal Relevance Offline Baseline Early Fallback And Delimiter Quality Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 40 cases so the next uncovered early fallback and delimiter-quality behaviors are represented in the offline benchmark before any post-`M8.5.51` ranking change is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 40 to 44 deterministic cases
- add one no-whole-word fallback case derived from the landed `M8.5.18` fallback behavior
- add one no-line-start-whole-word fallback case derived from the landed `M8.5.19` fallback behavior
- add one exact-tag wrapper delimiter-quality case
- add one raw-marker delimiter-quality case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and new case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history`
- no CI workflow changes

## Why These Cases

The current 40-case baseline already covers:

- raw > wrapper > plain ladders
- marker/plain-wrapper pagination and offset tie-breaks
- non-square marker families
- brace/angle branch, fallback, and pairwise coverage
- separator-quality and whitespace-family branches
- exact-tag punctuation-noise cleanliness

The next high-signal gaps still living only in service tests are:

- fallback from `M8.5.18` whole-word signals back to `M8.5.17` concentration/span ordering
- fallback from `M8.5.19` line-start-whole-word signals back to `M8.5.18`
- delimiter quality inside raw markers
- delimiter quality inside exact-tag wrappers

These are additive branch checks rather than new ranking ideas, so they fit the current baseline-first strategy.

## Recommended Cases

1. `no-whole-word-fallback-to-m8-5-17`
   - cover the `M8.5.18` fallback path when both candidates only contain substring hits such as `terror`

2. `no-line-start-whole-word-fallback-to-m8-5-18`
   - cover the `M8.5.19` fallback path when both candidates have whole-word hits but none at line start

3. `exact-tag-wrapper-delimiter-quality`
   - cover `[error] aa` outranking `[error]aa` directly within the same wrapper family

4. `raw-marker-delimiter-quality`
   - cover `error: aa` outranking `error:aa` directly within raw markers

## Approaches Considered

### 1. Expand the fixture with the four fallback and delimiter-quality cases above (recommended)

Pros:

- follows the restart guidance in `docs/progress.md`
- captures uncovered branch behavior without touching production code
- keeps the benchmark deterministic and easy to review

Cons:

- still leaves some early positive pairwise cases for a later batch

### 2. Add direct whole-word and line-start-whole-word pairwise cases first

Pros:

- covers the earliest positive gates directly

Cons:

- skips the more fragile additive fallback contracts the restart notes call out explicitly
- delays raw-marker and exact-tag wrapper delimiter coverage again

## Recommended Approach

Use approach 1 and expand the fixture from 40 to 44 cases with the four fallback and delimiter-quality scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused regression and full backend regression
- run `ruff`, web lint/build, and `git diff --check`

## Risks And Mitigations

- Risk: fallback cases accidentally duplicate already-covered later-stage ladders.
  - Mitigation: use direct service-test-derived transcripts that only exercise the fallback boundary itself.
- Risk: delimiter-quality cases overlap with existing punctuation-noise samples.
  - Mitigation: keep the new cases same-family and pairwise so they isolate delimiter quality rather than broader wrapper-family precedence.
