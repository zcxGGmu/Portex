# M7.3.3 IM Workspace Binding Design

## Goal

Complete the next parity slice after `M7.3.2` by adding explicit IM-to-workspace binding metadata so external IM chats can either stay isolated in their own fallback workspace or be attached to one canonical Portex workspace without changing the current execution-plane identity model.

## Scope

- keep `registered_groups` as the persisted topology source for both canonical web workspaces and IM endpoints
- add one explicit binding field so an IM endpoint can point at a canonical workspace row
- keep unbound IM chats working through their existing fallback `chat-<hash>` workspace folders
- make IM dispatch resolve execution workspace from binding metadata when present
- keep outbound IM replies addressed to the original IM chat endpoint
- keep `/groups` as a workspace list instead of exposing raw IM endpoint rows

## Out Of Scope

- do not auto-bind newly seen IM chats to a user workspace
- do not add `target_agent_id`, sub-agent binding, or multi-tab session targeting; that remains later `M7.3.x`
- do not add user-facing bind/unbind management APIs; that remains `M7.3.6`
- do not redesign coordinator/session lifecycle from `M7.2`
- do not add binding health checks, auto-unbind, or orphan cleanup loops

## Current Gap

Portex now has:

- a persisted `registered_groups` table
- canonical `web:main` / `web:home-{user_id}` workspace rows
- IM ingress that can lazily register external chats
- an execution/session model keyed by `group_folder`

Portex still lacks:

- any explicit statement that an IM endpoint belongs to a canonical workspace
- any way for IM dispatch to reuse an existing canonical workspace folder instead of always using a chat-local fallback folder
- any distinction between rows that are user-facing workspaces and rows that are merely external chat endpoints

Today, an IM chat is only `jid -> chat-<hash>`, so it cannot intentionally share workspace state with a user's main or home workspace.

## Parity Signal From HappyClaw

The parity signal worth taking now is narrow:

- external IM chats can be explicitly attached to a workspace
- the binding targets the workspace's main conversation identity, not an ad-hoc folder alias
- unbound chats remain isolated until an explicit binding exists

HappyClaw also supports richer agent-level binding, health checks, and UI flows. Those are intentionally deferred.

## Options Considered

### Option A: Unbound-first binding metadata on the existing registry table

- keep one row for each IM endpoint
- add one nullable binding field that points to a canonical workspace JID
- resolve execution folder through that binding when present

Pros:

- smallest schema change that still gives explicit binding semantics
- preserves current unbound IM behavior
- avoids inventing automatic ownership rules before the product has a management surface

Cons:

- does not yet expose a user-visible bind/unbind workflow

Recommendation: choose this option.

### Option B: Auto-bind new IM chats to a default workspace

- bind on first message to `main` or a per-user home workspace

Pros:

- looks closer to the final product on the surface

Cons:

- Portex does not currently have a reliable user-ownership signal for inbound IM chats
- risks misbinding chats and leaking workspace state across users

Reject.

### Option C: Add separate `workspaces` and `bindings` tables now

- split endpoint rows from workspace rows immediately

Pros:

- cleaner long-term data model

Cons:

- overreaches the current repo's migration/runtime boundaries
- forces a broader rewrite of listing and dispatch assumptions now

Reject.

## Recommended Design

### 1. Extend `registered_groups` With One Nullable Workspace Target

Add:

- `target_workspace_jid: str | None`

Meaning:

- `None`: the IM endpoint is currently unbound
- non-`None`: the IM endpoint is explicitly attached to the canonical workspace row identified by that JID

The binding target should always be a canonical workspace JID such as:

- `web:main`
- `web:home-{user_id}`

Do not add `target_agent_id` in this slice.

### 2. Keep IM Endpoint Rows And Workspace Rows Distinct

An IM endpoint row keeps its own endpoint identity:

- `jid`: original external endpoint, for example `telegram:-3001`
- `folder`: the endpoint's fallback isolated workspace, for example `chat-abc123`

Binding does not rewrite that row's `folder`.

