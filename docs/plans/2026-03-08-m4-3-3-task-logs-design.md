# M4.3.3 Task Execution Logs Design

## Goal

Complete `M4.3.3` by adding the smallest useful task execution log contract for Portex, so scheduled tasks can record runnable history and authorized users can query those logs without expanding into DB recovery, FastAPI lifecycle wiring, or the real agent execution chain.

## Scope

- Add `domain/models/task_log.py` with a formal `TaskRunLog` contract
- Add task log response schemas to `domain/schemas.py`
- Add a lightweight in-memory `services/task_log_service.py`
- Extend `TaskService` so scheduler executions are wrapped with success/error log recording
- Add `GET /tasks/{task_id}/logs`
- Add focused model / service / route tests
- Update `docs/progress.md` and `docs/TODO.md`

## Out of Scope

- Do not add DB-backed task or task-log persistence
- Do not add log retention cleanup jobs
- Do not wire scheduler `start()/stop()` into FastAPI lifecycle
- Do not connect scheduled execution to `services/agent_trigger.py`
- Do not add frontend task log UI
- Do not add task pause/resume/manual-run APIs

## Design Constraints

- Current `task_service` and `TaskScheduler` remain the in-memory runtime source of truth
- Current scheduler executes through an injected async executor callback
- Current `/tasks` CRUD must remain backward-compatible
- This milestone should provide traceability even though the scheduler loop is not auto-started yet

## Design Options

### Option A: Model only

- Add `TaskRunLog` SQLAlchemy model and stop there

Pros:
- Smallest diff

Cons:
- No runtime logging behavior
- No query path to prove logs are usable

### Option B: In-memory logs + query API

- Add formal model contract
- Add an in-memory log service
- Record logs around scheduler executor calls
- Expose `GET /tasks/{task_id}/logs`

Pros:
- Delivers a usable traceability loop now
- Fits the current in-memory runtime architecture
- Leaves DB migration for a later milestone

Cons:
- Log state remains process-local

### Option C: Full DB-backed logs now

- Add repositories, persistence, and query APIs immediately

Pros:
- Closer to final target

Cons:
- Explicitly exceeds the current task-service baseline
- Pulls in persistence decisions not yet scheduled

## Recommended Design

Choose **Option B**.

This gives `M4.3` the minimum “can be tracked” capability promised by the roadmap without overreaching into persistence or runtime lifecycle orchestration.

## Data Contract

Add `domain/models/task_log.py`:

- `id: int` — autoincrement primary key
- `task_id: str`
- `run_at: datetime`
- `duration_ms: int`
- `status: str` — `success` / `error` / `timeout`
- `result: str | None`
- `error: str | None`

Keep the model aligned with `docs/TODO.md` and avoid adding extra columns in this milestone.

## Log Service Contract

Add `services/task_log_service.py` with:

- `record_log(...) -> TaskRunLog`
- `list_logs(task_id: str, limit: int = 20) -> list[TaskRunLog]`
- `reset() -> None`

Runtime rules:

- store logs in memory per task id
- order query results by `run_at` descending, then `id` descending
- clamp `limit` to a safe positive range in the route layer

## Execution Logging Contract

Extend `TaskService` so its scheduler executor is wrapped:

1. capture `run_at`
2. execute the injected task executor
3. on success, record `status="success"`
4. on exception, record `status="error"` with `error=str(exc)`, then re-raise so scheduler keeps its current failure semantics

This milestone does **not** add timeout enforcement; `timeout` remains a reserved future status.

## API Behavior

Add `GET /tasks/{task_id}/logs` under `app/routes/tasks.py`.

Authorization:

- depends on `require_permission("tasks", "read")`

Behavior:

- return `404` if the task does not exist
- accept optional `limit` query param
- default `limit=20`
- return `{ "logs": [...] }`

## Testing Strategy

Add or extend tests for:

- `TaskRunLog` model metadata/defaults
- in-memory log service ordering and limiting behavior
- task service records success and error logs when `run_pending()` is triggered
- `GET /tasks/{task_id}/logs` auth, success, limit handling, and `404`

## Files

- Create: `domain/models/task_log.py`
- Create: `services/task_log_service.py`
- Create: `tests/services/test_task_log_service.py`
- Modify: `domain/models/__init__.py`
- Modify: `domain/schemas.py`
- Modify: `services/task_service.py`
- Modify: `app/routes/tasks.py`
- Modify: `tests/domain/models/test_models.py`
- Modify: `tests/services/test_task_service.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
