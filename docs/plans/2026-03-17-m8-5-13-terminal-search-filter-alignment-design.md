# M8.5.13 Terminal Search Filter Alignment Design

## Goal

Add timeline-aligned server-side filters to terminal-history search so operators can narrow search results by the same metadata they already use in the timeline view.

## Scope

- extend terminal-history search with optional `status`, `owner_user_id`, and `session_id_prefix` filters
- reuse the existing timeline filter semantics instead of inventing search-only rules
- keep `/terminals` search panel bound to the selected workspace and current filter controls
- preserve existing search pagination, snippet deep-linking, and cross-session navigation behavior
- preserve current RBAC/workspace-access boundaries and history compatibility anchors

## Out Of Scope

- no change to `GET /terminals/{group_id}/sessions/current/history`
- no change to `latest.json` / archived snapshot persistence format
- no time-range filters in this milestone
- no fuzzy/regex syntax, ranking changes, or new sort modes
- no new standalone search page outside `/terminals`

## Current Gap

`main` currently includes `M8.5.12`, so operators can search output, paginate results, navigate across sessions, and deep-link from snippets into detail highlights. But search still runs across the entire workspace history set even when the operator has already narrowed the timeline with `status`, `owner_user_id`, or `session_id_prefix`.

## Recommended Architecture

### 1. Reuse Existing Snapshot Filter Semantics

Extend `TerminalSessionService.search_history_by_group(...)` with optional:

- `status`
- `owner_user_id`
- `session_id_prefix`

Apply these by reusing the existing `_filter_history_snapshots(...)` helper before `_search_history_snapshots(...)`.

This keeps timeline and search aligned on:

- which snapshots are in scope
- which empty states are possible
- how session metadata filtering behaves

### 2. Additive Search API Contract

Extend:

- `GET /terminals/{group_id}/sessions/history/search`

with optional query parameters:

- `status`
- `owner_user_id`
- `session_id_prefix`

Behavior:

- workspace has no history snapshots: preserve current `404`
- workspace has history but filters remove every snapshot: preserve current `404`
- workspace has filtered snapshots but query yields no output match: return `200` empty page

This preserves the current distinction between "no searchable history set" and "searchable set with zero matches."

### 3. Frontend Filter Reuse

On `/terminals`:

- reuse the existing timeline filter controls as the search filter source of truth
- pass the same filter state into the search query hook/API call
- reset search pagination/detail target state whenever filters change

Do not add a second search-only filter section. One set of controls is enough and prevents state drift.

### 4. Compatibility Boundary

Keep unchanged:

- `latest.json` and archived snapshot file formats
- `GET /terminals/{group_id}/sessions/current/history`
- existing search result ordering and pagination shape
- snippet metadata/deep-link behavior
- terminal role/workspace access checks

## Risks And Mitigations

- **Risk:** timeline and search diverge on which snapshots a filter should include.
  - **Mitigation:** reuse the same service-side snapshot filter helper.
- **Risk:** changing filters leaves stale search/detail state in the UI.
  - **Mitigation:** reset `searchOffset`, `detailSessionId`, and pending match target on filter updates.
- **Risk:** filtered-empty and query-empty states become ambiguous.
  - **Mitigation:** preserve current backend semantics: empty filtered snapshot set stays `404`, empty matches on a valid filtered set stays `200`.

## Testing Strategy

### Backend

- service tests for `status`, `owner_user_id`, and `session_id_prefix` filtering before search
- route tests for parameter pass-through and unchanged empty/404 behavior
- OpenAPI tests for new search query parameters

### Frontend

- `/terminals` search query hook includes filter state in cache key and request params
- filter changes reset search/detail state cleanly
- existing search pagination and snippet deep-link behavior still compile and build cleanly

## Completion Signal

`M8.5.13` is complete when:

- terminal-history search accepts the same three filters as the timeline
- `/terminals` search results narrow according to the active timeline filters
- search pagination/navigation/snippet deep links still work within the filtered result set
- compatibility anchors and focused regression remain green
