# M7.3.1 Persisted Group Listing Design

## Goal

Complete the next parity slice after `M7.2.7` by replacing Portex's hard-coded `group-demo` list with a real persisted workspace/group registry and by letting the current message dispatch path lazily register resolved targets into that registry.

## Scope

- turn `domain.models.group.RegisteredGroup` into the current source of truth for group/workspace listing
- replace `GET /groups` hard-coded output with a DB-backed listing path
- add one minimal runtime registration hook so HTTP and IM dispatch can persist newly seen targets without a new management API
- keep the current temporary `chat_jid -> group_folder` rule, but isolate the persistence logic so later `M7.3.x` work can replace the resolver cleanly
- keep the existing `group_id/name` response contract for the group list route

## Out Of Scope

- do not define the final HappyClaw-style home workspace / main workspace model; that remains `M7.3.2`
- do not add explicit binding metadata such as `target_main_jid`, `target_agent_id`, or reply-policy routing; that remains `M7.3.3`
- do not persist or redesign the current `GroupMemberService`; that remains `M7.3.4`
- do not add sub-agent or multi-session-tab modeling; that remains `M7.3.5`
- do not add user-facing create/update/bind workspace APIs; that remains `M7.3.6`
- do not redesign coordinator/session lifecycle behavior from `M7.2`; the coordinator should keep consuming `group_folder` as-is

## Current Gap

Portex already has:

- a `RegisteredGroup` SQLAlchemy model with `jid/name/folder/added_at/created_by`
- a real execution plane keyed by `group_folder`
- current HTTP and IM ingress paths that can already resolve one execution target per inbound message

Portex still lacks:

- any runtime read/write path for `registered_groups`
- a real `/groups` listing backed by persisted rows
- any minimal bridge that writes resolved runtime targets into the registry

Today, `/groups` always returns `group-demo`, while actual message execution may already use other `group_folder` values that never appear in the listing model.

## Parity Signal From HappyClaw

The HappyClaw behavior worth mirroring here is the narrow foundation layer:

- one persisted registered-group registry
- one separation between chat identity (`jid`) and workspace folder (`folder`)
- one route/view layer that reads from that registry instead of inventing demo output

HappyClaw also has home workspaces, bound chats, shared folders, and richer access semantics, but those are later milestones and should not be swallowed into `M7.3.1`.

## Options Considered

### Option A: DB-backed registry plus lazy auto-registration on current dispatch paths

- add a small async service around `RegisteredGroup`
- make `/groups` read from that service
- let current dispatch code register resolved targets on first use

Pros:

- produces a real persisted list instead of a hard-coded demo response
- keeps the current resolver rules intact while making them observable
- gives the product a usable source of truth before `M7.3.2` / `M7.3.3`

Cons:

- name/visibility semantics remain intentionally minimal for now

Recommendation: choose this option.

### Option B: Only switch `/groups` from hard-coded data to direct DB reads

- add a DB reader but no write path

Pros:

- smallest route diff

Cons:

- registry will usually stay empty because nothing writes to it yet
- produces a technically persisted list that is not meaningfully reachable through the product

Reject.

### Option C: Jump directly to a full workspace/home/binding model

- add ownership, home workspaces, IM bindings, and richer APIs now

Pros:

- stronger long-term parity story

Cons:

- clearly crosses into `M7.3.2` through `M7.3.6`
- much larger blast radius than this slice needs

Reject.

## Recommended Design

### 1. Add A Narrow Registry Service

Add a new service module, for example `services/group_registry.py`, that owns two responsibilities:

- list registered groups in a deterministic order
- idempotently ensure one `RegisteredGroup` row exists for a resolved target

The service should stay intentionally thin and async, using the current `AsyncSession` style already present in the codebase.

### 2. Keep One Minimal Data Shape

For `M7.3.1`, the registry service only needs the existing model fields:

- `jid`
- `name`
- `folder`
- `added_at`
- `created_by`

Do not grow the table for home/binding metadata in this slice.

### 3. Make `/groups` Read The Registry

`GET /groups` should stop returning hard-coded demo data and instead:

1. resolve the DB-backed registry service
2. fetch registered rows
3. map each row to the existing `GroupSummaryResponse(group_id=row.folder, name=row.name)`

The current response schema can stay unchanged so the rest of the app does not need a coordinated API expansion yet.

### 4. Lazily Register Resolved Targets

The current runtime already resolves a target before persistence and execution.

Add one optional registration callback into `MessageDispatchService`:

- once a target is resolved
- before message persistence/execution proceeds
- call the registry service to ensure the target exists

Registration rules for this slice:

- `jid` is the current `chat_jid`
- `folder` is the resolved `group_folder`
- `name` is a minimal display string derived from the current target
- `created_by` is only set for authenticated web-originated messages; IM-originated rows may leave it empty

This preserves the current one-to-one temporary resolver rule without pretending that the final binding model already exists.

### 5. Keep Resolver Semantics Stable

Do not rewrite target resolution in this milestone.

For now:

- HTTP `/messages` may still send `group_id` as both `chat_jid` and `group_folder`
- IM ingress may still derive `group_folder` from `chat_jid`
- the coordinator may still treat `group_folder` as the workspace key

The new behavior is only that resolved targets become persisted registry rows instead of disappearing after execution.

## Data Flow

### Group Listing

1. user calls `GET /groups`
2. route resolves the registry service
3. registry service reads `registered_groups`
4. route returns `folder + name` summaries

### First Message Into A New Target

1. caller submits HTTP or IM message
2. dispatch resolves `ResolvedMessageTarget(group_folder, chat_jid)`
3. dispatch calls the registry ensure hook
4. registry inserts the row if it does not already exist
5. dispatch continues with message persistence and execution
6. subsequent `GET /groups` includes that target

## Testing Strategy

Focused tests should cover:

- registry service inserts one new row and reuses an existing row idempotently
- registry listing returns deterministic results from persisted rows
- `/groups` reads registry output instead of hard-coded demo data
- message dispatch calls the registry hook for both explicit and resolver-derived targets

Regression should continue to cover:

- current HTTP `/messages` dispatch wiring
- current IM ingress wiring
- current execution coordinator behavior

## Acceptance Criteria

This slice is complete when:

- `GET /groups` no longer contains hard-coded `group-demo`
- `RegisteredGroup` has a real service-level read/write path in the runtime
- the default dispatch path can lazily persist newly seen targets into `registered_groups`
- focused tests and a full backend regression pass
- handoff docs clearly mark `M7.3.1` complete and `M7.3.2` as the next step
