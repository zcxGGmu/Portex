# M7.2 Execution Plane Parity Design

## Goal

Add the smallest honest execution plane that turns Portex from “multiple direct runtime entrypoints” into one per-group queued coordinator with backend selection, minimal session continuity, cancellation, timeout, and observable run states.

## Scope

- replace the current `services/group_queue.py` placeholder with a real per-group execution coordinator
- unify Web chat, IM/HTTP dispatch, and scheduled tasks behind one execution submission contract
- add a deterministic execution-policy boundary that selects one backend per request
- connect the current in-process runtime, host-process runner, and container runner slices through one adapter contract
- add minimal session continuity so follow-up requests for one group can reuse the same execution session identity
- expose queued/running/completed/failed/cancelled/timeout state outside the direct WebSocket stream
- add focused tests for coordinator ordering, backend selection, follow-up injection, cancellation, timeout, and status transitions

## Out Of Scope

- do not define the final workspace/group topology or ownership model; that remains `M7.3`
- do not add monitor pages, status dashboards, or operator UI; that remains `M7.4`
- do not redesign the `container/agent-runner` request/response protocol
- do not add durable DB-backed queue recovery or a full migration system
- do not rewrite the browser chat UX; only rewire its backend path
- do not expand provider-specific IM product behaviors such as cards, pairing, long-message chunking, or richer attachments

## Current State

Portex already has:

- direct WebSocket execution through `trigger_agent_execution()`
- real IM/HTTP dispatch through `MessageDispatchService`
- a minimal `run_agent_execution()` structured runtime path
- host-mode execution in `infra/exec/process.py`
- container lifecycle orchestration in `infra/exec/docker.py` and `infra/exec/container_manager.py`

Portex does not yet have:

- a real queue or lifecycle coordinator
- one submission API shared by Web/IM/tasks
- one backend contract shared by in-process/host/container execution
- minimal session state outside the current direct runtime path
- unified cancellation/timeout semantics outside direct WebSocket execution

## Options Considered

### Option A: Coordinator-first

- Introduce an in-process `ExecutionCoordinator`
- Keep state in memory for this phase
- Plug Web/IM/tasks into one submission contract
- Wrap existing execution backends behind one adapter boundary

Pros:

- directly addresses `M7.2.1` through `M7.2.7`
- keeps scope away from `M7.3`
- allows later replacement of in-memory state without discarding the public contract

Cons:

- first phase is not durable across process restarts

Recommendation: choose this option.

### Option B: Backend-first

- Fully unify host/docker/openai adapters first
- Add queueing only after backend abstraction is complete

Pros:

- can look architecturally cleaner on paper

Cons:

- delays the actual user-visible queue/lifecycle behavior
- risks over-investing in abstraction before behavior is proven

Reject.

### Option C: Persistence-first

- Build a DB-backed run/session/queue model before any coordinator

Pros:

- strongest long-term durability story

Cons:

- quickly expands into `M7.3`
- requires larger schema and ownership decisions before the behavior contract is stable

Reject.

## Recommended Design

### 1. Shared Submission Contract

Add one execution-plane request contract, for example:

- `ExecutionRequest`
- `ExecutionSource` (`web`, `im`, `scheduled`)
- `ExecutionHandle`
- `ExecutionStatus`
- `ExecutionResult`

Every entrypoint should submit work through the same coordinator API instead of directly invoking runtime helpers.

The request contract should carry only what `M7.2` actually needs:

- `group_folder`
- `chat_jid`
- `user_id`
- `prompt`
- `source`
- optional `requested_mode`
- optional `request_metadata`

Do not add final workspace ownership/binding fields here.

### 2. Per-Group ExecutionCoordinator

Add a new in-process coordinator, likely under `services/execution_coordinator.py`.

Responsibilities:

- keep one FIFO queue per `group_folder`
- allow different groups to progress independently
- ensure at most one active execution per group
- expose `submit_execution()`, `cancel()`, and `get_status()`
- create and maintain minimal run/session state
- emit status transitions for callers and tests

Suggested run-state transitions:

- `queued`
- `running`
- `completed`
- `failed`
- `cancelled`
- `timeout`

### 3. Minimal Session Continuity

`M7.2` needs session continuity, but not the final workspace model.

For now, session state should stay minimal and coordinator-owned:

