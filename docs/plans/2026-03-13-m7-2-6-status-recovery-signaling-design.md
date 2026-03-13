# M7.2.6 Status Recovery Signaling Design

## Goal

Complete the next execution-plane parity slice after `M7.2.5` by exposing coordinator-owned execution status and minimal recovery signals through a stable read path, so run lifecycle is observable outside the current direct WebSocket stream.

## Scope

- add coordinator-owned run snapshots that track `queued/running/completed/failed/cancelled/timeout`
- expose minimal recovery signals for session-resume retry attempts in the openai lifecycle path
- add one authenticated read-only HTTP endpoint to query run status by `run_id`
- keep current WebSocket and IM/HTTP dispatch behavior stable while making status queryable
- add focused tests for snapshot transitions, recovery flags, and external status querying

## Out Of Scope

- do not build monitor pages or queue dashboards (`M7.4`)
- do not add DB-backed run persistence or restart-time recovery
- do not redesign WebSocket protocol payload families
- do not add workspace/group ownership topology changes (`M7.3`)
- do not add bulk run-list/search APIs in this slice

## Current Gap

Portex currently has run states and recovery handling inside `ExecutionCoordinator`, but no external read contract:

- run status is stored in internal maps and returned only via `wait_for_run()`/`get_status()`
- session-resume retry (`invalidate + fresh retry`) is internal and not externally visible
- routes (`/messages`, `/im`) expose completion results but not a queryable run status surface

This leaves `queued/running/timeout/cancelled/recovery` mostly hidden unless a caller is inside the active stream path.

## Options Considered

### Option A: Coordinator Snapshot + Read-Only Run Query API

- add a run snapshot DTO in coordinator
- update snapshot at submit/start/terminal/recovery points
- add `GET /executions/{run_id}` backed by coordinator snapshot

Pros:

- smallest change that closes M7.2.6 gap
- keeps transport and product surfaces stable
- easy to extend later to persistent storage

Cons:

- still in-memory only across process restarts

Recommendation: choose this option.

### Option B: Event Bus First

- emit lifecycle events into a pub/sub channel and build query from stream materialization

Pros:

- future-friendly for richer operator surfaces

Cons:

- overbuild for current milestone; pushes into M7.4 concerns

Reject.

### Option C: Full Monitor/Queue Status API Now

- include queue lengths, group-level capacity, active backend inventory, and run history listing

Pros:

- broad observability

Cons:

- scope expansion into operator surface and policy visibility

Reject.

## Recommended Design

### 1. Coordinator Run Snapshot Contract

Add a dedicated immutable-ish snapshot model (returned as copies) containing at least:

- identifiers: `run_id`, `group_folder`, `chat_jid`, `user_id`, `source`
- selection/runtime info: `requested_mode`, `backend`, `session_id`
- lifecycle info: `status`, `created_at`, `started_at`, `finished_at`
- terminal payload: `final_output`, `error`, `timeout_ms`
- recovery info: `recovery_attempted`, `recovery_reason`, `recovery_succeeded`

### 2. Snapshot Update Points

- `submit_execution()` initializes snapshot with `queued`
- `_execute_request()` marks `running` + `started_at`
- lifecycle retry branch marks recovery attempted/reason/success
- `_store_terminal_result()` writes terminal fields + `finished_at`
- retention cleanup removes stale completed snapshots with existing terminal retention policy

### 3. External Read Surface

Add an authenticated route:

- `GET /executions/{run_id}`
- returns normalized execution status response from coordinator snapshot
- returns `404` when the run is unknown/evicted

This provides one stable read path for HTTP/IM/Web callers to re-check run state.

### 4. API/Schema Integration

- add explicit response DTOs in `domain/schemas.py`
- add OpenAPI tag metadata for `executions`
- keep route-level auth at current baseline (`get_current_user`)

### 5. Recovery Signal Semantics

For this slice, “recovery signaling” means exposing whether coordinator attempted and resolved one session-resume recovery path (invalidate + fresh retry). It does not include process-restart replay or persistent replay queues.

## Data Flow

1. Caller submits execution -> coordinator creates snapshot (`queued`)
2. Worker starts run -> snapshot updates to `running`
3. If session-resume failure happens -> snapshot marks recovery attempt (+ reason), then retry outcome
4. Run reaches terminal -> coordinator stores result + updates snapshot terminal fields
5. External caller queries `/executions/{run_id}` -> receives current/terminal snapshot

## Testing Strategy

Focused tests should cover:

- snapshot transition correctness (`queued` -> `running` -> terminal)
- recovery flag correctness when retry succeeds/fails
- authenticated read endpoint happy path and 404 path

Regression should include:

- execution coordinator existing suite
- message/websocket integration suites touched by coordinator contracts
- API route/OpenAPI tests

## Acceptance Criteria

This slice is complete when:

- run status is queryable by `run_id` outside active stream consumption
- snapshot includes minimal recovery signals from coordinator lifecycle handling
- existing WebSocket/message/task flows are not behaviorally regressed
- docs/progress and tasks checklist are refreshed with fresh verification evidence
