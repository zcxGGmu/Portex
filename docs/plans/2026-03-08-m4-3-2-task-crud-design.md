# M4.3.2 Task CRUD API Design

## Goal

Complete `M4.3.2` by adding the smallest useful `/tasks` CRUD API around the existing in-memory `TaskScheduler`, so authenticated users can create, list, and delete scheduled tasks without expanding into DB persistence, execution logs, or real runtime wiring.

## Scope

- Extend `domain/schemas.py` with task request/response payloads
- Add a lightweight `services/task_service.py` that wraps a singleton `TaskScheduler`
- Implement:
  - `POST /tasks`
  - `GET /tasks`
  - `DELETE /tasks/{task_id}`
- Wire the task router into `app/main.py`
- Add focused service and API tests
- Update `docs/progress.md` and `docs/TODO.md`

## Out of Scope

- Do not add DB-backed task persistence or restart recovery
- Do not add task execution logs
- Do not wire scheduled execution into `services/agent_trigger.py`
- Do not add task update, pause, resume, or manual execute APIs
- Do not add frontend task UI
- Do not expand role/permission behavior beyond the existing static `tasks` templates

## Design Constraints

- `services/scheduler.py` is already complete for `M4.3.1` and must remain the runtime source of truth for scheduled tasks in this milestone
- `domain/models/task.py` `ScheduledTask` remains the task contract
- `M4.3.2` must keep task state process-local and in-memory only
- Current auth is still backed by the in-memory `AuthService`
- Existing permission templates already define:
  - `owner`: `tasks` read/write/execute
  - `admin`: `tasks` read/write/execute
  - `member`: `tasks` read

## Design Options

### Option A: Routes talk directly to `TaskScheduler`

- Keep all creation, validation, and serialization logic inside `app/routes/tasks.py`

Pros:
- Fewest files

Cons:
- Makes route logic noisy
- Harder to reset state cleanly in tests
- Pushes ID generation and task construction into the HTTP layer

### Option B: Thin task service over scheduler

- Add a small `TaskService` that owns a singleton `TaskScheduler`
- Keep routes responsible only for auth, permission checks, and HTTP mapping

Pros:
- Smallest clean boundary
- Easy test reset hook
- Reuses scheduler as-is without leaking its details into routes

Cons:
- Adds one extra file

### Option C: DB-backed CRUD now

- Introduce repositories and persistence-backed task management immediately

Pros:
- Closer to final architecture

Cons:
- Explicitly exceeds `M4.3.2`
- Pulls in unrelated lifecycle and recovery decisions

## Recommended Design

Choose **Option B**.

This keeps the milestone narrow while avoiding direct scheduler coupling inside the route layer. The task service stays intentionally thin: build a `ScheduledTask`, delegate validation/storage to `TaskScheduler`, and expose list/delete/reset operations for routes and tests.

## Data Contract

### Request schema

Add `CreateTaskRequest` with:

- `group_folder: str`
- `chat_jid: str`
- `prompt: str`
- `schedule_type: Literal["cron", "interval", "once"]`
- `schedule_value: str | None = None`
- `next_run: datetime | None = None`

### Response schemas

Add:

- `TaskResponse`
  - `id`
  - `group_folder`
  - `chat_jid`
  - `prompt`
  - `schedule_type`
  - `schedule_value`
  - `next_run`
  - `status`
  - `created_at`
- `TaskListResponse`
  - `tasks: list[TaskResponse]`
- `DeleteTaskResponse`
  - `status: str`

## Validation Rules

- `once`
  - requires `next_run`
  - must not provide a meaningful `schedule_value`
- `interval`
  - requires `schedule_value`
  - `schedule_value` must parse as a positive integer number of seconds
  - `next_run` is optional; if absent, scheduler initializes it
- `cron`
  - requires non-empty `schedule_value`
  - `schedule_value` must be parseable by `croniter`
  - `next_run` is optional; if absent, scheduler initializes it

Route/service behavior should convert invalid task payloads into `400`.

## Service Contract

Add `services/task_service.py` with a singleton `task_service`.

### Public methods

- `create_task(...) -> ScheduledTask`
- `list_tasks() -> list[ScheduledTask]`
- `delete_task(task_id: str) -> bool`
- `reset() -> None`

### Runtime rules

- Generate `task.id` with a stable `task-<hex>` format
- Default task status to `active`
- Delegate schedule validation and `next_run` initialization to `TaskScheduler.upsert_task()`
- Return list output in scheduler order
- `reset()` recreates the scheduler so tests do not leak state

## API Behavior

Implement under `app/routes/tasks.py`:

- `POST /tasks`
- `GET /tasks`
- `DELETE /tasks/{task_id}`

### Authorization

- `POST /tasks` depends on `require_permission("tasks", "write")`
- `GET /tasks` depends on `require_permission("tasks", "read")`
- `DELETE /tasks/{task_id}` depends on `require_permission("tasks", "write")`

### Response / error behavior

- `POST` returns the created task payload
- `GET` returns all current in-memory tasks
- `DELETE` returns `{"status": "removed"}`
- deleting a missing task returns `404`
- invalid schedule payload returns `400`
- missing or invalid auth remains `401`
- insufficient role permission remains `403`

## Testing Strategy

Add or extend focused tests for:

- task service create/list/delete behavior
- scheduler-backed initialization for `interval` / `cron`
- `POST /tasks` success for write-capable users
- `GET /tasks` success for read-capable users
- member cannot create/delete tasks
- invalid task payload returns `400`
- deleting a missing task returns `404`
- task routes require authentication

## Files

- Create: `services/task_service.py`
- Create: `tests/services/test_task_service.py`
- Modify: `domain/schemas.py`
- Modify: `app/routes/tasks.py`
- Modify: `app/main.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
