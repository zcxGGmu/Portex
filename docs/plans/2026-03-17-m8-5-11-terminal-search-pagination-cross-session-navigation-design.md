# M8.5.11 Terminal Search Pagination/Cross-Session Match Navigation Design

## Goal

Add paginated workspace terminal-output search and cross-session previous/next match navigation so operators can move through search hits across multiple history snapshots without leaving `/terminals`.

## Scope

- add a dedicated per-workspace terminal-history output search route
- keep search results paginated with stable ordering and additive metadata (`total`, `has_more`)
- return session-level match metadata (`match_count`, snippets) for operator triage
- add `/terminals` search panel with query + pagination controls
- keep local detail-match navigation and extend it to cross-session previous/next traversal
- keep current RBAC/workspace-access gates and history compatibility anchors unchanged

## Out Of Scope

- no change to `GET /terminals/{group_id}/sessions/current/history`
- no change to `latest.json` / archived snapshot persistence format
- no global cross-workspace search
- no regex/fuzzy syntax, ranking model, or index storage
- no backend-rendered highlight markup
- no new standalone page outside `/terminals`

## Current Gap

`main` currently includes `M8.5.8` timeline filters/detail, but still lacks output-level search discovery and any cross-session navigation flow for match iteration. Operators still need manual session-by-session inspection for error fragments.

## Recommended Architecture

### 1. Dedicated Search Read Model

Add `TerminalSessionService.search_history_by_group(...)` on top of the existing merged snapshot inventory (`in-memory + latest + archived`).

For each snapshot:

- run case-insensitive substring matching on `output`
- compute `match_count`
- build bounded plain-text snippets (small context window, capped count)

Sort matched sessions by:

1. `match_count` descending
2. `snapshot_at` descending
3. `session_id` ascending

Then paginate and return `total` + `has_more`.

### 2. Additive Search API Contract

Add:

- `GET /terminals/{group_id}/sessions/history/search?q=...&limit=...&offset=...`

Behavior:

- workspace has no history snapshots: preserve current terminal `404` mapping
- workspace has history but query yields no matches: `200` with empty result page
- keep existing terminal role + workspace-access boundaries unchanged

### 3. Frontend Search + Cross-Session Navigation

Upgrade `/terminals` with:

- `Search Output` controls bound to the selected workspace
- paginated search-result table (`Previous`/`Next`)
- action to open a matched session in existing detail panel

Reuse local detail-match highlighting/navigation and extend boundary behavior:

- `Next` at the last match in current detail jumps to the first match in the next search result session
- `Previous` at the first match jumps to the last match in the previous search result session
- if navigation crosses the current search page boundary, move search page offset and auto-select the boundary item on the newly loaded page

### 4. Compatibility Boundary

Keep these unchanged:

- `latest.json` persistence model
- `/terminals/{group_id}/sessions/current/history`
- existing timeline/detail routes and RBAC mapping

New search contracts are additive only.

## Risks And Mitigations

- **Risk:** Search and timeline use different snapshot sets.
  - **Mitigation:** share the same merged-snapshot inventory helper.
- **Risk:** Cross-session navigation state desynchronizes when query/page changes.
  - **Mitigation:** reset selection/index state deterministically on query/group/page transitions.
- **Risk:** Large outputs produce noisy snippets.
  - **Mitigation:** strict snippet count + context caps, no full-output duplication in search payloads.
- **Risk:** Route overlap with `/history/{session_id}`.
  - **Mitigation:** keep explicit `/history/search` route and dedicated schema tests.

## Testing Strategy

### Backend

- service tests for case-insensitive search, pagination, snippet caps, empty-match behavior, and missing-workspace `404`
- route tests for auth/access/success/empty/404 and query validation
- OpenAPI tests for the new search path, parameters, and DTO schemas

### Frontend

- `/terminals` search result rendering and pagination controls
- selecting a result opens detail and keeps highlight behavior
- previous/next can cross session boundaries
- page-boundary navigation updates offset and auto-selects boundary result
- frontend lint/build remain green

## Completion Signal

`M8.5.11` is complete when:

- operators can search terminal output within one workspace with paginated results
- operators can iterate matches across sessions from the detail panel using previous/next
- compatibility anchors (`latest.json`, `current/history`, RBAC boundaries) remain unchanged
- focused terminal regression and full verification remain green
