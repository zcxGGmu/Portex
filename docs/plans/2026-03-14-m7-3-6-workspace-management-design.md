# M7.3.6 Workspace Management API Design

## Goal

Complete the next parity slice after `M7.3.5` by adding the first real management API surface for canonical workspaces, conversation slots, and IM-to-workspace binding without pulling in frontend tab UI, deletion flows, or broader operator pages.

## Scope

- keep `/groups` as the canonical web-workspace list
- add shared-workspace creation and rename APIs
- add conversation-slot list/create APIs under one workspace
- add workspace-level IM binding list/bind/unbind APIs
- keep the current execution/session/message model unchanged beyond consuming the already-persisted workspace and slot metadata

## Out Of Scope

- do not add workspace deletion
- do not add slot rename/delete
- do not add frontend UI
- do not add slot-level IM binding or `target_agent_id`
- do not redesign current IM ownership discovery; keep the API surface conservative instead
- do not change authenticated WebSocket access or `M7.2` execution-plane behavior

## Current Gap

Portex now has:

- canonical web workspaces in `registered_groups`
- workspace membership in `group_members`
- IM endpoint binding metadata via `target_workspace_jid`
- persistent conversation slots under one workspace

Portex still lacks:

- any authenticated way to create a new shared workspace
- any authenticated way to rename an existing shared workspace
- any operator-facing way to see or create extra conversation slots
- any operator-facing way to view, bind, or unbind IM endpoint rows that are intentionally hidden from `/groups`

Today the model exists, but the management surface is still missing.

## Parity Signal From HappyClaw

The useful parity signal for this slice is still narrow:

- web users can manage workspace topology instead of relying only on lazy runtime registration
- extra conversations can be created explicitly instead of only through test seeding
- IM chats can be intentionally attached to one workspace through an authenticated management path

HappyClaw also exposes richer binding UX, force-rebind flows, agent-level binding, delete/archive flows, and broader settings pages. Those remain later work.

## Options Considered

### Option A: Expose raw IM endpoint rows directly in `/groups`

- keep one route family
- treat workspaces and IM endpoints as one flat list

Pros:

- smallest route count

Cons:

- breaks the `M7.3.3` decision that `/groups` is a workspace list
- mixes transport endpoints with canonical workspaces again
- makes future frontend state harder to reason about

Reject.

### Option B: Keep `/groups` workspace-first and add nested slot/binding subresources

- `/groups` remains the canonical workspace list
- workspace CRUD stays under `/groups`
- slot management lives under `/groups/{group_id}/slots`
- IM binding management lives under `/groups/{group_id}/bindings/im`

Pros:

- preserves the current mental model
- maps cleanly onto the already-separated workspace, slot, and binding concepts
- keeps raw IM endpoint rows out of the main workspace list while still exposing them where needed

Cons:

- requires a few new DTOs and route helpers

Recommendation: choose this option.

### Option C: Introduce a brand-new `/workspaces` root and deprecate `/groups`

- move all canonical workspace work to a new route family immediately

Pros:

- arguably cleaner naming

Cons:

- unnecessary churn in the current codebase
- duplicates or deprecates existing route contracts too early
- adds migration noise without closing more parity gaps

Reject.

## Recommended Design

### 1. Keep `/groups` As The Canonical Workspace Surface

`GET /groups` keeps its current meaning:

- return visible canonical `web:*` workspaces only
- continue hiding raw `telegram:*` / `feishu:*` endpoint rows

Build `M7.3.6` on top of that rather than redefining it.

### 2. Add Minimal Shared-Workspace Management

Add:

- `POST /groups`
- `PATCH /groups/{group_id}`

Behavior:

- only authenticated users with current `groups.write` permission can create or rename shared workspaces
- created workspaces are canonical `web:{group_id}` rows with `is_home=False`
- creator becomes `created_by` and is also seeded into `group_members` as `owner`
- `main` and `home-*` remain reserved canonical folders
- renaming only changes `name`, not `folder` or `jid`
- home workspaces and `web:main` remain non-renamable in this slice

This keeps the existing folder-based execution identity stable.

### 3. Add Minimal Conversation-Slot Management

Add:

- `GET /groups/{group_id}/slots`
- `POST /groups/{group_id}/slots`

Behavior:

- any user who can access the workspace can list slots
- any user who can access the workspace can create a non-`main` slot
- `main` remains implicit, reserved, and non-deletable
- slot IDs are explicit and persistent; they do not get auto-generated from title
- slot creation only adds metadata; it does not create a new permission boundary

This matches the `M7.3.5` decision that slots are conversation contexts inside one workspace, not mini-workspaces.

