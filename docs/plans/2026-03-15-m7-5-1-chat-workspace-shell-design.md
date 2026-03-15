# M7.5.1 Chat Workspace Shell Design

## Goal

Complete the first `M7.5` frontend parity slice by expanding the current narrow `ChatPanel` into a workspace shell layout that has explicit space for workspace context, members, skills/files entry points, and execution controls while preserving the current text-only chat run chain.

## Scope

- expand `/chat` from a single chat column to a workspace shell layout
- keep the existing WebSocket send/cancel behavior intact
- add read-only workspace context surfaces in chat:
  - current workspace summary
  - workspace slots snapshot
  - workspace members snapshot
  - resource dock (files/memory/skills/mcp quick entries)
  - execution status/control summary
- add minimal frontend API client/hooks needed for workspace members and slots reads
- keep responsive behavior usable on desktop and mobile

## Out Of Scope

- do not add file upload/attachment UX in chat (`M7.5.2`)
- do not add workspace-switching UX (`M7.5.3`)
- do not add IM binding workflows (`M7.5.4`)
- do not add terminal panel (`M7.5.5`)
- do not change backend route contracts
- do not change the current WebSocket transport payload shape

## Current Gap

Portex currently has:

- standalone operator pages (`/files`, `/memory`, `/skills`, `/mcp-servers`, `/monitor`, `/usage`, `/audit`, `/settings`)
- a minimal chat page with runtime status and one narrow chat panel
- basic run controls (`send`, `cancel`, `clear`) mixed directly inside the message form

Portex currently lacks:

- a chat-first workspace shell that surfaces workspace context near the conversation
- in-chat visibility of slots/members/resources without leaving `/chat`
- a layout that can absorb richer chat features in later `M7.5.x` steps

## Options Considered

### Option A: Keep current ChatPanel and add more buttons

Pros:

- smallest code change

Cons:

- preserves a cramped single-column structure
- does not create durable layout space for files/members/skills/execution context
- increases visual clutter in one panel

Reject.

### Option B: Replace ChatPanel with a workspace shell layout and keep message chain unchanged

Pros:

- directly addresses `M7.5.1` intent
- reuses existing API surfaces without backend change
- keeps `M7.5.2+` room by separating context panels from message composer

Cons:

- larger frontend refactor than option A
- introduces additional read queries in chat view

Recommendation: choose this option.

### Option C: Build a full HappyClaw-like integrated shell now

Pros:

- highest feature parity immediately

Cons:

- swallows `M7.5.2` ~ `M7.5.7` scope into one step
- higher regression risk and harder verification/handoff

Reject.

## Recommended Design

### 1. Workspace Shell Structure

Turn `ChatPanel` into a three-zone shell:

- left: workspace context (`Workspace Snapshot`)
- center: message timeline + thinking/tool panels + composer
- right: resource/execution cards (`Resource Dock`, `Execution Controls`)

On narrow screens, collapse into a single-column stacked flow while keeping panel ordering deterministic.

### 2. Keep One Active Workspace In M7.5.1

Reuse current `/groups` list and resolve one active workspace in chat without adding a selector yet:

- active workspace = first visible workspace returned by `/groups`

This intentionally avoids stepping into `M7.5.3` while still grounding side panels in real workspace data.

### 3. Add Read Helpers For Members And Slots

Frontend only:

- `GET /groups/{group_id}/members`
- `GET /groups/{group_id}/slots`

Expose typed client methods and query hooks; show concise list cards in chat shell.

Failure handling is non-blocking:

- if members/slots fail, show muted error text in that card
- message send/cancel remains available

### 4. Resource Dock As Entry Surface, Not Embedded Tools

Add quick cards/buttons for:

- files
- memory
- skills
- mcp servers

The shell shows minimal counts/summaries and links to existing dedicated pages. No file attachment or inline editors in this milestone.

### 5. Execution Controls Card

Move execution controls out of the composer and into a dedicated card:

- running/idle badge
- active run id preview
- event counters (tokens/tool events)
- `Cancel` and `Clear` controls

Composer keeps only message input and `Send`.

### 6. Keep Messaging Contract Stable

Do not modify:

- websocket URL resolution behavior
- send payload (plain text for user message)
- cancel payload (`{ type: "cancel", run_id }`)
- stream-event mapping contract

This keeps `M7.5.1` purely UI/surface expansion.

## Validation Plan

Feature-level verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Completion Signal

`M7.5.1` is complete when:

- `/chat` renders a workspace shell (not narrow single-column-only chat panel)
- workspace snapshot (summary/slots/members) is visible without leaving chat
- resource dock and execution controls have dedicated space in the shell
- current chat run/send/cancel behavior stays functional
- verification commands pass and progress handoff is updated to `M7.5.2`
