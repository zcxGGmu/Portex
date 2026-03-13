# M7.3.2 Workspace Topology Design

## Goal

Complete the next parity slice after `M7.3.1` by defining Portex's first real workspace topology: one canonical workspace key per folder, one canonical web workspace JID for home/main workspaces, and one consistent per-user home-workspace rule that later IM binding work can attach to.

## Scope

- keep `registered_groups` as the current persisted source of truth for workspace/chat topology
- define `folder` as the workspace key and `jid` as one chat endpoint bound to that workspace
- add explicit `is_home` semantics for Portex home/main workspaces
- introduce deterministic home-workspace creation rules for authenticated users
- make `/groups` and HTTP `/messages` understand the new canonical web home/main JIDs
- keep current coordinator/session behavior keyed by `group_folder`

## Out Of Scope

- do not add explicit IM binding metadata such as `target_main_jid`, `target_agent_id`, or reply policy; that remains `M7.3.3`
- do not redesign `GroupMemberService` into a persistent membership model; that remains `M7.3.4`
- do not add sub-agent or multi-tab workspace modeling; that remains `M7.3.5`
- do not add user-facing workspace create/update/bind APIs beyond the existing routes; that remains `M7.3.6`
- do not redesign WebSocket broadcast normalization or IM routing to merge home-folder siblings yet

## Current Gap

Portex now has a persisted `registered_groups` table and DB-backed `/groups`, but its topology is still only a temporary `chat_jid -> group_folder` registry:

- `group_folder` is the execution/workspace key in `M7.2`
- `/messages` still treats `group_id` as both `chat_jid` and `group_folder`
- authenticated users do not automatically get a personal workspace row
- there is no stable distinction between a web workspace endpoint and an IM endpoint that may later bind into the same workspace

That makes `M7.3.1` useful as a persisted list, but still not a real workspace model.

## Parity Signal From HappyClaw

The narrow parity signal worth taking now is:

- `folder` is the workspace boundary
- `jid` is an endpoint attached to that workspace
- a user has one home workspace
- some special workspace is the shared main workspace
- later IM bindings point to a canonical workspace endpoint instead of inventing new workspace identity rules

HappyClaw also carries richer binding and sub-agent metadata. Those remain later milestones.

## Portex Role Mapping Choice

HappyClaw's shared `web:main` belongs to admin users. Portex already uses the distinct roles `owner`, `admin`, and `member`.

For Portex, choose one explicit rule and stay consistent:

- `owner` users share the main workspace: `jid="web:main"`, `folder="main"`
- `admin` and `member` users get one personal home workspace: `jid="web:home-{user_id}"`, `folder="home-{user_id}"`

This intentionally does not mirror HappyClaw's mixed admin fallback behavior. It is a Portex-specific equivalent that matches the current role model.

## Options Considered

### Option A: Extend `registered_groups` with minimal home-workspace semantics

- add `is_home`
- keep `created_by`
- add home-workspace creation helpers
- keep binding metadata deferred

Pros:

- smallest change that still defines a real workspace topology
- preserves the `M7.2` execution/session model keyed by `group_folder`
- gives `M7.3.3` one stable canonical workspace endpoint to bind IM chats to later

Cons:

- still lacks explicit IM-binding metadata
- non-home visibility remains intentionally minimal

Recommendation: choose this option.

### Option B: Add separate `workspaces` and `workspace_bindings` tables now

- split endpoint rows from workspace rows immediately

Pros:

- cleaner long-term model

Cons:

- overreaches far beyond the current repo's migration/runtime boundaries
- forces a broader rewrite of `M7.2` assumptions now

Reject.

### Option C: Keep topology implicit and only document the intended rules

- add no runtime behavior yet

Pros:

- smallest code change

Cons:

- does not actually define a working Portex equivalent
- leaves `/messages` unable to target a canonical home/main web endpoint

Reject.

## Recommended Design

### 1. Keep `registered_groups` As The Topology Table

For `M7.3.2`, `registered_groups` remains the only persisted topology source.

Use the fields with these meanings:

- `jid`: one addressable chat endpoint
- `folder`: workspace identity used by execution/session lifecycle
- `created_by`: owner/creator when the workspace is user-owned
- `is_home`: whether the row is a Portex home/main workspace endpoint

