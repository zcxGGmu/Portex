# M7.4.1 Monitor And Status Surface Design

## Goal

Complete the first `M7.4` operator-surface slice by adding a real read-only monitor/status API and a matching web page for queue state, execution snapshots, and backend/runtime health instead of relying only on `/health` plus per-run status lookups.

## Scope

- add one authenticated read-only monitor API
- expose queue state, recent run state, and minimal backend/runtime health in one payload
- add one protected `/monitor` web page
- keep the page read-only in this slice
- reuse current in-memory coordinator state instead of adding new persistence

## Out Of Scope

- do not add cancel/retry/reset controls
- do not add metrics history, charts, or time-series storage
- do not add prompt/final-output inspection to the monitor payload
- do not redesign the execution plane or persist monitor state
- do not add websocket-based monitor streaming
- do not add a settings/operator shell redesign beyond the minimal nav entry

## Current Gap

Portex now has:

- `/health` for coarse process liveness
- `/executions/{run_id}` for one run snapshot at a time
- an in-memory `ExecutionCoordinator` that already knows queued, running, and recent terminal runs
- a web app with authenticated `Chat` and `Settings` pages only

Portex still lacks:

- a single operator-facing read surface for queue and runtime state
- any page that summarizes current execution activity
- any backend contract for backend-specific health details

Today operators can only infer state indirectly or inspect one run id at a time.

## Parity Signal From HappyClaw

The useful parity signal for this milestone is narrow:

- there is one operator-visible surface for “what is the system doing now?”
- that surface shows queue/workspace activity, recent runs, and runtime/backend health
- the first version is observational, not a full control plane

HappyClaw also includes richer monitor cards, control actions, logs, and broader operational tooling. Those remain later milestones.

## Options Considered

### Option A: Backend-only monitor API

- add `GET /monitor`
- defer the page

Pros:

- smallest backend delta

Cons:

- does not satisfy the explicit `API and page` requirement in `M7.4.1`
- leaves the operator surface invisible to normal users of the web app

Reject.

### Option B: Minimal read-only operator surface

- add one aggregated API
- add one `/monitor` page
- keep it read-only

Pros:

- closes the actual parity gap without swallowing later operator/control work
- reuses the current coordinator state cleanly
- small enough to verify in one slice

Cons:

- touches backend, frontend, and route docs together

Recommendation: choose this option.

### Option C: Full operator console with control actions

- add status plus cancel/retry/reset

Pros:

- looks more complete on the surface

Cons:

- pulls execution control into the same slice
- raises new permission, audit, and failure-semantics questions
- too broad for the first `M7.4` step

Reject.

## Recommended Design

### 1. Add One Aggregated `GET /monitor` API

Introduce one read-only route:

- `GET /monitor`

This route should aggregate three areas:

- `health`
- `queue`
- `runs`

The purpose is “current operational state,” not detailed execution history.

### 2. Restrict Monitor Access To Operator Roles

`GET /monitor` should be visible only to:

- `owner`
- `admin`

Regular `member` users should receive `403`.

Reasoning:

- the monitor payload is global operational state, not one user’s own workspace view
- `M7.4.1` is an operator surface milestone, not a workspace-member reporting milestone

The frontend should mirror that rule:

- only show the `Monitor` nav entry to `owner/admin`
- direct navigation by a `member` should render a forbidden/error state after the API returns `403`

### 3. Expose Queue State By Workspace

The monitor queue section should summarize the current coordinator state by `group_folder`.

Recommended shape:

- `group_id`
- `queued_runs`
- `running_runs`
- `active_run_id`
- `active_backend`

This gives operators a stable answer to:

- which workspace is blocked or busy?
- is anything queued?
- which backend is currently active there?

This should come directly from coordinator-owned in-memory state rather than a separate database table.

### 4. Expose Recent Run Snapshots

The monitor run list should return a recent bounded list of `ExecutionRunSnapshot` summaries.

Include:

- `run_id`
- `group_id`
- `chat_jid`
- `user_id`
- `source`
- `slot_id`
- `status`
- `backend`
- `requested_mode`
- `created_at`
- `started_at`
- `finished_at`
- `error`
- `timeout_ms`
- `recovery`

