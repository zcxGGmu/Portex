# Terminal Relevance Offline Baseline Realistic Edge Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline beyond the current 8 cases so mid-chain ranking behavior is covered by more realistic marker/plain/noise/whitespace edge samples before any post-`M8.5.51` ranking change is proposed.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` from 8 to 12 deterministic cases
- add one non-square wrapper-marker family ladder case
- add one plain exact-tag single-space separator quality ladder case
- add one exact-tag punctuation-noise cleanliness case
- add one `M8.5.49` other-leading whitespace offset pagination case
- keep `scripts/evaluate_terminal_relevance.py` unchanged
- keep `tests/scripts/test_evaluate_terminal_relevance.py` aligned with the expanded case count and expected case IDs

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no changes to terminal history APIs, DTOs, UI, `latest.json`, or `/sessions/current/history`
- no new CI workflow logic
- no frontend changes

## Constraints

- every case must be repo-local, offline, deterministic, and explicitly reviewable
- case expectations must come from already-landed terminal behavior rather than speculative new semantics
- fixture expansion must preserve the current benchmark harness and failure contract

## Case Selection

Add four new cases with the highest signal-to-noise ratio relative to the existing 8-case fixture:

1. `non-square-wrapper-marker-family-ladder`
   - cover `(error): ... > {error}: ... > <error>: ... > [error] ...`
   - purpose: move non-square wrapper marker precedence into offline coverage instead of leaving it only in service tests

2. `single-space-separator-quality-ladder`
   - cover clean single-space plain exact-tag lines versus later non-single-space noise versus earlier non-single-space noise
   - purpose: exercise the `M8.5.39` + `M8.5.40` separator-quality path with equalized stronger signals

3. `exact-tag-punctuation-noise-cleanliness`
   - cover clean exact-tag output versus tighter-wrapper punctuation noise
   - purpose: bring the `M8.5.35` punctuation-noise demotion path into the offline fixture

4. `m8-5-49-other-leading-whitespace-offset-pagination`
   - cover later-vs-earlier `other-leading whitespace payload` ordering plus sliced pagination
   - purpose: add baseline coverage for the pre-`M8.5.50` fallback branch that the current 8-case fixture skips

## Approaches Considered

### 1. Expand the fixture with a few deterministic high-signal cases (recommended)

Pros:

- improves coverage without touching production ranking logic
- keeps review overhead low
- matches the current “baseline first, behavior change second” workflow

Cons:

- still limited to hand-curated samples

### 2. Add a large matrix of mechanically generated cases

Pros:

- broader combinatorial input surface

Cons:

- much harder to review and reason about
- higher risk of encoding generator mistakes as expected behavior

## Recommended Approach

Use approach 1 and extend the fixture from 8 to 12 cases with the four targeted scenarios above.

## Verification

- RED -> GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run the terminal-focused regression suite
- run full backend regression and hygiene checks

## Risks And Mitigations

- Risk: a new case accidentally encodes an unverified cross-signal ordering assumption.
  - Mitigation: derive every case from already-landed service tests or from compositions that are directly implied by those tests and verify immediately with the offline script.
- Risk: fixture growth adds low-value redundancy.
  - Mitigation: only add cases that cover signals not already present in the current 8-case baseline.
