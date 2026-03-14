# M7.3.4 Workspace Membership Design

## Goal

Complete the next parity slice after `M7.3.3` by turning the current placeholder group-member layer into a real workspace membership model that controls visibility and access for shared workspaces without prematurely expanding into workspace-management APIs or frontend transport rewiring.

## Scope

- keep `registered_groups` as the persisted workspace and IM endpoint registry
- promote `group_members` into the persistent source of truth for shared workspace membership
- bind membership to `group_folder`, not to one specific `jid`
- keep `is_home=True` workspaces private and non-shareable
- let non-home canonical `web:*` workspaces be shared through membership
- apply membership-aware access checks to workspace listing, member management, HTTP message dispatch, and execution-status reads

## Out Of Scope

- do not add workspace create/update/bind APIs; that remains `M7.3.6`
- do not add sub-agent or multi-tab data model changes; that remains `M7.3.5`
- do not rework the current WebSocket transport or add authenticated `/ws/{group_folder}` access control in this slice
- do not change the current IM ingress execution ownership model from `M7.3.3`
- do not redesign execution coordinator, workspace lifecycle, or runtime backend selection from `M7.2`

## Current Gap

Portex now has:

- a persisted `registered_groups` table with canonical `web:main`, `web:home-{user_id}`, and IM endpoint rows
- execution and session identity keyed by `group_folder`
- minimal member CRUD routes from `M4.2.3`

Portex still lacks:

- any persistent runtime source of truth for shared workspace membership
- any linkage between member records and canonical workspace folders
- any consistent access model for "who can see this workspace", "who can send to it", and "who can read runs from it"

Today, `GroupMember` exists mainly as a formal model while `group_member_service` is still an in-memory CRUD store keyed by route-facing `group_id`. That is not enough to represent a real shared working session.

## Parity Signal From HappyClaw

The parity signal worth taking now is still narrow:

- memberships belong to the shared workspace folder
- home workspaces remain private
- ordinary workspaces can be shared with additional users
- membership drives visibility and access, not just a standalone CRUD screen

HappyClaw also includes broader workspace CRUD, search UX, pinned groups, sub-agents, and authenticated transport boundaries. Those remain later milestones.

## Options Considered

### Option A: Only make `GroupMemberService` DB-backed

- replace the in-memory store with database persistence
- leave listing, dispatch, and execution-status access rules mostly unchanged

Pros:

- smallest code change
- low short-term risk

Cons:

- still does not represent a real working-session membership boundary
- leaves membership disconnected from workspace visibility and execution access

Reject.

### Option B: Promote membership to the real workspace access boundary

- persist membership by `group_folder`
- use membership to answer visibility and access questions for shared workspaces
- keep home workspaces private and keep workspace-management APIs deferred

Pros:

- closes the actual parity gap without swallowing later API work
- matches the current execution-plane identity model keyed by `group_folder`
- keeps the data model narrow and compatible with `M7.3.2` and `M7.3.3`

Cons:

- requires touching multiple route boundaries in one slice

Recommendation: choose this option.

### Option C: Skip directly to full workspace CRUD plus membership plus IM binding management

- fold `M7.3.4` and `M7.3.6` together

Pros:

- fewer intermediate steps

Cons:

- scope becomes too large
- harder to verify and review
- mixes access-model work with management-surface work

Reject.

## Recommended Design

### 1. Keep Two Distinct Responsibilities

Keep:

- `registered_groups` as the workspace and IM endpoint registry
- `group_members` as the workspace membership table

Do not overload `registered_groups` with member lists, and do not duplicate ownership metadata into `group_members` when `created_by` already captures workspace ownership.

### 2. Key Membership By `group_folder`

Membership should belong to the execution workspace identity:

- `group_folder`
- `user_id`

This aligns with:

- execution coordinator queue identity
- workspace lifecycle session identity
- current canonical workspace topology
- IM binding resolution from `M7.3.3`

The effect is deliberate: all JIDs that resolve to the same workspace folder share one member list and one execution context.

### 3. Home Workspaces Stay Private

For any workspace with `is_home=True`:

- it is visible only to its owner
- member-management APIs are not allowed
- no extra members can be added

This preserves the `M7.3.2` home/main topology semantics and avoids turning user home workspaces into shared rooms accidentally.

### 4. Shared Membership Applies Only To Non-Home Canonical Web Workspaces

Only non-home canonical `web:*` rows participate in user-managed sharing.

Access rules:

- owner (`created_by`) can always access and manage the workspace
- listed members can access the workspace
- non-members cannot access it

Raw IM endpoint rows are not independently shared. If an IM endpoint is bound to a workspace, it inherits that workspace's access model on Web/HTTP/read surfaces.

### 5. Normalize Route Access Through Canonical Workspace Resolution

Routes should stop treating arbitrary `group_id` strings as their own access boundary.

Instead:

1. resolve the incoming route target to the canonical workspace row when possible
2. evaluate owner/member access against that workspace's `folder`
3. use the resolved `group_folder` as the execution and membership identity

This is especially important for:

- `/groups`
- `/groups/{group_id}/members`
- `/messages`
- `/executions/{run_id}`

### 6. Keep IM Ingress Semantics Stable

`M7.3.4` should not change the inbound IM dispatch behavior established in `M7.3.3`.

That means:

- IM ingress still resolves execution workspace by endpoint binding metadata
- outbound replies still use the original IM `chat_jid`
- membership inheritance only affects workspace visibility and read-side access on authenticated Web/HTTP surfaces

Do not introduce IM-side membership checks or ownership rewrites here.

## Data Model Changes

### `group_members`

Keep the table narrow and explicit:

- `group_folder`
- `user_id`
- `role`
- `joined_at`
- `added_by`

Primary identity:

- `(group_folder, user_id)`

Compatibility path:

- old SQLite tables that still expose `group_jid` should be backfilled or read through a compatibility layer
- runtime schema self-healing should handle the minimal column additions without a dedicated migration system

### Roles

Keep the role set narrow:

- `owner`
- `admin`
- `member`

But keep owner special:

- owner cannot be transferred through normal member updates
- owner cannot be removed

The practical shared-workspace path for this slice is still owner + member access control; role persistence stays future-compatible without forcing new permission rules now.

## Route Behavior

### `/groups`

Return only canonical web workspaces visible to the current user.

Rules:

- show the user's own home workspace
- show non-home `web:*` workspaces they created
- show non-home `web:*` workspaces where they are a member
- continue hiding raw `telegram:*` / `feishu:*` endpoint rows

### `/groups/{group_id}/members`

Resolve `group_id` to the canonical workspace first.

Rules:

- missing or inaccessible workspace -> `404`
- home workspace member management -> `400`
- list members requires workspace access
- add/remove members requires workspace owner
- self-removal is allowed for non-owner members
- owner removal or owner transfer remains unsupported -> `400`

### `POST /messages`

Resolve the target workspace before dispatch.

Rules:

- canonical workspace hit -> enforce workspace access, then dispatch into its `group_folder`
- fallback legacy `group_id` path remains for non-registry targets, but it does not participate in shared-workspace membership semantics
- inaccessible canonical workspace -> `404`

This lets shared members participate in the same execution/session context as the owner.

### `GET /executions/{run_id}`

Read access should align with workspace membership.

Rules:

- missing run -> `404`
- inaccessible run/workspace -> `404`
- workspace owner can read
- workspace members can read
- unrelated users cannot read

Do not preserve the current blanket "owner/admin can read almost everything" rule.

### WebSocket

Explicitly leave `/ws/{group_folder}` access control unchanged in this slice.

Reason:

- the current transport is still an early direct-entrypoint path
- changing it now would pull in frontend and protocol rewiring outside `M7.3.4`

Record this as a residual risk, not as hidden scope.

## Error Handling

Use one consistent rule:

- return `404` when the workspace does not exist or the caller should not learn whether it exists
- return `400` only when the caller already targeted a valid accessible workspace but the action itself is invalid under the model
- use `409` for duplicate membership conflicts

Examples:

- inaccessible shared workspace -> `404`
- member-management request against a home workspace -> `400`
- duplicate member add -> `409`
- owner demotion/removal -> `400`

## Testing Strategy

Focused tests should cover:

- `GroupMember` exposes the persistent workspace-membership contract, including `group_folder` identity and `added_by`
- SQLite initialization and runtime schema healing support the upgraded `group_members` shape
- membership service persists by `group_folder`, preserves owner invariants, supports self-removal, and rejects invalid mutations
- registry service can answer workspace access and member-management eligibility using owner/member state
- `/groups` visibility includes shared workspaces for members and still hides other users' home workspaces plus raw IM endpoint rows
- `/groups/{group_id}/members` enforces home-private rules, owner-only management, and self-leave
- `/messages` allows shared members into the workspace execution context and rejects unrelated users with `404`
- `/executions/{run_id}` allows workspace members to read shared runs and hides runs from non-members

Regression should continue to cover:

- current IM binding behavior from `M7.3.3`
- execution coordinator behavior from `M7.2`
- existing home/main workspace topology from `M7.3.2`

## Acceptance Criteria

This slice is complete when:

- Portex persists workspace membership by `group_folder` instead of relying on the current in-memory member store
- home workspaces remain private and cannot be member-managed
- non-home canonical web workspaces can be shared with additional users
- workspace membership affects workspace listing, member management, HTTP message dispatch, and execution-status reads
- raw IM endpoint rows remain hidden from `/groups`
- `M7.3.3` IM ingress semantics remain stable
- focused tests, full backend regression, lint, and diff hygiene all pass
- handoff docs move the next start point from `M7.3.4` to `M7.3.5`