### 4. Add Conservative Workspace-Level IM Binding Management

Add:

- `GET /groups/{group_id}/bindings/im`
- `PUT /groups/{group_id}/bindings/im/{im_jid}`
- `DELETE /groups/{group_id}/bindings/im/{im_jid}`

Behavior:

- these routes stay workspace-scoped, not global
- only authenticated global `owner` users can use them
- caller must also be able to access the target workspace
- bind/unbind targets the workspace main conversation only
- binding is idempotent for the same workspace
- binding returns `409` when the IM endpoint is already bound to another workspace
- unbinding returns `400` when the IM endpoint is not bound to the requested workspace
- raw IM endpoint rows remain hidden from `/groups`, but this subresource can list them for binding management

The conservative owner-only rule is intentional because unbound IM endpoints currently do not carry a trustworthy user ownership signal.

### 5. Represent IM Binding List As Operator-Facing Status

`GET /groups/{group_id}/bindings/im` should return all currently known IM endpoint rows together with lightweight binding status:

- `im_jid`
- `name`
- `channel`
- `fallback_group_id`
- `binding_state` in `unbound | bound | orphaned`
- `target_group_id`
- `target_group_name`
- `bound_to_current_group`

This keeps `/groups` clean while still giving the later UI enough information to show:

- available endpoints
- endpoints already bound here
- endpoints bound elsewhere
- orphaned bindings that currently fall back at runtime

### 6. Keep Validation And Conflict Handling Narrow

Workspace IDs and slot IDs should stay simple:

- lowercase letters, digits, and hyphens only
- no empty strings
- reserved `main`
- reserved `home-*`

Do not add slugification, auto-renaming, or force-rebind in this slice.

If the caller wants to move an IM endpoint from one workspace to another, they must unbind first and then bind again.

### 7. Reuse Existing Access Semantics

Workspace resolution and access control should continue to reuse the current registry/member model:

- canonical workspace lookup goes through `get_web_workspace_by_folder(...)`
- workspace access stays based on `created_by`, `is_home`, and `group_members`
- slot access inherits workspace access
- execution and message dispatch continue to default to `slot_id="main"` unless an explicit slot is chosen

No new permission template is needed for this slice.

## Data Flow

### Create Shared Workspace

1. authenticated caller hits `POST /groups`
2. route validates `group_id` and `name`
3. registry creates `web:{group_id}` with `folder=group_id`
4. member service seeds `(group_folder=group_id, user_id=creator, role=owner)`
5. main slot is ensured
6. API returns the new workspace summary

### Create Extra Slot

1. authenticated caller resolves a visible workspace
2. route confirms workspace access
3. slot service inserts `(workspace_folder, slot_id, title, created_by)`
4. later `/messages` and execution status can reuse that slot immediately

### Bind IM Endpoint

1. owner resolves target workspace
2. route lists or looks up raw IM endpoint rows through the registry
3. if endpoint is unbound, set `target_workspace_jid` to the workspace JID
4. if endpoint is already bound here, keep success idempotent
5. if endpoint is bound elsewhere, reject with `409`
6. IM ingress will then resolve future inbound messages into that workspace folder

### Unbind IM Endpoint

1. owner resolves target workspace
2. route confirms the endpoint is currently bound to that workspace
3. clear `target_workspace_jid`
4. future inbound messages fall back to the endpoint row's own `chat-<hash>` folder again

## Testing Strategy

Focused tests should cover:

- workspace creation seeds canonical row, owner membership, and main slot
- workspace creation rejects reserved or invalid IDs
- workspace rename rejects home/main workspaces and missing/inaccessible targets
- slot list/create honors workspace access and preserves `main` first ordering
- IM binding list returns hidden raw endpoint rows only through the new binding route
- IM bind is idempotent for same target and rejects other-target conflicts
- IM unbind rejects mismatched bindings and clears matching bindings
- OpenAPI docs include the new routes and response models

Regression should continue to cover:

- `/groups` workspace listing
- `/messages` explicit slot dispatch
- IM ingress fallback/bound resolution
- execution-status access control

## Acceptance Criteria

This slice is complete when:

- authenticated callers can create and rename shared canonical workspaces through HTTP
- authenticated callers can list and create conversation slots under accessible workspaces
- owner users can list, bind, and unbind IM endpoints for a workspace without exposing raw IM rows in `/groups`
- the current workspace/member/slot semantics remain intact
- focused feature tests, broader regression tests, lint, and diff hygiene all pass
- handoff docs move the next real parity entrypoint past `M7.3.6`
