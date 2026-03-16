# M8.5.9 Terminal History Output Search Design

## Goal

Add per-workspace terminal output search so operators can locate matching terminal-history sessions quickly and then inspect the full snapshot in the existing detail panel.

## Scope

- add a dedicated per-workspace terminal-history search route
- search across the current merged snapshot set for one workspace (`in-memory + latest.json + archived snapshots`)
- return session-level aggregated search matches with snippets
- add `/terminals` search UI and detail-panel keyword highlighting
- keep existing timeline/detail routes and compatibility anchors unchanged

## Out Of Scope

- no change to `GET /terminals/{group_id}/sessions/current/history`
- no change to `latest.json` or archived snapshot persistence format
- no cross-workspace global search
- no regex, fuzzy search, ranking model, or persistent index
- no export, download, or search-history UX
- no backend-rendered HTML highlighting

## Current Gap

`M8.5.8` lets operators filter metadata and inspect one session in detail, but there is still no way to answer "which terminal-history session contains this error/output fragment?" within a workspace. Operators must open snapshots one by one and search manually.

## Recommended Architecture

### 1. Dedicated Search Read Model

Add `TerminalSessionService.search_history_by_group(...)` instead of overloading the existing timeline route. Search should reuse the current merged snapshot inventory so results stay consistent with timeline and detail:

1. in-memory current snapshot
2. persisted `latest.json`
3. archived `snapshots/<session_id>.json`

Each snapshot is scanned case-insensitively against the query string. Matching snapshots are returned as session-level aggregated results with:

- `session`
- `snapshot_at`
- `match_count`
- `snippets`

Search results should sort by:

1. `match_count` descending
2. `snapshot_at` descending
3. `session_id` ascending

### 2. Additive Search API

Add a dedicated route:

- `GET /terminals/{group_id}/sessions/history/search?q=...&limit=20&offset=0`

This keeps the current timeline route focused on metadata browsing while the new search route handles output matching. Empty-match cases should return `200` with an empty page; only workspaces with no history at all should continue returning the existing terminal `404`.

### 3. Snippet Contract

Backend snippets should stay plain text. Each result should expose a bounded list of short snippets around the matched text, plus `match_count`. The backend should not emit HTML or presentation markup; frontend highlighting remains a pure rendering concern.

Start with:

- case-insensitive substring match
- up to 3 snippets per session result
- a small fixed context window around each match

This is enough to validate operator value without prematurely introducing index maintenance or advanced query syntax.

### 4. Minimal UI Upgrade

Keep `/terminals` as the only operator surface. Add a `Search Output` panel that:

- accepts a query for the selected workspace
- shows session-level results with `session_id`, status, `snapshot_at`, `match_count`, and snippets
- reuses the current detail panel when the operator opens a result
- highlights the active search term in the detail output on the frontend

Search state should remain separate from timeline metadata filters so the two tools do not overwrite each other.

## Risks And Mitigations

- **Risk:** timeline and search return inconsistent session sets.
  - **Mitigation:** both read from the same merged snapshot inventory.
- **Risk:** one large snapshot dominates the response with too many matches.
  - **Mitigation:** cap snippets per result and return `match_count` separately.
- **Risk:** search route becomes a disguised heavy analytics endpoint.
  - **Mitigation:** stay within single-workspace scan, bounded outputs, and no indexing.
- **Risk:** highlighting logic pollutes backend contracts.
  - **Mitigation:** keep snippets/output plain text and do highlighting only in the frontend.

## Testing Strategy

### Backend

- service tests for case-insensitive search across in-memory, `latest.json`, and archived snapshots
- service tests for snippet capping, `match_count`, empty-result behavior, and missing-workspace `404`
- route tests for auth/access/success/empty/404 and required query validation
- OpenAPI tests for the new search path and DTOs

### Frontend

- `/terminals` renders search results only when a query is submitted
- selecting a search result reuses the detail panel
- frontend highlighting only applies when there is an active search term
- frontend lint/build stay green

## Completion Signal

`M8.5.9` is complete when:

- operators can search terminal output within one workspace
- results identify matching sessions with snippets and counts
- operators can open matching sessions in the existing detail panel with frontend highlighting
- `latest.json`, current-history, timeline, and detail compatibility remain unchanged
- focused terminal tests and full regression stay green
