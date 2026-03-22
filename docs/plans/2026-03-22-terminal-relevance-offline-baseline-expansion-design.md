# Terminal Relevance Offline Baseline Expansion Design

## Goal

Expand the fixed offline terminal relevance baseline fixture so post-`M8.5.51` ranking behavior is covered by more realistic ordering chains and pagination slices before any new tie-break refinement is considered.

## Scope

- expand `tests/fixtures/terminal_relevance_baseline.json` with additional deterministic cases
- include broader ranking ladder coverage (`raw marker > wrapper marker > plain exact-tag`)
- include pagination slice coverage (`limit`/`offset`) on existing `M8.5.50` / `M8.5.51` signal paths
- keep evaluation script surface unchanged (`scripts/evaluate_terminal_relevance.py`)
- keep script tests aligned with expanded fixture size and expected metrics

## Out Of Scope

- no new ranking rules in `services/terminal_sessions.py`
- no API/route/DTO/UI/RBAC changes
- no changes to `latest.json` or `/sessions/current/history` compatibility contracts
- no CI workflow changes in this step

## Constraints

- fixture must remain repo-local, offline, and deterministic
- case IDs and expected orders must be explicit and reviewable
- baseline script must continue returning non-zero on expectation mismatch

## Approaches Considered

### 1. Expand fixture with deterministic targeted cases (recommended)

Add a small number of high-signal cases derived from already-verified service tests and preserve current metrics contract.

Pros:

- increases coverage without touching production code
- keeps interpretation simple and auditable
- aligns with current “baseline-first, then decide ranking changes” workflow

Cons:

- still limited by manually curated samples

### 2. Generate random synthetic fixtures

Auto-generate many random transcripts and compare rank invariants.

Pros:

- broader input surface

Cons:

- less deterministic and harder to review/debug
- risk of overfitting to generator assumptions

### 3. Defer expansion and only gate with existing 4 cases

Pros:

- zero additional effort now

Cons:

- too little evidence to judge future tie-break refinements safely

## Recommended Approach

Use approach 1: expand fixture with a focused set of deterministic cases that cover ranking ladder and pagination behavior on `M8.5.50`/`M8.5.51` paths.

## Verification

- RED->GREEN on `tests/scripts/test_evaluate_terminal_relevance.py`
- run `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text`
- run terminal-focused suite and full backend regression
- run lint/build hygiene checks (`ruff`, web lint/build, `git diff --check`)

## Risks And Mitigations

- Risk: fixture order assumptions drift from runtime behavior.
  - Mitigation: derive new cases from existing service-level behavior and immediately validate with script output.
- Risk: pagination baseline only checks sliced order.
  - Mitigation: keep expected full order in fixture and rely on `top1_accuracy`/`mrr` over full ranking in script logic.
