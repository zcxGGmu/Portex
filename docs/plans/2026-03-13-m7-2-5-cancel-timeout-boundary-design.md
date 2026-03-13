# M7.2.5 Cancel Timeout Boundary Design

## Goal

Complete the next execution-plane parity slice after `M7.2.4` by hardening cancellation and timeout semantics across the real queue + executor boundary, so `cancelled` and `timeout` no longer mean only “the coordinator decided to stop”, but also imply the underlying host/container execution is still reachable for cleanup until it really exits.

## Scope

- keep the coordinator as the user-visible owner of `cancelled` and `timeout` terminal states
- make host/container backends retain real active-run handles long enough for post-cancel and post-timeout cleanup
- remove the current host-process timeout semantic split where inner executor timeout can surface as generic `failed`
- keep queue release immediate on running cancel, but continue backend cleanup in the background until the executor is gone
- preserve current WebSocket and scheduled-task outward semantics while making their underlying cleanup path more honest

## Out Of Scope

- do not add a new operator/status API or richer external state model; that remains `M7.2.6`
- do not redesign the WebSocket protocol or add a new cancel surface for scheduled tasks in this slice
- do not fully copy HappyClaw's `_interrupt` / `_close` / `closed` / `interrupted` multi-signal protocol yet
- do not redesign workspace lifecycle or execution-mode policy
- do not introduce DB-backed run persistence or process supervisors

## Current Gap

Portex already has:

- immediate queued cancel
- immediate running cancel terminal state plus best-effort background backend cancel
- coordinator-owned timeout results
- strong OpenAI-path cancellation semantics through `runtime.cancel()`

Portex still lacks:

- reliable cleanup reachability after a host/container `execute()` coroutine is cancelled
- one normalized timeout story across coordinator and host-mode executor internals
- proof that host/container timeouts stop the real child/container instead of only returning a terminal result

Today, both host and container backends remove their active process/container handles inside the `execute()` coroutine path. If the coordinator times out or cancels that coroutine first, the later `backend.cancel(run_id)` can no longer reach the underlying executor reliably.

## Parity Signal From HappyClaw

The HappyClaw behavior worth mirroring here is the layering, not the full protocol surface:

- queue release and executor cleanup are separate concerns
- soft interruption and hard stop are distinguished
- timeout is normalized as its own terminal reason, not leaked as a generic executor error
- executor cleanup continues until the real process/container is gone

Portex does not need to copy the full `_interrupt` / `_close` sentinel protocol in `M7.2.5`, but it should stop losing the real executor handle at the exact moment cleanup is still needed.

## Options Considered

### Option A: Cleanup-aware backend handles

- keep the current coordinator contract
- make host/container backends own active execution handles that survive coroutine cancellation until cleanup completes
- normalize host timeout into `timeout`

Pros:

- directly addresses the real queue/executor boundary bug
- keeps scope below `M7.2.6`
- preserves current user-visible transport semantics

Cons:

- still does not expose richer cleanup progress outside the backend

Recommendation: choose this option.

### Option B: Coordinator-only fixes

- add more state or retry logic in the coordinator
- leave backend handle ownership mostly unchanged

Pros:

- smaller-looking diff

Cons:

- cannot solve unreachable child/container cleanup after coroutine cancellation
- keeps the real bug alive under a different shape

Reject.

### Option C: Full HappyClaw signal parity now

- add explicit `interrupt`, `close`, `closed`, `interrupted`, richer recovery signals, and task/runtime-specific stop surfaces at once

Pros:

- architecturally ambitious

Cons:

- swallows `M7.2.6` state/recovery work and likely part of runner protocol redesign

Reject.

## Recommended Design

### 1. Separate Terminal Result From Cleanup Reachability

Keep the current coordinator behavior:

- queued cancel returns `cancelled` immediately
- running cancel records `cancelled` immediately and frees the queue
- timeout records `timeout` immediately

But decouple that from backend cleanup ownership:

- host/container backends must retain an active execution handle after `execute()` is cancelled
- `backend.cancel(run_id)` must still be able to stop the real process/container even if the original `execute()` coroutine was already cancelled by the coordinator

### 2. Backend-Owned Active Run Handles

For host and container backends, introduce a small internal active-run handle, for example:

- `process`
- `container_name` when applicable
- `cleanup_started`
- `cleanup_done`

The handle lifecycle should be:

1. register before awaiting the long-running subprocess
2. keep it registered if `execute()` is cancelled
3. remove it only after normal completion or explicit cleanup completion

This is the minimum needed to stop losing the executor reference at the queue boundary.

### 3. Host Timeout Normalization

Current host mode has two timeout owners:

- coordinator outer `asyncio.wait_for(...)`
- `ProcessExecutor.run_agent()` inner timeout

`M7.2.5` should collapse the semantic split:

- the execution plane should surface host timeout as `timeout`, never generic `failed`
- if the inner executor timeout still exists as a safety rail, it must map to a dedicated timeout-shaped exception/result that the backend normalizes into `timeout`

Do not leave timeout detection based only on string matching.

### 4. Container Cleanup After Outer Cancel/Timeout

`ContainerBackend.execute()` currently waits on `docker run ... process.communicate(...)`. If the coordinator cancels that coroutine, the backend must still retain:

- the host-side `docker run` process handle
- the Docker container name

Then `backend.cancel(run_id)` should:

1. attempt container stop
2. kill the local `docker run` process if still alive
3. wait briefly for cleanup completion when possible

This keeps cleanup bounded while preserving current immediate terminal-state behavior.

### 5. Keep Transport Semantics Stable

Do not widen transport contracts in this slice.

WebSocket should continue to emit:

- `run.failed` with `{"status": "cancelled"}` on cancel
- `run.timeout` on timeout

Scheduled tasks should continue to record:

- `completed -> success`
- `timeout -> timeout`
- `failed/cancelled -> error`

The point of `M7.2.5` is to make those terminal states more truthful underneath, not to redesign the user-facing payloads yet.

## Data Flow

### Running Cancel

1. coordinator marks run `cancelled`
2. coordinator frees the group queue immediately
3. original `execute()` coroutine may be cancelled
4. backend cancel uses the retained active-run handle to stop the real executor
5. backend handle is removed only after cleanup completes

### Timeout

1. coordinator timeout fires
2. coordinator requests `backend.cancel(run_id)`
3. backend cleanup uses the retained active-run handle
4. timeout result stays `timeout`
5. no host/container timeout path should degrade into generic `failed`

## Testing Strategy

Focused tests should cover:

- host/container active-run handles surviving outer cancellation long enough for `backend.cancel()` to clean them up
- coordinator timeout on host/container leading to real backend cancel calls and normalized `timeout` results
- host inner timeout mapping to `timeout` instead of `failed`
- queue release still happening immediately on running cancel
- WebSocket and scheduled-task outward semantics staying unchanged

Regression should continue to include:

- coordinator ordering/session-lifecycle tests
- execution backend adapter tests
- WebSocket integration tests
- scheduled-task service tests

## Acceptance Criteria

This slice is complete when:

- host/container cleanup remains reachable after outer coroutine cancellation
- coordinator `cancelled` / `timeout` terminal states no longer rely on already-disposed backend handles
- host timeout surfaces as `timeout`, not generic `failed`
- queue release remains immediate for running cancel
- current WebSocket and scheduled-task outward semantics remain intact
- `docs/progress.md` clearly records that `M7.2.5` hardened the queue/executor cleanup boundary, while richer external status/recovery signaling still remains for `M7.2.6`
