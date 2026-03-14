# M7.3.5 Conversation Slots Design

## Goal

Complete the next parity slice after `M7.3.4` by deciding that Portex should support more than one conversation context inside one workspace, but only through a minimal persistent conversation-slot model instead of jumping straight to full HappyClaw-style sub-agent and multi-tab parity.

## Scope

- introduce a persistent conversation-slot model under one workspace
- reserve one non-deletable `main` slot for every workspace
- allow future extra conversation slots under the same workspace
- keep workspace membership, files, memory, and IM binding at the workspace level
- thread slot identity into runtime/session/message boundaries where it becomes part of the real data model
- keep IM ingress pinned to the workspace `main` slot in this slice

## Out Of Scope

- do not add full sub-agent or task-agent persistence
- do not add `target_agent_id` or any IM-to-slot binding metadata
- do not add slot management APIs (`list/create/rename/delete`); that remains `M7.3.6`
- do not add frontend tab UI; that remains `M7.5`
- do not rework authenticated WebSocket access control; that remains deferred
- do not redesign workspace membership from `M7.3.4`

## Current State

Portex now has:

- canonical workspaces persisted in `registered_groups`
- workspace membership persisted in `group_members`
- execution/session identity currently keyed by `group_folder`
- IM endpoint binding metadata via `target_workspace_jid`
- one implicit conversation context per workspace

Portex still lacks:

- any persistent way to represent more than one conversation inside the same workspace
- any slot-level identity that runtime/session/message data can attach to
- any bridge between the current single-workspace session model and future tabbed chat UX

Today, one workspace effectively means one conversation axis. That keeps the current system simple, but it prevents Portex from cleanly growing toward HappyClaw's "main conversation plus additional tabs" product shape.

## Parity Signal From HappyClaw

The relevant parity signal is narrower than "copy HappyClaw exactly."

HappyClaw clearly supports:

- one main conversation per workspace
- additional conversation tabs
- task/sub-agent surfaces with their own status and routing behavior
- optional IM binding to one specific agent/tab

Portex should not swallow that whole product surface right now. The useful parity lesson for this milestone is only:

- one workspace may contain multiple conversation contexts
- the main conversation is special and always exists
- conversation identity is not the same thing as workspace membership or IM binding

Task-agent persistence, agent-specific IM routing, and full tab UI remain later work.

## Options Considered

### Option A: Stay Single-Conversation Per Workspace

- keep `1 workspace = 1 conversation = 1 session`
- explicitly reject multi-tab or sub-agent parity

Pros:

- smallest implementation
- no changes to runtime identity

Cons:

- hard-codes a product limitation that HappyClaw does not have
- would force a second breakup of the current model if Portex later wants tabs
- keeps workspace and conversation identity incorrectly fused together

Reject.

### Option B: Add Minimal Conversation Slots

- define one workspace-level `main` conversation slot
- allow additional conversation slots later
- keep task/sub-agent persistence out of scope
- keep IM routing at the workspace level for now

Pros:

- creates a clean data-model seam without swallowing the whole product surface
- preserves `M7.3.4` membership semantics
- gives `M7.3.6` and `M7.5` a stable target

Cons:

- requires runtime/session/message contracts to acknowledge slot identity
- adds one more identity axis to the model

Recommendation: choose this option.

### Option C: Jump Directly To Full HappyClaw Agent Tabs

- persist main tabs, conversation tabs, task tabs, and IM-to-agent bindings together

Pros:

- closes more parity gaps at once

Cons:

- explodes scope across backend, runtime, IM routing, snapshots, and frontend
- mixes data-model work with product-surface work
- hard to verify incrementally

Reject.

## Recommended Design

### 1. Separate Workspace Identity From Conversation Identity

Keep the current workspace boundaries exactly where they are:

- `registered_groups` remains the workspace and IM endpoint registry
- `group_members` remains the workspace membership source of truth
- workspace files, memory, and IM binding remain keyed by workspace

Add one narrower layer underneath:

- a persistent conversation-slot identity inside one workspace

This means:

- workspace answers "who can access this place?"
- slot answers "which conversation inside this place?"

### 2. Add A Persistent `conversation_slots` Table

Use one explicit table rather than hiding the concept in message metadata.

Recommended fields:

- `workspace_folder`
- `slot_id`
- `title`
- `created_by`
- `created_at`

Primary identity:

- `(workspace_folder, slot_id)`

Rules:

- every workspace has a reserved `slot_id="main"`
- `main` is non-deletable
- additional slots are conversation slots only in this milestone

Do not add `kind`, `target_agent_id`, `reply_policy`, or `is_main` here. `main` can be represented by the reserved `slot_id`.

### 3. Make Slot Identity Part Of Runtime Identity

The current runtime/session model is too coarse because it keys workspace lifecycle directly by `group_folder`.

For conversation slots, the stable mental model should become:

- workspace key: `group_folder`
- conversation key: `(group_folder, slot_id)`

Practical consequence:

- session continuity belongs to a slot, not to the whole workspace
- two slots in the same workspace should be able to keep separate context histories

The runtime can still derive a single string key internally, for example from `workspace_folder + slot_id`, but that derived key must now represent one slot-scoped conversation, not the whole workspace.

### 4. Make Slot Identity Part Of Message Persistence

If future tabs should show distinct histories, message persistence must know which slot a message belongs to.

Do not rely only on JSON-encoded `attachments` metadata for this. That is acceptable for correlation metadata, but not for a future first-class history boundary.

The minimal forward-compatible shape is:

- messages remain attached to the same workspace/chat boundary as today
- each message also carries a `slot_id`
- old rows can default to `main`

This keeps the schema honest without requiring tab-management APIs in the same milestone.

### 5. Default Everything To `main` Until Management APIs Exist

Compatibility should stay simple:

- existing callers that do not specify a slot land in `main`
- IM ingress always lands in `main`
- existing workspaces should auto-heal to contain `main`
- current tests and runtime flows can keep working with the default slot

This makes `M7.3.5` safe to land before `M7.3.6`.

### 6. Do Not Turn Slots Into Independent Security Boundaries

Slots are not mini-workspaces.

They must not get:

- separate membership
- separate IM binding ownership
- separate file roots
- separate memory roots

The permission answer stays:

- if you can access the workspace, you can access its conversation slots

This keeps `M7.3.4` intact and avoids multiplying authorization rules.

### 7. Keep IM Binding At Workspace Level

In this milestone:

- IM endpoint rows still bind to a workspace
- IM ingress still resolves one workspace
- resolved IM messages always enter that workspace's `main` slot

This is deliberate. Slot-level IM routing is a later decision because it would require new metadata, new conflict rules, and new orphan-binding recovery behavior.

### 8. Explicitly Defer Task-Agent Persistence

HappyClaw's task agents are not just "another conversation tab." They also carry:

- parent/child execution semantics
- lifecycle cleanup behavior
- event-stream routing
- optional IM-target interactions

Portex should not fake this as a generic slot in `M7.3.5`.

For now:

- conversation slots are persistent
- task/sub-agent surfaces remain runtime/event concepts

## API And Product Boundary

`M7.3.5` should create the data-model capability, not the full operator surface.

That means:

- no slot CRUD API yet
- no frontend tab bar yet
- no explicit tab-switch UX yet

But the model should be ready for:

- future `slot_id` on Web-originated dispatch
- future execution snapshots exposing `slot_id`
- future slot list/create/delete APIs in `M7.3.6`

## Compatibility Strategy

Use a migration path that preserves current behavior:

- old workspaces implicitly become `main`
- old messages implicitly become `main`
- old execution/session logic defaults to `main`
- current IM binding remains workspace-scoped

The result should be:

- no behavior regression for current single-conversation flows
- a real new platform seam for future tabs

## Verification Focus

When this milestone is implemented, the important proof points are:

- a workspace automatically has a `main` slot
- runtime/session identity can distinguish `main` from another slot in the same workspace
- message persistence distinguishes slot histories
- IM dispatch still lands on `main`
- workspace permissions still apply at the workspace level, not the slot level

## Residual Risks

- WebSocket transport is still keyed only by `group_folder`, so authenticated slot-aware WebSocket routing remains future work
- slot management APIs do not exist yet, so extra slots will initially be reachable only through direct service/test seeding until `M7.3.6`
- task-agent parity is still intentionally deferred and must not be confused with conversation-slot parity
