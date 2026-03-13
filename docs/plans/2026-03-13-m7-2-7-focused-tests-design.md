# M7.2.7 Focused Execution-Plane Tests Design

## Goal

Complete the next parity sub-step after `M7.2.6` by adding focused, behavior-level tests for queue ordering, executor selection, follow-up session behavior, cancellation, timeout, and recovery signaling so the current execution plane is locked against regressions before `M7.3`.

## Scope

- add focused tests on the coordinator for queue ordering and mixed-source serialization
- add focused tests that verify backend selection is externally observable via run snapshots
- add focused tests for cancellation edge behavior (`missing` / terminal re-cancel)
- add focused tests for recovery signaling in both retry-success and retry-failure/no-retry paths
- add focused WebSocket contract coverage for timeout terminal payload
- keep implementation changes minimal and only where tests expose real correctness gaps

## Out Of Scope

- do not introduce new execution features, APIs, or persistence models
- do not redesign WebSocket protocol families beyond existing `run.timeout` semantics
- do not expand into `M7.3` workspace/group model or `M7.4` operator dashboard surfaces
- do not replace existing broad-regression strategy with a new test harness

## Current Gap

`M7.2.1` ~ `M7.2.6` already established the execution plane and status query path, but several parity-critical behaviors are still under-asserted in focused tests:

- queue ordering tests emphasize happy-path FIFO, but do not explicitly lock “head run failed then next run still progresses”
- mixed-source (`web`/`im`/`scheduled`) same-group serialization is mostly implicit, not explicit
- backend selection is tested in policy unit tests, but less directly at coordinator run-snapshot observability level
- cancellation tests focus on queued/running behavior, but less on idempotent/terminal edge queries
- recovery tests cover retry-success; retry-failure/no-retry guardrails need explicit assertions
- WebSocket timeout event payload needs explicit focused coverage

## Option Analysis

### Option A: Focused contract tests on existing slices (recommended)

- extend existing `tests/services/test_execution_coordinator.py`
- extend existing `tests/app/routes/test_websocket_routes.py`
- keep runtime/backends unchanged unless a test exposes a defect

Pros:

- smallest diff with strongest regression value
- matches the milestone intent (`tests` first, behavior locking)
- low risk of accidental scope expansion

Cons:

- does not add new product surface, only guardrails

### Option B: Add new dedicated test modules only

Pros:

- isolates new tests from existing files

Cons:

- duplicates fixtures/stubs already present
- higher maintenance cost for no milestone-level functional gain

Reject.

### Option C: Expand into runtime instrumentation while testing

Pros:

- potentially richer diagnostics

Cons:

- scope creep into implementation and observability redesign

Reject.

## Recommended Design

### 1. Queue ordering and mixed-source serialization

Add coordinator tests that explicitly prove:

- same-group run #2 executes even when run #1 fails
- same-group requests from different `source` values remain serialized

### 2. Executor selection observability

Add coordinator tests that submit requests with explicit `requested_mode` (`host` / `container`) and assert run snapshots expose selected backend names (`host_process` / `docker_container`).

### 3. Cancellation edge semantics

Add coordinator tests for:

- cancelling unknown run returns `False`
- cancelling terminal run returns `False` (idempotent edge)

### 4. Recovery behavior guardrails

Add coordinator tests for:

- session-resume retry failure sets `recovery_attempted=True` and `recovery_succeeded=False`
- `fresh_session=True` requests do not enter resume-retry recovery signaling

### 5. Timeout transport contract

Add WebSocket route test asserting timeout terminal event stays `run.timeout` and includes `status=timeout` plus `timeout_ms`.

## Testing Strategy

Focused verification:

- coordinator-focused suite
- websocket route suite

Broader regression:

- current `M7.2` execution-plane matrix

Repository regression:

- full backend tests, `ruff`, frontend lint/build, and diff hygiene

## Acceptance Criteria

This sub-step is complete when:

- each of the six focused behavior families has explicit tests
- no existing execution-plane behavior regresses
- all focused + broader + repo regression checks pass
- `tasks/todo.md` and `docs/progress.md` are updated with fresh evidence and next step
