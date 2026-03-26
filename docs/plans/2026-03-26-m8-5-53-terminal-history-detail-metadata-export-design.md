# M8.5.53 Terminal History Detail Metadata Export Design

## Goal

Extend terminal history detail download so operators can export either raw text or the full detail payload as a downloadable JSON attachment, while keeping raw text as the default behavior and preserving existing timeline/search/detail/RBAC contracts.

## Scope

- extend `GET /terminals/{group_id}/sessions/history/{session_id}/download`
- add an optional query parameter:
  - `format=text|json`
- keep `text` as the default so the current raw output download remains unchanged
- for `format=json`, export the existing terminal history detail payload as `application/json` attachment content
- add one additional `Download JSON` action to the `/terminals` history detail panel

## Out Of Scope

- no workspace-wide bulk export
- no timeline/search export
- no new persistence fields or service-layer storage changes
- no changes to `services/terminal_sessions.py`
- no changes to terminal relevance / offline baseline / search sorting
- no changes to `latest.json`, `/sessions/current/history`, or RBAC

## Context

`M8.5.52` already added raw terminal output download from the history detail panel. That closes the “I need the transcript body” gap, but it still leaves one operator workflow awkward: when the operator wants to preserve the exact snapshot metadata together with the output, they must manually copy fields from the detail panel or call the JSON detail API separately.

The next smallest additive step is not bulk export. It is letting the same download surface emit either:

- plain text output for transcript-centric workflows
- JSON detail payload for audit/debug workflows

This stays aligned with the current operator-surface track and avoids reopening the converged relevance chain.

## Approaches Considered

### 1. Extend the existing download route with `format=text|json` (recommended)

Pros:

- smallest additive API delta
- preserves the current raw text route path and default behavior
- keeps one clear download entry point for one snapshot
- lets the frontend reuse the same API helper with only a narrow option addition

Cons:

- one route now serves two content types

### 2. Add a second dedicated JSON export route

Pros:

- route semantics are explicit

Cons:

- duplicates detail-download path structure
- adds another operator-facing endpoint for the same snapshot

### 3. Build JSON client-side from the existing detail query only

Pros:

- no backend change

Cons:

- browser-only behavior; API clients still lack a direct export endpoint
- duplicates serialization rules in the frontend
- no server-owned content type or attachment filename contract

## Recommended Approach

Use approach 1. Keep the current route path, make raw text the default, and add one explicit `format=json` branch for metadata-rich export.

## Route Contract

### Path

- `GET /terminals/{group_id}/sessions/history/{session_id}/download`

### Query Parameter

- `format`
  - allowed values: `text`, `json`
  - default: `text`

### Semantics

- `format=text`
  - unchanged `M8.5.52` behavior
  - response body is exactly the stored snapshot output
  - `Content-Type: text/plain; charset=utf-8`
  - attachment filename ends with `.log`
- `format=json`
  - response body is the existing `TerminalSessionHistoryDetailResponse` payload serialized as JSON
  - `Content-Type: application/json`
  - attachment filename ends with `.json`

Missing workspace/session behavior stays exactly as today:

- same auth checks
- same workspace access checks
- same `404` mapping path

## Backend Design

In `app/routes/terminals.py`:

- add a narrow literal query parameter for `format`
- keep using `get_history_snapshot_by_group(...)`
- reuse `_to_terminal_history_detail_response(...)` for the JSON payload instead of rebuilding fields
- generalize the attachment filename helper so it can emit either `.log` or `.json`

No service, schema, or persistence change is required.

## Frontend Design

In `web/src/api/client.ts`:

- extend `downloadTerminalHistoryDetail(...)` with an optional format argument defaulting to `text`

In `web/src/pages/Terminals.tsx`:

- generalize the existing filename helper to accept file extensions
- keep the current `Download Output` action for raw text
- add `Download JSON` beside it
- reuse the same action/error state and blob-download pattern already used by the current detail download

## Testing Strategy

Backend coverage:

- route test: default download still returns raw text and `.log`
- route test: `format=json` returns JSON attachment content and `.json`
- route test: missing session with `format=json` still returns `404`
- route test: invalid format returns `422`
- OpenAPI test: download route exposes the `format` parameter

Frontend verification:

- `npm run build` and `npm run lint` cover the new helper signature and UI wiring

Regression verification:

- focused terminal route/API tests
- `ruff`
- web lint/build
- `git diff --check`

## Risks And Mitigations

- Risk: the new JSON branch could accidentally change the default raw download behavior.
  - Mitigation: keep `format=text` as the explicit default and retain the existing success test unchanged.
- Risk: attachment filenames could diverge between text and JSON branches.
  - Mitigation: use one shared helper with a validated extension input.
- Risk: frontend action handling could become duplicated and drift.
  - Mitigation: reuse one shared download helper in the page with a small format/file-extension parameter.

## Rollout

Additive operator-facing API/UI change only. No migration and no compatibility break for existing raw terminal history downloads.
