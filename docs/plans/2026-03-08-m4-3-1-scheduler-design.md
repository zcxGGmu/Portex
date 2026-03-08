# M4.3.1 Scheduler Design

## Goal

Complete `M4.3.1` by introducing the smallest useful task scheduler for Portex: an async poll loop that tracks scheduled tasks in memory, detects due work for `cron` / `interval` / `once`, and delegates execution through an injected async callback.

## Scope

- Replace the current placeholder `services/scheduler.py`
- Reuse the existing `domain/models/task.py` `ScheduledTask` contract
- Add a `TaskScheduler` with:
  - in-memory task registry
  - async `start()` / `stop()`
  - one-shot `run_pending()` for tests and future orchestration
  - due-task detection for `cron` / `interval` / `once`
  - injected async `executor(task)` callback
  - duplicate-run guard for already-running task ids
- Add focused service tests for scheduling behavior
- Add `croniter` to project dependencies

## Out of Scope

- Do not implement task CRUD API in `app/routes/tasks.py`
- Do not connect the scheduler to `services/agent_trigger.py` yet
- Do not add DB persistence or DB polling for scheduler runtime state
- Do not add task execution logs in this milestone
- Do not extend `ScheduledTask` with new persistence columns yet
- Do not add frontend task UI

## Current Constraints

- `services/scheduler.py` is still a no-op placeholder
- `app/routes/tasks.py` is still a placeholder and belongs to `M4.3.2`
- `ScheduledTask` currently includes `id`, `group_folder`, `chat_jid`, `prompt`, `schedule_type`, `schedule_value`, `next_run`, `status`, `created_at`
- There is no persisted `last_run` or execution log model yet

## Design Options

### Option A: Loop skeleton only

- Add async `start()` / `stop()` and a no-op `run_pending()`
- Defer real scheduling logic

Pros:
- Lowest implementation risk

Cons:
- Too little functional value
- Guarantees more refactoring in `M4.3.2`

### Option B: Minimal usable scheduler

- Add a real `TaskScheduler`
- Keep runtime task storage in memory
- Use `next_run` as the due trigger
- Delegate work to an injected async executor

Pros:
- Delivers real scheduling behavior now
- Stays within the current architecture
- Keeps later API/DB integration straightforward

Cons:
- Runtime state is still process-local

### Option C: Scheduler + real execution pipeline

- Wire scheduler directly into message/runtime execution now

Pros:
- Closest to final workflow

Cons:
- Pulls in unrelated async lifecycle and side-effect complexity
- Exceeds the safe scope of `M4.3.1`

## Recommended Design

Choose **Option B**.

This yields a working scheduler without prematurely coupling it to the runtime execution path or task CRUD surface. The scheduler becomes a narrow, testable service that future milestones can connect to APIs and execution backends.

## Core API

Implement `TaskScheduler` in `services/scheduler.py` with:

- `upsert_task(task: ScheduledTask) -> ScheduledTask`
- `remove_task(task_id: str) -> bool`
- `list_tasks() -> list[ScheduledTask]`
- `run_pending() -> None`
- `start() -> None`
- `stop() -> None`

### Constructor dependencies

- `executor: Callable[[ScheduledTask], Awaitable[None]] | None`
- `poll_interval_seconds: float = 60.0`
- `sleep_func: Callable[[float], Awaitable[None]] | None`
- `now_func: Callable[[], datetime] | None`

These make async behavior deterministic in tests and avoid coupling to the real runtime for now.

## Scheduling Rules

### Shared due rule

- Only tasks with `status == "active"` are considered runnable
- Only tasks with non-null `next_run` are considered runnable
- A task is due when `task.next_run <= now`

### `once`

- Requires `next_run`
- When execution succeeds, mark `status = "completed"` and `next_run = None`

### `interval`

- `schedule_value` is interpreted as whole seconds
- If `next_run` is missing on upsert, initialize it to `now + interval`
- After success, advance from the prior scheduled anchor until the next timestamp is in the future

### `cron`

- `schedule_value` is a cron expression parsed by `croniter`
- If `next_run` is missing on upsert, initialize it to the next cron fire time after `now`
- After success, compute the next cron fire time after the previous scheduled anchor

## Execution Rules

- The scheduler uses an in-memory `running_task_ids` guard so the same task is not started twice concurrently
- If `executor(task)` raises, the scheduler:
  - removes the task from `running_task_ids`
  - leaves task `status` / `next_run` unchanged
  - continues processing other tasks
- `run_pending()` processes due tasks in ascending `next_run`, then `id`

## Loop Behavior

- `start()` sets `running = True` and loops:
  1. `await run_pending()`
  2. if still running, `await sleep_func(poll_interval_seconds)`
- `stop()` sets `running = False`
- This milestone keeps loop ownership local to the service and does not register lifecycle hooks in FastAPI yet

## Validation Rules

- Unsupported `schedule_type` raises `ValueError`
- Invalid interval values (non-positive or non-integer) raise `ValueError`
- Invalid cron expressions raise `ValueError`
- `once` tasks without `next_run` raise `ValueError`

## Testing Strategy

Add `tests/services/test_scheduler.py` covering:

- `once` task executes once, then becomes `completed`
- `interval` task executes when due and rolls `next_run` forward
- `cron` task executes when due and recomputes `next_run`
- inactive tasks are skipped
- future tasks are skipped
- executor failures do not crash `run_pending()` and do not mutate schedule state
- `start()` / `stop()` loop can be controlled through injected sleep
- duplicate-run guard prevents concurrent double-execution of the same task

## Files

- Create: `tests/services/test_scheduler.py`
- Modify: `services/scheduler.py`
- Modify: `pyproject.toml`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