Do not include:

- `prompt`
- `final_output`

This keeps the monitor surface operational instead of turning it into a message audit log or transcript browser.

The ordering should be:

- newest first by `created_at`

The initial limit can stay small and fixed, for example 50.

### 5. Expose Minimal Backend And Runtime Health

The monitor health block should supplement `/health` with backend-specific best-effort state.

Recommended top-level fields:

- `api_status`
- `version`
- `coordinator_status`
- `backends`

Each backend entry should contain:

- `backend`
- `status` in `ok | error`
- `detail`

Best-effort health rules:

- `openai_runtime`: runtime backend wiring can be constructed without raising
- `host_process`: host process executor can validate its runner path / basic local configuration
- `docker_container`: Docker client can attempt a lightweight daemon list call

Important constraint:

- one backend health failure must not make `/monitor` itself fail with `500`
- backend-specific problems stay in payload form

### 6. Add Coordinator Read Helpers Instead Of Reaching Into Private State From Routes

The route should not manually inspect coordinator private dictionaries.

Instead, add explicit read helpers on `ExecutionCoordinator`, for example:

- one method for queue/workspace summaries
- one method for recent run snapshots

This keeps monitor aggregation as a supported read-side contract rather than another route poking through internal coordinator state.

### 7. Add A Minimal `/monitor` Page

Add one protected page:

- route: `/monitor`

The page should use the existing app layout and add one new nav item:

- `Monitor`

The page layout can stay simple:

- panel 1: system health
- panel 2: queue by workspace
- panel 3: recent runs

Do not add:

- charts
- client-side filtering
- control buttons
- websocket streaming

The first version should refresh by periodic polling. A 5-second interval is sufficient for now.

### 8. Keep Failure Modes Explicit But Non-fatal

API behavior:

- unauthenticated -> `401`
- authenticated `member` -> `403`
- coordinator empty -> `200` with empty queue/run arrays
- one backend probe failure -> `200` with `status="error"` on that backend entry

Frontend behavior:

- loading -> skeleton/placeholder text
- `403` -> forbidden operator view
- network/API error -> retry-oriented error state

This keeps the operator page useful even when some runtime pieces are degraded.

## API Shape

### `GET /monitor`

Response shape:

- `health`
  - `api_status`
  - `version`
  - `coordinator_status`
  - `backends[]`
- `queue`
  - `groups[]`
- `runs`
  - `items[]`

The route should live in its own router rather than overloading `/health` or `/executions`.

Recommended tag:

- `monitor`

## Data Flow

### Backend

1. authenticated operator requests `/monitor`
2. route verifies role
3. route queries coordinator queue snapshot helper
4. route queries coordinator recent-run helper
5. route builds best-effort backend health entries
6. route returns one aggregated JSON payload

### Frontend

1. user opens `/monitor`
2. page issues `GET /monitor`
3. page renders health, queue, and runs in separate panels
4. page refreshes on a fixed interval
5. role or network errors render dedicated states

## Testing Strategy

### Backend

Focused tests should cover:

- coordinator queue snapshot helper on queued/running mixes
- recent-run snapshot ordering and bounded limit
- `/monitor` returns `401` when unauthenticated
- `/monitor` returns `403` for `member`
- `/monitor` returns `200` plus empty arrays when coordinator is idle
- `/monitor` tolerates individual backend probe failures without returning `500`
- OpenAPI documents the new route and schemas

### Frontend

For this slice, frontend verification can stay at:

- route wiring
- API client wiring
- protected navigation visibility by role
- `npm run lint`
- `npm run build`

Do not over-expand into full browser e2e for the first monitor page.

## Acceptance Criteria

This slice is complete when:

- operator roles can call `GET /monitor` and receive queue, run, and health summaries
- members cannot access the monitor API
- the coordinator exposes explicit read helpers for monitor use
- the web app exposes a protected `/monitor` page and nav item for operators
- the page shows useful read-only health, queue, and recent-run panels
- focused backend tests, broader backend regression, frontend lint/build, and diff hygiene all pass
- handoff docs move the next real parity entrypoint to `M7.4.2`
