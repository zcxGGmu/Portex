# M7.2.4 Session Workspace Lifecycle Design

## Goal

Complete the next parity slice after `M7.2.3` by replacing Portex's nominal `group_folder -> session_id` reuse with a minimal, coordinator-owned workspace/session lifecycle that lets follow-up turns reuse a real execution session instead of always behaving like fresh stateless triggers.

## Scope

- add an explicit in-memory workspace/session lifecycle boundary owned by the execution coordinator
- keep `group_folder` as the current workspace key and make that rule explicit
- make `openai_runtime` actually consume the resolved session lifecycle through the OpenAI Agents SDK session interface
- preserve success-only session updates so failed runs do not overwrite the last good workspace session
- add one automatic recovery path for session-resume failure: invalidate the stale session and retry fresh once
- keep host/container execution on the same lifecycle contract without claiming full long-lived follow-up parity for those backends yet

## Out Of Scope

- do not add a DB-backed workspace/session model or expand `domain/models/session.py` into a real persistence layer
- do not add new HTTP/WebSocket APIs for reset/rebind/workspace management
- do not redefine the final workspace/home/sub-session topology; that remains `M7.3`
- do not redesign `ExecutionPolicy`, task contracts, or WebSocket payloads in this slice
- do not make host/container execution fully stateful or long-lived; only the contract should be ready for that later

## Current Gap

Portex already has:

- one per-group execution coordinator
- minimal session-id string reuse in `ExecutionCoordinator`
- request-scoped backends for `openai_runtime`, `host_process`, and `docker_container`

Portex still lacks:

- an explicit workspace/session lifecycle abstraction
- any backend that turns the reused `session_id` into real follow-up continuity
- success-only session commit rules owned by a dedicated lifecycle boundary
- any recovery behavior when a stale session can no longer be resumed

Today, `openai_runtime` ignores `RunRequest.session_id`, and host/container only forward the string into payload/env/container naming. In practice, follow-up turns still execute like fresh runs.

## Parity Signal From HappyClaw

The HappyClaw behavior worth mirroring here is narrow but important:

- workspace identity is keyed by `group_folder`
- follow-up turns reuse a persisted session attached to that workspace
- only successful outputs update the current session binding
- stale session resume failures trigger session invalidation and a fresh retry path

HappyClaw also has reset APIs, sub-agent session partitions, and broader workspace binding rules, but those belong to later milestones.

## Options Considered

### Option A: Coordinator-owned lifecycle plus real OpenAI session persistence

- add a minimal workspace/session store keyed by `group_folder`
- keep lifecycle state in memory for now
- wire `openai_runtime` to the Agents SDK `Session` interface so reused session IDs actually carry history

Pros:

- solves the real follow-up gap without crossing into `M7.3`
- keeps lifecycle ownership in one place instead of spreading it across routes and backends
- gives one honest parity win in the default runtime path immediately

Cons:

- host/container still do not get full session continuity in this slice

Recommendation: choose this option.

### Option B: Keep improving the coordinator's raw `_session_ids` map

- retain the current implicit lifecycle
- only add more bookkeeping around session-id strings

Pros:

- smallest short-term diff

Cons:

- still does not create real follow-up continuity
- keeps lifecycle semantics hidden inside coordinator internals

Reject.

### Option C: Jump directly to a persistent workspace/session database layer

- promote `domain/models/session.py` into the source of truth now
- add storage-backed lifecycle before behavior is proven

Pros:

- strongest long-term persistence story

Cons:

- drags in `M7.3` ownership and topology decisions immediately
- much larger blast radius than this slice needs

Reject.

## Recommended Design

### 1. Explicit Workspace Lifecycle Boundary

Add a new service module, for example `services/workspace_lifecycle.py`, with two narrow responsibilities:

- `WorkspaceResolver`: resolve one execution request to one workspace key
- `WorkspaceSessionStore`: hold the minimal mutable session lifecycle state for that workspace

For `M7.2.4`, `WorkspaceResolver` should simply return `request.group_folder`. The point is not to invent a richer topology now; it is to stop burying workspace identity inside coordinator implementation details.

### 2. Minimal WorkspaceSessionState

