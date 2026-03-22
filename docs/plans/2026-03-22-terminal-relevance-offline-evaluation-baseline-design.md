# Terminal Relevance Offline Evaluation Baseline Design

## Goal

Add a fixed, repo-local offline evaluation baseline for terminal-history `relevance` ranking so future tie-break changes can be judged against stable sample cases and explicit metrics before adding more `M8.5.x` refinements.

## Scope

- add a standalone script to run fixed terminal relevance cases and print metrics
- add a committed fixture dataset with deterministic sample transcripts and expected order
- add script-level tests that validate parsing, metrics computation, and failure signaling
- keep runtime/API/UI/RBAC/search contracts unchanged

## Out Of Scope

- no route/schema/frontend changes
- no CI workflow policy changes in this step
- no new search/ranking logic in `TerminalSessionService`
- no full-text indexing or tokenizer redesign

## Constraints

- must stay offline and deterministic
- must run from local repo without network access
- must preserve `latest.json` and `/sessions/current/history` compatibility boundaries

## Approaches Considered

### 1. Script + JSON fixture + pass/fail metrics (recommended)

Implement `scripts/evaluate_terminal_relevance.py` using a small in-memory harness around `TerminalSessionService`, driven by a committed JSON fixture containing cases and expected ordering.

Pros:

- deterministic and reviewable baseline
- easy to extend by adding fixture cases
- no production-surface changes

Cons:

- uses a lightweight local harness in script code

### 2. Encode baseline as pure pytest suite only

Treat the baseline only as tests under `tests/services/test_terminal_sessions.py`.

Pros:

- no extra script surface

Cons:

- lacks one-command operator-facing score summary
- harder to use as a pre-change benchmark report

### 3. Build a web operator benchmark page

Expose ranking benchmarks via backend API + frontend page.

Pros:

- discoverable by operators

Cons:

- out of current scope; expands API/UI surface and maintenance cost

## Recommended Approach

Use approach 1: script + committed fixture + explicit metrics and exit code behavior.

## Data Contract

Fixture file (JSON) contains:

- `version`: fixture schema version
- `cases[]`:
  - `id`: unique case identifier
  - `query`: search query
  - `entries[]`: list of terminal outputs tagged by stable `id`
  - `expected_order`: ranked list of entry IDs (best first)
  - optional `limit` / `offset`

## Metrics

For all cases:

- `case_count`
- `pass_count`
- `pass_rate`
- `top1_accuracy`
- `mrr` (mean reciprocal rank of expected top-1)

Per-case report:

- expected order
- actual order
- pass/fail
- reciprocal rank

Exit code policy:

- `0` when all cases pass
- `1` when at least one case fails or fixture is invalid

## Implementation Notes

- use a script-local fake terminal bridge (same behavior shape as tests)
- instantiate `TerminalSessionService` with deterministic `now_func`
- for each case:
  - create one session per entry
  - emit output
  - close session
  - call `search_history_by_group`
  - map session IDs back to fixture entry IDs
- compute summary metrics and render text/json output

## Verification

- focused RED->GREEN for new script tests
- run the evaluation script once against committed fixture
- run existing terminal-focused suite to guard regressions
- full backend tests + lint/build hygiene before completion

## Risks And Mitigations

- Risk: flaky ordering from timestamp collisions.
  - Mitigation: deterministic monotonic `now_func`.
- Risk: fixture drift from real ranking intent.
  - Mitigation: keep cases small, named by intent, and update alongside ranking changes.
- Risk: false confidence from too few cases.
  - Mitigation: start minimal baseline and require new cases with each future ranking refinement.
