# M7.5.3 Workspace/Room Switching UX Design

## Goal

Complete `M7.5.3` by adding richer room/workspace switching UX in Web chat, replacing the prior implicit fixed-target behavior with explicit, user-controllable workspace/room context switching.

## Scope

- add explicit workspace selector in chat shell
- add room (conversation slot) selector in chat shell
- make chat websocket target follow selected workspace
- isolate chat context when switching workspace/room so message streams are not mixed
- keep attachment upload and existing send/cancel contracts working in switched contexts

## Out Of Scope

- no backend websocket protocol changes
- no new backend APIs
- no IM binding UX (`M7.5.4`)
- no terminal panel (`M7.5.5`)

## Current Gap

After `M7.5.2`, chat uses the first workspace returned by `/groups` as an implicit active target. Users still cannot explicitly switch workspace or room in chat, which makes multi-workspace usage awkward.

## Options Considered

### Option A: Add workspace dropdown only

Pros:

- smallest delta

Cons:

- does not satisfy “room/workspace switching” fully

Reject.

### Option B: Add workspace + room selectors with frontend context switching

Pros:

- directly satisfies `M7.5.3`
- can be implemented with current APIs (`/groups`, `/groups/{id}/slots`)
- preserves backend stability

Cons:

- room selection remains a frontend context dimension because websocket endpoint is workspace-scoped

Recommendation: choose this option.

### Option C: Add backend slot-aware websocket routing first

Pros:

- strongest semantic room separation

Cons:

- scope explosion beyond `M7.5.3`

Reject.

## Recommended Design

### 1. Workspace Switching Surface

In `Workspace Snapshot`:

- add searchable workspace selector
- selected workspace becomes active websocket target
- switching workspace reconnects websocket

### 2. Room (Slot) Switching Surface

In `Conversation Slots`:

- make slots clickable as active room pills
- selecting a room switches chat context key to `{workspace}:{slot}`
- room switching does not require backend route changes

### 3. Context Isolation

Extend chat store with context switching:

- preserve per-context draft/messages/events/run state snapshot
- restore context snapshot when switching back
- avoid cross-workspace/room message mixing

### 4. Runtime Contract Preservation

Keep current websocket contract unchanged:

- user send remains text payload
- cancel remains `{ type: "cancel", run_id }`

For non-main room, include a minimal room marker in outbound prompt text for backend awareness without protocol changes.

### 5. UX Guardrails

- disable workspace/room switching while run is active
- clear attachment selection when workspace changes
- show active workspace and active room explicitly in shell cards

## Verification Plan

- red evidence: introduce chat usage of new store context-switch API before implementation, run `cd web && npm run build` and capture failure
- green:
  - `cd web && npm run lint`
  - `cd web && npm run build`
- regression:
  - `.venv/bin/pytest -o addopts='' -q`
  - `.venv/bin/ruff check .`
  - `git diff --check`

## Completion Signal

`M7.5.3` is complete when:

- users can explicitly switch workspace and room in chat UI
- websocket target follows selected workspace
- chat contexts are isolated by workspace/room selection
- verification passes and handoff moves to `M7.5.4`
