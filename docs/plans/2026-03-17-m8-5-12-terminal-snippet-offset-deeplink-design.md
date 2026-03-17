# M8.5.12 Terminal Snippet-to-Offset Deep Link Design

## Goal

Add snippet-level deep linking on `/terminals` so operators can click a search snippet and jump directly to the corresponding output match in history detail.

## Scope

- extend terminal-history search results with additive snippet position metadata
- keep existing `snippets: string[]` response field for compatibility
- add snippet click actions in `/terminals` search results
- when snippet is clicked, open history detail and activate the matching offset highlight
- preserve current RBAC/workspace-access boundaries and existing route structure

## Out Of Scope

- no change to `GET /terminals/{group_id}/sessions/current/history`
- no change to persisted `latest.json` / archived snapshot formats
- no cross-workspace search
- no regex/fuzzy search or ranking/index redesign
- no changes to terminal ownership/session lifecycle semantics

## Current Gap

`M8.5.11` supports search pagination and cross-session next/previous match navigation, but the operator cannot jump from a specific snippet line to its exact detail position. `View Details` always anchors to boundary matches instead of the selected snippet.

## Recommended Architecture

### 1. Additive Search Snippet Position Model

In `TerminalSessionService.search_history_by_group(...)`, keep current matching/sorting behavior and add snippet-level metadata:

- `match_index`: zero-based index of the match in this session output
- `match_offset`: character offset in output where the match starts
- `text`: rendered snippet string (same content previously returned in `snippets`)

Keep existing `snippets` list in the response as a compatibility mirror of `snippet_matches[].text`.

### 2. Additive API Contract

Extend `TerminalSessionHistorySearchMatchResponse` with:

- `snippet_matches: list[TerminalSessionHistorySearchSnippetResponse]`

where each item includes `text`, `match_index`, and `match_offset`.

This is additive only; existing clients that read `snippets` remain compatible.

### 3. Frontend Deep Link Flow

On `/terminals`:

- render each snippet as a clickable control
- clicking a snippet opens/keeps the target detail session
- use `match_offset` (primary) + `match_index` (fallback) to select the exact highlight in detail output
- keep existing previous/next navigation behavior intact

### 4. Compatibility Boundary

Keep unchanged:

- `latest.json` and archived history file formats
- `/sessions/current/history` behavior
- terminal role gate + workspace-access checks

## Risks And Mitigations

- **Risk:** Offset target not found in recalculated ranges.
  - **Mitigation:** fallback to `match_index`, then clamp to valid range.
- **Risk:** API contract break for current clients.
  - **Mitigation:** additive field only; preserve `snippets`.
- **Risk:** UI state drift when switching pages/sessions.
  - **Mitigation:** keep deterministic pending-target state and reset on query/group changes.

## Testing Strategy

### Backend

- service tests assert snippet metadata (`match_index`, `match_offset`, `text`) and compatibility `snippets`
- route tests assert new `snippet_matches` field shape
- OpenAPI tests assert new schema component/property visibility

### Frontend

- TypeScript compile/lint validation for new API type usage
- `/terminals` behavior check via build/lint and manual flow logic review:
  - snippet click opens detail
  - selected snippet lands on corresponding highlighted match
  - previous/next navigation still works

## Completion Signal

`M8.5.12` is complete when:

- search API returns additive snippet position metadata while keeping `snippets`
- snippet click in `/terminals` deep-links detail to the intended match
- terminal focused regression and full verification remain green