This is important because `/groups` currently maps rows directly to visible workspace items and does not deduplicate by folder. If a bound IM row started sharing the target workspace folder directly, the workspace list would show duplicate logical workspaces.

### 3. Resolve Execution Workspace Through Binding Metadata

When an IM message arrives:

1. ensure the IM endpoint row exists
2. read that row's `target_workspace_jid`
3. if the target exists, execute in the target workspace row's `folder`
4. otherwise, execute in the IM endpoint row's own fallback `folder`

This keeps the execution/session plane stable:

- `group_folder` remains the coordinator's workspace key
- `chat_jid` remains the original IM endpoint for transport and audit visibility

So a bound IM chat can reuse workspace session/memory state while still replying to the external chat that initiated the message.

### 4. Keep Outbound Replies Addressed To The Original IM Chat

Binding only changes which workspace folder is used for execution.

It does not change reply addressing:

- inbound IM chat JID stays the `chat_jid`
- outbound IM reply still routes to that same external JID

This avoids conflating transport identity with workspace identity.

### 5. Filter IM Endpoint Rows Out Of `/groups`

`GET /groups` should continue to behave like a workspace list, not an endpoint inventory.

For `M7.3.3`, apply one narrow rule:

- only show canonical web workspace rows in `/groups`
- do not show `telegram:*` / `feishu:*` endpoint rows

Keep the existing home/main visibility rules from `M7.3.2` on top of that.

### 6. Use Conservative Orphan Handling

If `target_workspace_jid` is set but the target workspace row cannot be found:

- treat the IM endpoint as effectively unbound for this execution
- fall back to the endpoint row's own `folder`

Do not:

- auto-clear the binding field
- auto-unbind
- add background health checks

Those belong to a later management/repair slice.

## Data Flow

### First Message From A New IM Chat

1. IM ingress normalizes the message
2. registry ensures one endpoint row exists for the external `chat_jid`
3. the new row is stored with:
   - external `jid`
   - fallback `folder`
   - `target_workspace_jid=None`
4. dispatch executes against the fallback `folder`
5. replies still go to the original IM endpoint

### Message From A Bound IM Chat

1. IM ingress normalizes the message
2. registry loads the endpoint row
3. registry resolves the bound workspace row from `target_workspace_jid`
4. dispatch submits execution with:
   - `group_folder=<bound workspace folder>`
   - `chat_jid=<original IM endpoint>`
5. coordinator/session reuse follows the bound workspace folder
6. outbound reply still routes to the original IM endpoint

### Message From An Orphaned Bound IM Chat

1. IM ingress loads the endpoint row
2. `target_workspace_jid` points to a missing workspace row
3. registry resolves no valid target
4. dispatch falls back to the endpoint row's own fallback folder
5. the binding metadata remains unchanged for now

## Testing Strategy

Focused tests should cover:

- `RegisteredGroup` exposes nullable `target_workspace_jid`
- `init_db` and runtime schema healing backfill `target_workspace_jid` on old SQLite tables
- registry service can:
  - ensure/load IM endpoint rows
  - resolve unbound IM chats to their fallback folder
  - resolve bound IM chats to the target workspace folder
  - fall back when the target workspace row is missing
- IM dispatch uses the resolved workspace folder for execution while preserving the original IM `chat_jid`
- `/groups` no longer lists raw IM endpoint rows, while existing main/home visibility still holds

Regression should continue to cover:

- current HTTP `/messages` behavior
- current execution coordinator behavior
- current IM reply routing

## Acceptance Criteria

This slice is complete when:

- Portex can persist explicit IM-to-workspace binding metadata
- unbound IM chats still execute in isolated fallback workspaces
- bound IM chats execute in the target workspace folder without changing reply addressing
- `/groups` remains a workspace list and no longer exposes raw IM endpoint rows
- old SQLite databases can be upgraded in place through the current init/runtime compatibility path
- focused tests, full backend regression, lint, and diff hygiene all pass
- handoff docs mark `M7.3.3` complete and move the next start point to `M7.3.4`
