# M8.5.60 Terminal Cross-Workspace History Archive Export Design

## Goal

Add a cross-workspace downloadable JSON archive for all terminal-history snapshots across canonical web workspaces so operators can preserve the full transcript archive from the top-level `/terminals` surface without changing existing workspace-scoped export contracts.

## Scope

- add `GET /terminals/history/archive`
- export all available terminal-history snapshots across canonical web workspaces visible in `/terminals`
- return an `application/json` attachment containing:
  - `total_workspaces`
  - `total_snapshots`
  - `items`
  - each item includes:
    - `group_id`
    - `group_name`
    - `chat_accessible`
    - `total`
    - `items`
      - same payload shape as `TerminalSessionHistoryDetailResponse`
- add one overview-level `Export History Archive JSON` action to `/terminals`

## Out Of Scope

- no current-page export changes
- no latest-history bundle changes
- no ZIP/CSV/text bundle format
- no top-level cross-workspace search archive in this session
- no `latest.json` or persistence-layout changes
- no changes to terminal relevance / offline baseline / search sorting
- no changes to RBAC or workspace-access rules

## Context

The terminal operator surface now supports:

- overview export
- latest-history bundle export
- workspace-scoped detail export
- workspace-scoped current-page timeline/search export
- workspace-scoped all-pages timeline/search archive export

The remaining obvious export gap is a full cross-workspace transcript archive. Operators can already export:

- overview-only inventory
- one latest snapshot per workspace
- full archives per workspace

but they still need to export workspace archives one by one to capture the full system-wide transcript set.

The next additive step is therefore a top-level cross-workspace archive export.

## Approaches Considered

### 1. Add a cross-workspace history archive route grouped by workspace (recommended)

Pros:

- directly closes the remaining top-level transcript archive gap
- preserves the current per-workspace archive semantics
- grouped payload is easier to inspect than one flat cross-workspace list
- fits naturally beside overview and latest-history top-level exports

Cons:

- larger payload than the latest-history bundle

### 2. Export one flat list of snapshots across all workspaces

Pros:

- simpler response shape

Cons:

- less operator-friendly
- loses natural workspace grouping

### 3. Jump to ZIP or file bundle formats

Pros:

- stronger artifact story

Cons:

- larger scope jump
- unnecessary before the JSON contract is established

## Recommended Approach

Use approach 1. Add a top-level route that groups full snapshot details by workspace and reuses the same canonical overview ordering as `/terminals`.

## Route Contract

### Path

- `GET /terminals/history/archive`

### Semantics

- applies the same auth and terminal-role checks as `GET /terminals`
- uses the same canonical web workspace inventory and ordering as the overview surface
- includes only workspaces that currently have terminal history
- returns `application/json`
- returns an attachment filename ending with `.json`

### Response Shape

Return a JSON object containing:

- `total_workspaces`
- `total_snapshots`
- `items`
  - `group_id`
  - `group_name`
  - `chat_accessible`
  - `total`
  - `items`
    - same payload shape as `TerminalSessionHistoryDetailResponse`

If no workspaces currently have terminal history, return `404`.

## Backend Design

In `services/terminal_sessions.py`:

- add one helper that returns all history snapshots grouped by workspace folder
- mirror the current merged per-workspace history semantics already used by `list_history_snapshots_by_group(...)`

In `app/routes/terminals.py`:

- add an archive bundle filename helper
- add the new top-level history archive route beside `/terminals/export` and `/terminals/history/export`
- reuse canonical web workspace discovery and ordering from the overview surface
- join workspace metadata with the grouped snapshot helper

No persistence or ranking change is required.

## Frontend Design

In `web/src/api/client.ts`:

- add `downloadTerminalHistoryArchiveBundle(token)`

In `web/src/pages/Terminals.tsx`:

- add one overview-level action:
  - `Export History Archive JSON`
- reuse the existing page-level `actionKey` / `actionError` / `actionNotice` state
- reuse the existing blob-download browser flow

## Testing Strategy

Service coverage:

- grouped archive helper returns the expected grouped snapshot sets
- empty result returns an empty mapping/list so the route can map it to `404`

Backend coverage:

- cross-workspace history archive route returns JSON attachment content
- auth and role checks stay aligned with the overview route
- empty-history case returns `404`
- OpenAPI exposes the new route

Frontend verification:

- `npm run build` and `npm run lint` cover the new helper and action wiring

Regression verification:

- focused terminal service + route/API tests
- `ruff`
- web lint/build
- `git diff --check`

## Risks And Mitigations

- Risk: payloads can grow significantly larger than the latest-history bundle.
  - Mitigation: keep the format JSON-first and group by workspace so later size-management decisions can layer on top cleanly.
- Risk: archive grouping/order could drift from the overview surface.
  - Mitigation: reuse canonical workspace ordering from the overview route and per-workspace merged history ordering from the service layer.

## Rollout

Additive operator-facing API/UI change only. No migration and no compatibility break for existing overview/latest-history/workspace export contracts.
