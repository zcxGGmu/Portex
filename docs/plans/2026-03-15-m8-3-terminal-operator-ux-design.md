# M8.3 Terminal Operator UX Design

## Goal

Add the first operator-facing terminal management surface for Portex by introducing a dedicated read-only terminal overview API and a standalone `/terminals` page.

## Scope

- add a dedicated operator read API for terminal session overview
- add a standalone `/terminals` page in the Web app
- show terminal state across all canonical web workspaces
- keep the current chat-embedded `TerminalPanel` behavior unchanged
- add the minimum chat deep-link support needed to open one specific workspace from `/terminals`
- expose whether the current operator can actually open a given workspace in chat

## Out Of Scope

- no terminal session start, reconnect, close, takeover, or force-close controls from `/terminals`
- no transcript/history replay on the operator page
- no expansion of terminal ownership or role semantics
- no terminal persistence beyond the current in-memory session registry
- no changes to terminal protocol, PTY fidelity, ANSI rendering, or resize propagation
- no terminal data folded into the existing `/monitor` API or page
- no room-level chat deep-linking beyond workspace selection

## Current Gap

`M8.1` and `M8.2` together made terminal sessions usable from `/chat`, but the only read surface is still per-workspace and embedded in the chat shell.

Portex currently lacks:

- a global operator overview of which workspaces have live terminal sessions
- a global view of detached sessions and reconnect deadlines
- a dedicated navigation surface for terminal operations comparable to other operator pages
- a reliable workspace deep link from operator surfaces into `/chat`

There is also one implementation nuance in the current app: `/groups` returns only workspaces accessible to the current user, not every canonical workspace. That means a global operator terminal page cannot assume every listed workspace is also chat-openable for the same operator.

## Options Considered

### Option A: Add a dedicated terminal overview API and standalone `/terminals` page (recommended)

Pros:

- keeps terminal operator scope explicit and isolated from execution monitor scope
- creates a clean expansion point for later light-control actions
- avoids frontend N+1 polling against per-workspace terminal APIs
- keeps current chat terminal behavior stable

Cons:

- requires new DTOs, route tests, and one more operator page

Recommendation: choose this option.

### Option B: Fold terminal state into the existing `/monitor` API and page

Pros:

- fewer top-level routes and pages

Cons:

- bloats an existing execution-focused operator payload
- couples terminal lifecycle concerns to execution queue/run monitoring
- makes future terminal-specific evolution harder

Reject.

### Option C: Let the frontend enumerate workspaces and call current-session APIs one by one

Pros:

- minimizes backend changes

Cons:

- causes N+1 requests proportional to workspace count
- makes empty-state and permission handling brittle
- duplicates aggregation work in the browser

Reject.

## Recommended Architecture

### 1. Dedicated Operator Route

Add a new read-only route:

- `GET /terminals`

This route is a global operator surface, not a workspace-scoped user surface. It should stay separate from:

- `/monitor`
- `/terminals/{group_id}/sessions`
- `/ws/terminals/{session_id}`

### 2. Access Control

Keep access semantics aligned with current operator pages:

- `owner` and `admin`: allowed
- `member`: `403`

Unlike `/groups`, this route should not be limited to only workspaces accessible in chat. It is a global operator read surface over canonical web workspaces.

### 3. Backend Read Model

Extend `TerminalSessionService` with a pure read helper, for example:

- `list_sessions() -> list[TerminalSessionRecord]`

The helper should expose current in-memory session snapshots without changing lifecycle semantics.

No new persistence, history, or audit storage is added in this milestone.

### 4. Workspace Aggregation

In the route layer:

1. fetch canonical web workspaces from `GroupRegistryService`
2. fetch current terminal session snapshots from `TerminalSessionService`
3. join them by workspace folder
4. compute whether the current operator can open that workspace in chat

For chat accessibility, reuse `GroupRegistryService.user_can_access_group(...)` and surface the result explicitly. This avoids promising a deep link that the current operator cannot actually use.

### 5. Response Shape

Return a simple list response built around canonical workspaces:

- `group_id`
- `group_name`
- `chat_accessible`
- `session: TerminalSessionResponse | null`

This keeps the route aligned with existing terminal session DTOs instead of inventing a second session schema.

Suggested container DTOs:

- `TerminalWorkspaceSummaryResponse`
- `TerminalWorkspaceListResponse`

### 6. Sorting Semantics

Sort items so active operational signal appears first:

1. workspaces with session status `attached`, `created`, or `detached`
2. workspaces with session status `closed` or `exited`
3. workspaces with no session

Within the same bucket, keep deterministic ordering by workspace name or id.

### 7. Frontend Page

Add a new operator page:

- `web/src/pages/Terminals.tsx`

The page should reuse existing operator conventions from `/monitor`:

- role gate
- loading state
- forbidden state
- unavailable state

Primary sections:

- summary cards derived from the returned list
- workspace table or card list showing current terminal state

Displayed fields:

- workspace name / id
- session id
- status
- owner user id
- backend
- container name
- created time
- last attached time
- reconnect deadline

This page stays read-only.

### 8. Chat Deep Link

Add the minimum workspace-level chat deep link:

- `/chat?workspace=<group_id>`

`ChatPanel` should, on initial load, prefer the query-string workspace when:

- the workspace id exists in the currently visible chat workspace list

If valid, sync that workspace selection into the existing local storage key so later navigation stays consistent.

Do not add room-level parameters or other chat routing changes in `M8.3`.

### 9. Navigation

Add `Terminals` to the operator navigation set:

- desktop top navigation
- mobile `More` sheet

Only `owner/admin` should see the entry.

## Testing Strategy

### Backend

- add focused service coverage for the new terminal session listing helper
- add route coverage for `GET /terminals`
- cover `401`, `403`, populated response, empty response, ordering, and `chat_accessible`

### OpenAPI

- extend API schema tests for the new route and DTOs
- keep existing terminal session route contracts unchanged

### Frontend

- use the established red-green build pattern:
  - wire `/terminals` route and navigation before the page exists
  - confirm `npm run build` fails
  - implement the page, client helpers, and chat deep link
  - confirm build recovers

### Regression

- run focused terminal backend tests
- run frontend lint and production build
- run full backend pytest
- run Ruff and `git diff --check`

## Completion Signal

`M8.3` is complete when:

- Portex exposes a dedicated read-only `GET /terminals` operator API
- `/terminals` shows terminal state across canonical web workspaces
- the page clearly distinguishes active, detached, closed/exited, and empty workspaces
- `Open in Chat` is shown only when the current operator can actually open that workspace
- the current chat terminal control boundary remains unchanged
- focused verification and full regression both pass
