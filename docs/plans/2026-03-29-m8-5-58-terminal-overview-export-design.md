# M8.5.58 Terminal Overview Export Design

## Goal

Add a downloadable JSON export for the top-level `/terminals` overview so operators can preserve the current cross-workspace terminal session and latest-history inventory outside the browser without changing existing workspace-scoped export, relevance, or RBAC behavior.

## Scope

- add `GET /terminals/export`
- reuse the existing `/terminals` overview semantics
- return an `application/json` attachment containing the current `TerminalWorkspaceListResponse` payload
- add one `Export Overview JSON` action to the `/terminals` overview surface

## Out Of Scope

- no timeline/search/detail export changes
- no cross-workspace full transcript archive
- no ZIP/CSV/text bundle format
- no changes to `latest.json`, `/sessions/current/history`, or persistence layout
- no changes to terminal relevance / offline baseline / search sorting
- no changes to RBAC or workspace access rules

## Context

The terminal operator surface now supports export at three workspace-scoped layers:

- detail
- timeline/search current-page
- timeline/search all-pages archive

What remains missing is the top-level cross-workspace overview itself. Operators can already see the current workspace/session/history inventory on `/terminals`, but they cannot export that inventory snapshot without calling the API separately or copying the table manually.

The next smallest additive step is therefore not a larger transcript archive. It is giving the overview page the same export affordance that the deeper terminal surfaces now have.

## Approaches Considered

### 1. Add a top-level overview export route plus one UI action (recommended)

Pros:

- fills the remaining export gap in the current operator surface hierarchy
- reuses the existing overview payload and RBAC boundary directly
- smaller than cross-workspace transcript archive work
- provides a useful inventory snapshot without changing lower-level history contracts

Cons:

- exports summary/inventory data only, not transcript detail

### 2. Jump directly to cross-workspace transcript archive export

Pros:

- stronger archive story

Cons:

- much larger payload and scope jump
- unclear aggregation/output contract across workspaces
- unnecessary before the overview surface itself has export parity

### 3. Only polish export UX consistency

Pros:

- smaller frontend-only delta

Cons:

- leaves the remaining top-level export gap unaddressed

## Recommended Approach

Use approach 1. Add a dedicated overview export route that serializes the existing overview payload as a JSON attachment, then expose it through one extra action near the overview summary.

## Route Contract

### Path

- `GET /terminals/export`

### Semantics

- applies the same auth and terminal-role checks as `GET /terminals`
- reuses the same overview read model and ordering semantics
- returns `application/json`
- returns an attachment filename ending with `.json`

### Response Shape

Return the existing `TerminalWorkspaceListResponse` payload as a downloadable JSON attachment.

## Backend Design

In `app/routes/terminals.py`:

- add a helper for overview export filenames
- add the new export route beside the existing overview route
- reuse `list_terminal_overview(...)` logic rather than rebuilding overview state

No service or persistence change is required.

## Frontend Design

In `web/src/api/client.ts`:

- add `downloadTerminalOverview(...)`

In `web/src/pages/Terminals.tsx`:

- add one `Export Overview JSON` action near the session summary / workspace table
- reuse the existing page-level `actionKey` / `actionError` / `actionNotice` state
- reuse the existing blob-download browser flow

## Testing Strategy

Backend coverage:

- overview export returns JSON attachment content
- auth and role checks stay aligned with the overview route
- OpenAPI exposes the new overview export path

Frontend verification:

- `npm run build` and `npm run lint` cover the new helper and action wiring

Regression verification:

- focused terminal route/API tests
- `ruff`
- web lint/build
- `git diff --check`

## Risks And Mitigations

- Risk: overview export semantics could drift from the normal overview response.
  - Mitigation: reuse the existing overview route logic / payload construction.
- Risk: operators may mistake overview export for transcript archive export.
  - Mitigation: keep the action label explicit about exporting overview JSON, not history output.

## Rollout

Additive operator-facing API/UI change only. No migration and no compatibility break for existing terminal overview/history/search/detail contracts.