- `session_id`
- `last_run_id`
- `selected_backend`
- `last_status`

Default rule:

- same `group_folder` reuses the current session unless the request explicitly asks for a fresh session

This is enough to stop every follow-up from behaving like a totally fresh trigger while still deferring `M7.3`.

### 4. ExecutionPolicy

Add a deterministic `ExecutionPolicy` boundary that chooses one backend per request.

Inputs:

- request source
- optional explicit mode
- group/workspace identifier
- maybe a small future config object

Outputs:

- backend kind (`openai_runtime`, `host_process`, `docker_container`)
- resolved session behavior

The first `M7.2` version can default most requests to the current in-process runtime while still making host/container selectable and testable.

### 5. ExecutionBackend Adapter Boundary

Wrap existing backends behind one request-scoped adapter interface.

Suggested surface:

- `submit(request) -> ExecutionResult`
- `cancel(run_id)`

The coordinator should not know backend-specific details such as Docker container names or subprocess argv.

Backends needed in `M7.2`:

- `OpenAIRuntimeBackend`
  - wraps `run_agent_execution()`
- `HostProcessBackend`
  - wraps `ProcessExecutor`
  - converts runner stdout/stderr into a structured result
- `ContainerBackend`
  - wraps `ContainerManager` + request-scoped runner invocation/result collection

The current host/container helpers are already useful, but they are not yet unified at the request/result level. `M7.2.2` is primarily about this adapter layer.

### 6. Entry-Point Wiring

Once the coordinator exists:

- WebSocket route submits `ExecutionRequest` and subscribes to status events instead of calling `trigger_agent_execution()` directly
- `MessageDispatchService` submits through the coordinator instead of directly running the current runtime
- scheduled tasks submit execution requests instead of directly awaiting a task executor

This keeps Web/IM/tasks on one execution-plane rule set.

### 7. Cancellation, Timeout, and Signals

`M7.2` must make cancellation and timeout coordinator-owned, not transport-owned.

Requirements:

- one cancel path works for Web/IM/tasks
- timeout state is recorded on the run, not only emitted as a direct WebSocket message
- callers can query status by `run_id`
- later operator APIs can consume the same state without rewriting execution flow

### 8. Task Integration

Scheduled tasks should stop “executing prompts directly”.

Instead:

- `TaskScheduler` detects due tasks
- `TaskService` adapts each task into `ExecutionRequest(source="scheduled")`
- coordinator executes it
- task logs record the resulting run outcome

This is the minimum required to stop Web/IM/tasks from having three different execution semantics.

## Data Flow

1. Caller submits `ExecutionRequest`
2. `ExecutionCoordinator` enqueues by `group_folder`
3. When head-of-line reaches execution, coordinator resolves backend via `ExecutionPolicy`
4. Coordinator reuses or creates minimal session state
5. Selected `ExecutionBackend` executes the request
6. Coordinator updates run status and result
7. Caller-specific adapter consumes status/result:
   - WebSocket broadcaster
   - IM/HTTP dispatch
   - task log service

## Testing Strategy

### Coordinator Unit Tests

Cover:

- same-group FIFO ordering
- different-group independence
- session reuse across follow-up requests
- cancellation before start
- cancellation during execution
- timeout transition
- status visibility by `run_id`

### Policy / Backend Unit Tests

Cover:

- mode-selection behavior
- in-process backend result mapping
- host-process backend result mapping
- container backend result mapping

### Integration Tests

Cover at least:

- WebSocket request now going through the coordinator
- IM/HTTP dispatch still functioning through the coordinator
- scheduled task submission entering the same contract

## Risks And Boundaries

- If the coordinator starts deciding final workspace ownership/binding semantics, it has crossed into `M7.3`
- If status/monitor APIs become a full product surface, the work has crossed into `M7.4`
- If the container runner protocol needs redesign, stop and split that work; `M7.2` should wrap the current protocol, not replace it
- In-memory coordinator state is acceptable for `M7.2`, but the design should keep a clean seam for later durable state

## Expected Deliverables

- a real `ExecutionCoordinator`
- a shared execution request/result contract
- an execution-policy boundary
- request-scoped adapters for current backends
- Web/IM/tasks all submitting through the same execution plane
- focused coordinator/backend tests and integration coverage
