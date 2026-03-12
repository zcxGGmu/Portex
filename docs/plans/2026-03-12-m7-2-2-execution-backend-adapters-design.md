# M7.2.2 Execution Backend Adapters Design

## Goal

Complete the next concrete parity step after the coordinator core by:

- wrapping the current in-process, host-process, and container runner slices behind one request-scoped execution backend contract
- rewiring WebSocket and IM/HTTP message dispatch to submit work through `ExecutionCoordinator`
- keeping scheduled-task submission deferred to the next execution-plane sub-step

## Scope

- add a real `services/execution_backends.py` module for `openai_runtime`, `host_process`, and `docker_container`
- keep `ExecutionCoordinator` as the only queue/lifecycle owner
- let the OpenAI backend reuse the current runtime streaming path so WebSocket can still receive runtime events
- let host/container backends translate runner stdin/stdout behavior into `ExecutionResult`
- make the default app wiring resolve through one coordinator singleton instead of direct runtime helpers

## Out Of Scope

- do not route scheduled tasks through the coordinator yet
- do not redesign the container runner protocol
- do not add durable run persistence, recovery, dashboards, or operator APIs
- do not redesign browser chat UX or add new WebSocket event families beyond the current contract

## Current Gap

Portex already has:

- `ExecutionCoordinator` / `ExecutionPolicy`
- structured runtime results for the direct in-process path
- host runner request stdin support via `ProcessExecutor`
- container mount/environment composition via `ContainerManager`

Portex still lacks:

- a backend adapter module that turns all three execution modes into one `ExecutionBackend` contract
- runner output parsing that converts host/container stdout into `completed` / `failed` / `timeout`
- app-level wiring that makes WebSocket and IM/HTTP submit through the coordinator instead of bypassing it

## Options Considered

### Option A: Narrow adapter-first completion

- implement backends for all three modes
- rewire only WebSocket and IM/HTTP callers in this step
- defer scheduled tasks

Pros:

- matches the handoff entrypoint in `docs/progress.md`
- closes the most immediate behavior gap without swallowing the rest of `M7.2`
- keeps risk manageable because task scheduling semantics stay untouched for now

Cons:

- `M7.2` remains in progress after this slice

Recommendation: choose this option.

### Option B: Finish all remaining `M7.2` wiring in one pass

- adapters, Web/IM/HTTP rewiring, scheduled tasks, and extra status/reporting together

Pros:

- fewer intermediate commits on paper

Cons:

- mixes unrelated execution surfaces
- increases regression risk in the task subsystem
- makes verification noisier and root-cause isolation worse

Reject.

## Recommended Design

### 1. Execution Backends

Add `services/execution_backends.py` with three implementations:

- `OpenAIRuntimeBackend`
  - delegates to `run_agent_execution()`
  - accepts an optional runtime-event callback from request metadata so WebSocket keeps the current streamed event behavior
  - exposes `cancel(run_id)` through the underlying runtime
- `HostProcessBackend`
  - builds `ContainerInput`
  - calls `ProcessExecutor.run_agent()`
  - parses runner stdout into a normalized result
- `ContainerBackend`
  - builds the same `ContainerInput`
  - uses `ContainerManager` for naming, env, and volume composition
  - invokes `docker run -i --rm ...` with stdin payload and parses framed runner stdout

The backend boundary stays intentionally thin: request in, normalized execution result out, best-effort cancel.

### 2. Runner Output Parsing

Host and container runner invocations both ultimately produce `ContainerOutput` JSON.

Add parser helpers that:

- accept raw JSON or framed output (`---PORTEX_OUTPUT_START---` / `---PORTEX_OUTPUT_END---`)
- map runner `success/error/timeout` to execution `completed/failed/timeout`
- surface stderr or malformed stdout as a failed execution result instead of crashing the coordinator

This keeps `M7.2.2` focused on protocol wrapping, not protocol redesign.

### 3. Default Coordinator Wiring

Add one default coordinator factory that caches:

- `ExecutionPolicy`
- the three default backends
- one shared coordinator instance

App routes and services should depend on that factory instead of constructing their own direct runtime helpers.

### 4. WebSocket Rewiring

The WebSocket route should:

- create an `ExecutionRequest` with an event-handler callback in request metadata
- submit it through the coordinator
- use the returned `run_id` as the active socket run
- cancel through `ExecutionCoordinator.cancel()`

The OpenAI backend keeps runtime streaming intact by forwarding runtime events to the callback while the coordinator owns queueing, timeout, and terminal status.

### 5. IM / HTTP Rewiring

`MessageDispatchService` should submit an `ExecutionRequest` and await the coordinator result instead of directly calling `run_agent_execution()`.

This preserves the current message persistence and outbound reply flow while moving execution ownership under the coordinator.

### 6. Deferred Task Wiring

Scheduled tasks stay on the current executor boundary in this step.

Reason:

- the user-directed restart point is `M7.2.2`
- tasks require separate verification for log semantics and deletion/cancellation behavior
- mixing them into this slice increases the chance of breaking a stable subsystem

## Testing Strategy

Focused tests should cover:

- `OpenAIRuntimeBackend` mapping and cancel delegation
- `HostProcessBackend` parsing of success/error/malformed runner output
- `ContainerBackend` CLI arg composition, framed output parsing, and best-effort cancel
- WebSocket route submitting through the coordinator and cancelling through the coordinator path
- IM/HTTP dispatch using the coordinator-owned result instead of the direct runtime helper

Regression should still include:

- current execution coordinator core tests
- message dispatch / IM / message route focused tests
- WebSocket integration tests

## Acceptance Criteria

This step is complete when:

- `services/execution_backends.py` exists and default coordinator wiring uses it
- `app/routes/websocket.py` no longer calls `trigger_agent_execution()` directly
- default `MessageDispatchService` no longer calls `run_agent_execution()` directly
- focused tests cover all three backends plus the rewired entrypoints
- `docs/progress.md` records `M7.2.2` as complete and clearly states that scheduled tasks remain for the next step
