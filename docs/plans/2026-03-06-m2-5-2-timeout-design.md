# M2.5.2 Timeout Flow Design

## Background

`M2.5.1` has already established the runtime-side cancellation primitive in `infra/runtime/openai.py`. The next step is to add service-layer timeout orchestration so long-running streamed executions can be terminated deterministically and surfaced as a stable platform event.

Current behavior:
- `services/agent_trigger.py` streams runtime events to the WebSocket broadcaster.
- There is no timeout boundary in the service layer.
- Existing stream events distinguish normal completion and runtime failure, but not service-enforced timeout.

## Goals

- Preserve HappyClaw-compatible timeout configuration semantics by treating timeout values as milliseconds.
- Keep timeout policy in the service/orchestration layer, not inside the runtime adapter.
- Emit a dedicated `run.timeout` terminal event so downstream consumers can distinguish timeout from runtime/model failure.
- Reuse the `M2.5.1` cancel path by calling `runtime.cancel(request.request_id)` when the timeout budget is exceeded.

## Non-Goals

- No frontend cancel button or timeout UI in this step.
- No changes to SDK event mapping in `infra/runtime/mapper.py`.
- No production routing changes to connect the WebSocket echo path to the runtime pipeline in this step.

## Design

### 1. Timeout boundary

`services/agent_trigger.py` will accept `timeout_ms: int = 300_000`.

Before entering `asyncio.timeout()`, the service converts to seconds:

```python
timeout_seconds = timeout_ms / 1000
```

This avoids unit ambiguity and keeps the external API aligned with HappyClaw's millisecond-based configuration.

### 2. Timeout handling

The runtime stream loop will be wrapped in `asyncio.timeout(timeout_seconds)`.

If the timeout is hit:
- call `await runtime.cancel(request.request_id)`
- broadcast a synthetic terminal event:

```python
RunEvent(
    event_type="run.timeout",
    run_id=run_id,
    payload={
        "status": "timeout",
        "timeout_ms": timeout_ms,
    },
)
```

`trigger_agent_execution()` should still return the original `run_id` after handling the timeout, rather than re-raising `asyncio.TimeoutError`.

### 3. Contract alignment

To keep the backend/frontend/platform contract consistent in the same phase:
- add `RUN_TIMEOUT = "run.timeout"` to `portex/contracts/events.py`
- add a matching contract assertion in `tests/portex/contracts/test_events.py`
- add `run.timeout` to `web/src/types/events.ts`

The frontend does not need to render the event yet, but it should recognize it as a valid stream event for `M2.5.3`.

## Testing Strategy

### Service tests

Add two tests in `tests/services/test_agent_trigger.py`:
- timeout path: long-lived runtime stream, low `timeout_ms`, assert `runtime.cancel()` is called and `run.timeout` is broadcast
- non-timeout path: stream completes before the budget expires, assert no timeout event is emitted

### Regression

Run:
- focused service tests
- full backend pytest
- `ruff check .`
- frontend lint/build to confirm the added stream event type does not break TypeScript compilation

## Risks

- The current production WebSocket route still only echoes text; timeout behavior remains covered by service-level tests until the runtime pipeline is wired into production routes.
- Adding `run.timeout` now without UI handling is intentional; consumers can safely ignore it until `M2.5.3`.

## Recommended Next Step

After `M2.5.2`, proceed to `M2.5.3` and teach the chat UI/store to treat `run.timeout` as a terminal state alongside `run.completed` and `run.failed`.
