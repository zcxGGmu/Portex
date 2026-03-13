# M7.2.3 Scheduled Tasks And Mode Inputs Design

## Goal

Complete the next documented parity slice after `M7.2.2` by:

- routing scheduled tasks through the shared `ExecutionCoordinator`
- letting non-default callers provide explicit `execution_mode` input where it already makes product sense
- keeping the policy contract narrow: explicit mode wins, otherwise default OpenAI runtime

## Scope

- add optional caller-facing `execution_mode` input to HTTP `/messages`
- add optional persisted `execution_mode` input to scheduled-task create/list contracts
- adapt scheduled-task execution from `TaskService` into `ExecutionRequest(source="scheduled")`
- map coordinator results back into the existing task-log contract without redesigning the scheduler loop

## Out Of Scope

- do not redesign `ExecutionPolicy` into a source-aware or role-aware resolver
- do not add IM-specific runtime selection controls in this slice
- do not add durable run persistence, recovery, or operator APIs
- do not change scheduler retry semantics beyond what current `TaskService` already does on success/error
- do not implement HappyClaw's broader script-task or context-mode surface

## Current Gap

Portex already has:

- `ExecutionRequest.requested_mode`
- `ExecutionCoordinator` + request-scoped backends
- WebSocket and default IM/HTTP dispatch wired through the coordinator

Portex still lacks:

- any caller that actually fills `requested_mode`
- scheduled-task execution through the coordinator
- a persisted task-level execution-mode choice

Today, `services/task_service.py` still executes the injected task executor directly, and HTTP `/messages` still cannot select `host` or `container`.

## Parity Signal From HappyClaw

HappyClaw's scheduled-task path runs through the same execution-mode decision as regular chat execution, instead of having a separate runtime stack. It also persists task-level execution metadata (`execution_type` plus group execution mode). For `M7.2.3`, Portex only needs the narrow parity essence:

- scheduled tasks should use the shared execution plane
- task and HTTP callers should be able to request `openai` / `host` / `container`

Portex should explicitly defer the rest of HappyClaw's task surface, especially script tasks and broader group/home-mode inheritance rules.

## Options Considered

### Option A: Narrow explicit-mode bridge

- add optional `execution_mode` only where there is already a clear caller contract: HTTP `/messages` and task create/list
- keep IM callers on default OpenAI mode for now
- make `TaskService` translate scheduled tasks into `ExecutionRequest`

Pros:

- matches the restart note in `docs/progress.md`
- fixes the real gap without widening policy scope
- keeps scheduler logic unchanged

Cons:

- IM still has no explicit mode override in this slice

Recommendation: choose this option.

### Option B: Full policy redesign now

- teach `ExecutionPolicy` to infer mode from source, user, group config, and legacy helpers
- update every caller at once

Pros:

- more ambitious parity story on paper

Cons:

- mixes contract cleanup with policy invention
- risks swallowing `M7.3` ownership/workspace questions

Reject.

### Option C: Add a task-only execution path

- wire scheduled tasks into execution backends directly
- leave HTTP dispatch contract unchanged

Pros:

- touches fewer route schemas immediately

Cons:

- preserves multiple execution semantics
- fails the stated `M7.2.3` goal of one rule set

Reject.

## Recommended Design

### 1. Caller-Facing Execution Mode Contract

Add one optional field:

- `execution_mode: Literal["openai", "host", "container"] | None`

Apply it to:

- `SendMessageRequest`
- `CreateTaskRequest`
- `TaskResponse`
- `ScheduledTask`

Do not add it to `UnifiedMessage`; IM normalization should remain transport-focused. Instead, let `/messages` pass the value directly into `MessageDispatchService`.

### 2. Message Dispatch Propagation

Keep `MessageDispatchService.dispatch_inbound_message()` as the single runtime-entry method for non-WebSocket callers, but add an optional `execution_mode` argument. When the service builds `ExecutionRequest`, it should copy that value into `requested_mode`.

This keeps HTTP capable of choosing `host` / `container` while IM continues using the default `None -> openai_runtime` path.

### 3. Scheduled Task Coordinator Bridge

Keep `TaskScheduler` generic and unaware of runtimes.

Instead, change `TaskService` so its default execution path:

1. builds `ExecutionRequest(source="scheduled")`
2. uses a fixed scheduler identity for `user_id`
3. copies `task.execution_mode` into `requested_mode`
4. waits for the coordinator result

This keeps the scheduler as a pure time/due-state loop while moving execution ownership into the coordinator where it belongs.

### 4. Task Log Mapping

Map coordinator results into the current task-log schema like this:

- `completed` -> log `success`
- `timeout` -> log `timeout`
- `failed` -> log `error`
- `cancelled` -> log `error` with `error="cancelled"`

To preserve current scheduler semantics, non-success outcomes should still raise after logging so the scheduler does not advance `next_run` on failed executions. That matches existing Portex behavior and avoids quietly changing retry semantics in this slice.

### 5. Legacy Helper Boundary

`services/execution_mode.py` should remain unused for now. `M7.2.3` is not the right place to resurrect group-config-driven host/container inference unless a concrete caller already provides that input.

The policy rule stays:

- explicit `requested_mode` -> mapped backend
- otherwise -> `openai_runtime`

## Data Flow

### HTTP `/messages`

1. route validates `execution_mode`
2. route normalizes inbound message
3. route calls `dispatch_inbound_message(message, execution_mode=...)`
4. dispatch service submits `ExecutionRequest(requested_mode=...)`
5. coordinator selects backend and returns result

### Scheduled Task

1. task API persists optional `execution_mode`
2. scheduler marks task due
3. `TaskService` builds `ExecutionRequest(source="scheduled", requested_mode=task.execution_mode)`
4. coordinator executes via the shared backend policy
5. task log records the normalized result

## Testing Strategy

Focused tests should cover:

- HTTP request schema and route propagation of `execution_mode`
- `ScheduledTask` model/schema carrying `execution_mode`
- `MessageDispatchService` copying explicit mode into `ExecutionRequest.requested_mode`
- `TaskService` default path submitting due tasks through the coordinator
- task-log mapping for `completed`, `timeout`, and failed coordinator results

Regression should still include:

- current execution coordinator/policy tests
- message route + dispatch focused tests
- task API and scheduler-focused tests

## Acceptance Criteria

This slice is complete when:

- `/messages` can pass `openai` / `host` / `container` into the execution plane
- scheduled tasks are executed through `ExecutionCoordinator`, not a parallel direct-runtime path
- tasks persist and expose optional `execution_mode`
- focused tests prove both mode propagation and scheduled-task coordinator execution
- `docs/progress.md` clearly records `M7.2.3` and the remaining deferred gaps
