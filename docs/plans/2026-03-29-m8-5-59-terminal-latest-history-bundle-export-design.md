# M8.5.59 Terminal Latest History Bundle Export Design

## Goal

Add a cross-workspace downloadable JSON bundle for the latest terminal-history snapshot of each workspace so operators can preserve the current transcript state across `/terminals` without changing the existing overview export or workspace-scoped history export contracts.

## Scope

- add `GET /terminals/history/export`
- export the latest available terminal-history snapshot for each canonical web workspace that currently has history
- return an `application/json` attachment containing:
  - `total`
  - `items`
  - each item includes:
    - `group_id`
    - `group_name`
    - `chat_accessible`
    - `history`
      - same payload shape as `TerminalSessionHistoryDetailResponse`
- add one overview-level `Export Latest Histories JSON` action to `/terminals`

## Out Of Scope

- no full cross-workspace timeline archive
- no search-result bundle changes
- no current-page export changes
- no `latest.json` or persistence-layout changes
- no changes to terminal relevance / offline baseline / search sorting
- no changes to RBAC or workspace-access rules

## Context

The terminal operator surface now supports:

- top-level overview export
- per-workspace detail export
- per-workspace current-page timeline/search export
- per-workspace all-pages timeline/search archive export

One gap remains between overview-only inventory export and a heavier cross-workspace archive: there is still no single export that captures the latest transcript snapshot for all workspaces at once. Operators who need a broad incident-time bundle still have to export workspace archives one by one.

The next smallest additive step is therefore a cross-workspace latest-history bundle:

- broader than overview export because it includes transcript detail
- much smaller than a full cross-workspace archive because it includes only the latest snapshot per workspace

## Approaches Considered

### 1. Add a cross-workspace latest-history bundle route (recommended)

Pros:

- fills the gap between overview export and full archive work
- reuses the current latest-history merge semantics
- keeps payload bounded to one snapshot per workspace
- fits naturally beside the top-level `/terminals` overview

Cons:

- requires a small new service helper for latest snapshots across workspaces

### 2. Jump directly to full cross-workspace transcript archive

Pros:

- stronger archive story

Cons:

- much larger scope and payload
- unclear filtering and output contract across workspaces

### 3. Keep only the overview export

Pros:

- no additional backend work

Cons:

- leaves the current transcript-bundle gap unaddressed

## Recommended Approach

Use approach 1. Add a dedicated top-level latest-history bundle route that reuses the current latest snapshot merge semantics and overview workspace metadata, then expose it through one overview action.

## Route Contract

### Path

- `GET /terminals/history/export`

### Semantics

- applies the same auth and terminal-role checks as `GET /terminals`
- uses the same canonical web workspace inventory and ordering as the overview surface
- includes only workspaces that currently have terminal history
- returns `application/json`
- returns an attachment filename ending with `.json`

### Response Shape

Return a JSON object containing:

- `total`
- `items`
  - `group_id`
  - `group_name`
  - `chat_accessible`
  - `history`
    - same shape as `TerminalSessionHistoryDetailResponse`

If no workspaces currently have terminal history, return `404` to stay aligned with the existing history-export family.

## Backend Design

In `services/terminal_sessions.py`:

- add one helper that returns the latest merged snapshot for each workspace folder
- mirror the current `list_history_summaries()` merge semantics, but keep full snapshots

In `app/routes/terminals.py`:

- add a bundle filename helper
- add the new top-level history export route beside `/terminals` and `/terminals/export`
- reuse canonical web workspace discovery and ordering from the overview surface
- join workspace metadata with the new latest-snapshot helper

No persistence or ranking change is required.

## Frontend Design

In `web/src/api/client.ts`:

- add `downloadTerminalLatestHistories(token)`

In `web/src/pages/Terminals.tsx`:

- add one overview-level action:
  - `Export Latest Histories JSON`
- reuse the existing page-level `actionKey` / `actionError` / `actionNotice` state
- reuse the existing blob-download browser flow

## Testing Strategy

Service coverage:

- latest-history bundle helper returns one merged latest snapshot per workspace
- empty result returns an empty list so the route can map it to `404`

Backend coverage:

- latest-history bundle route returns JSON attachment content
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

- Risk: latest-history semantics could drift from current overview history signals.
  - Mitigation: derive bundle data from the same latest merged snapshot source used for overview history summaries.
- Risk: operators may confuse the bundle with full archive export.
  - Mitigation: label it explicitly as latest histories, not archive.

## Rollout

Additive operator-facing API/UI change only. No migration and no compatibility break for existing overview/history/search/detail contracts.