No new binding columns are added yet.

### 2. Add Explicit Home-Workspace Rows

Introduce one service-level helper that ensures a user has the correct canonical workspace row:

- `owner` -> `web:main`, folder `main`, `is_home=True`
- `admin`/`member` -> `web:home-{user_id}`, folder `home-{user_id}`, `is_home=True`

Display-name rules stay intentionally small:

- shared main workspace name: `Main`
- personal workspace name: `{username} Home`

If the row already exists, the helper should preserve its original `added_at` and existing `created_by` when already set.

### 3. Make Home Visibility Deterministic

Because `registered_groups` will now contain per-user home rows, `/groups` must stop exposing every home row to every authenticated user.

For `M7.3.2`, apply one narrow visibility rule:

- include `is_home` rows only when:
  - `created_by == current_user.id`, or
  - the row is the shared main workspace and `current_user.role == "owner"`
- keep non-home rows visible with the current minimal behavior

This is enough to prevent obvious cross-user leakage without prematurely redesigning the full sharing model.

### 4. Resolve Canonical Web Targets For Home/Main Messages

HTTP `/messages` still accepts `group_id`, and the current schema uses `group_id=row.folder`.

Add one route-level resolution step before building the normalized `UnifiedMessage`:

1. ensure the authenticated user's home/main workspace exists
2. if there is a canonical web workspace row for the requested folder, use its `jid` as `chat_jid`
3. keep `group_folder` equal to the resolved row's `folder`
4. otherwise fall back to the current `group_id -> (chat_jid, group_folder)` behavior

This allows `group_id="main"` to dispatch through `chat_jid="web:main"` while keeping execution/session reuse keyed by `group_folder="main"`.

### 5. Create Home Workspaces On Registration, With Read-Path Healing

To make the topology real instead of purely lazy:

- authenticated user registration should ensure the new user's home/main workspace row exists

Also keep one idempotent healing path:

- `/groups` and `/messages` should call the same ensure helper before listing or resolving canonical web targets

That makes old users created before `M7.3.2` automatically converge without a dedicated migration route.

## Data Flow

### User Registration

1. user registers through `/auth/register`
2. auth route creates the in-memory user record
3. registry service ensures the user's canonical home/main workspace row
4. future `/groups` and `/messages` can rely on that row

### Group Listing

1. authenticated user calls `GET /groups`
2. route ensures the user's home/main workspace row exists
3. route fetches persisted rows
4. route filters out unrelated home rows
5. route returns the current summary schema using `folder` as `group_id`

### Message To A Home/Main Workspace

1. authenticated user posts `/messages` with `group_id=main` or `group_id=home-...`
2. route ensures the caller's home/main workspace row exists
3. route resolves the canonical web workspace JID for that folder
4. dispatch persists and executes with:
   - `chat_jid=web:...`
   - `group_folder=<folder>`
5. `M7.2` coordinator/session behavior remains unchanged because it still keys on `group_folder`

## Testing Strategy

Focused tests should cover:

- registry service creates member/admin home rows and shared owner main rows
- registry service can find the canonical web workspace row by folder
- `/auth/register` ensures the home/main workspace row
- `/groups` shows the caller's own home or the shared main workspace and hides unrelated home rows
- `/messages` resolves `group_id=main` or `group_id=home-...` to the canonical `web:*` `chat_jid`
- existing non-home dispatch behavior still falls back to the current `group_id` mapping

Regression should continue to cover:

- existing HTTP `/messages` dispatch wiring
- existing IM ingress wiring
- existing `M7.2` execution/session behavior

## Acceptance Criteria

This slice is complete when:

- Portex has a deterministic rule for main workspace vs per-user home workspace
- `registered_groups` can persist `is_home` rows for those workspaces
- user registration and authenticated read paths ensure the canonical home/main row exists
- `/groups` no longer exposes unrelated users' home workspaces
- HTTP `/messages` can target home/main workspaces through canonical `web:*` JIDs while preserving `group_folder` execution identity
- focused tests, full backend regression, lint, and diff hygiene all pass
- handoff docs mark `M7.3.2` complete and `M7.3.3` as the next step