The in-memory store should hold only the fields needed for this phase:

- `workspace_key`
- `session_id`
- `backend`
- `generation`

`generation` exists only to mint deterministic fresh session IDs after reset/rotation without depending on ad-hoc coordinator state.

The store should support four lifecycle operations:

- preview or allocate the next session ID for one workspace/backend request
- commit a successful session as the current one
- invalidate the current session after a proven resume failure
- inspect the current lifecycle state in tests

### 3. Real Session Persistence In The OpenAI Runtime Path

`infra/runtime/openai.py` should stop ignoring `RunRequest.session_id`.

Instead, it should create an Agents SDK `SQLiteSession` bound to:

- session id: the coordinator-resolved workspace session ID
- db path: a stable file under `data/sessions/{group_folder}/`

Then `Runner.run_streamed(...)` should receive that session object. This is the key step that turns follow-up runs into actual continuation for the default backend.

The runtime should not invent session IDs. It should only consume the lifecycle already resolved by the coordinator.

### 4. Success-Only Session Commit

The lifecycle rule should be:

- reuse the current workspace session when backend is still `openai_runtime` and the caller did not request `fresh_session`
- mint a fresh session candidate when the caller sets `fresh_session=True`
- commit the candidate as current only after a successful run
- failed, cancelled, or timed-out runs must not overwrite the last good committed session

This preserves a working conversation after failed retries and mirrors the HappyClaw “only update session on trusted success” behavior.

### 5. Session Resume Recovery

Add one explicit recovery path for the default OpenAI backend:

1. backend attempts execution with the committed workspace session
2. if the runtime reports a session-resume failure
3. coordinator invalidates the workspace session
4. coordinator retries once with a fresh session

If the fresh retry also fails, the run should fail normally. This keeps recovery deterministic and bounded.

### 6. Host/Container Contract In This Slice

Host/container should continue to receive a resolved `session_id` value through the existing backend contract, but `M7.2.4` should not claim real follow-up continuity there yet.

For now:

- the lifecycle boundary remains backend-neutral
- host/container execution stays effectively stateless
- future work can teach those backends to persist or resume execution without changing the coordinator contract again

That keeps this slice honest while still preparing the right abstraction boundary.

## Data Flow

### Follow-Up Run On OpenAI Runtime

1. caller submits `ExecutionRequest(group_folder=...)`
2. coordinator resolves `workspace_key = group_folder`
3. workspace session store returns the current or fresh candidate session ID
4. `OpenAIRuntimeBackend` passes that session ID into the runtime request
5. `OpenAIAgentsRuntime` creates a persistent Agents SDK `SQLiteSession`
6. runner executes against that session-backed history
7. coordinator commits the session only if the run completes successfully

### Resume-Failure Recovery

1. coordinator selects the committed session ID
2. runtime/backend reports a session-resume failure
3. coordinator invalidates the current workspace session
4. coordinator retries once with a fresh candidate session ID
5. success commits the new session; failure returns a normal failed result

## Testing Strategy

Focused tests should cover:

- workspace lifecycle store state transitions
- coordinator success-only session commit behavior
- `fresh_session=True` creating a new committed session only on success
- stale-session resume failure invalidating and retrying fresh once
- `OpenAIAgentsRuntime` passing a real Agents SDK session object into `Runner.run_streamed`
- stable session DB path creation under `data/sessions/{group_folder}/`

Regression should continue to cover:

- current coordinator ordering/cancellation/timeout semantics
- execution backend adapters
- message dispatch and scheduled-task entrypoints that already rely on the coordinator

## Acceptance Criteria

This slice is complete when:

- the coordinator owns an explicit workspace/session lifecycle abstraction instead of a raw `_session_ids` dict
- the default `openai_runtime` path consumes `session_id` through the Agents SDK session interface
- two follow-up runs in the same workspace can reuse a real persisted session
- failed or cancelled runs do not overwrite the last good committed session
- a stale-session resume failure triggers one invalidate-and-fresh-retry path
- `docs/progress.md` clearly records that `M7.2.4` gives real session continuity to the OpenAI path while host/container continuity remains deferred
