# M8.5.61 Terminal Export UX Consistency Design

## Goal

Make the existing `/terminals` export and download actions more consistent for operators without changing any backend route, payload shape, RBAC rule, or terminal-history behavior.

## Scope

- keep the current export/download surface exactly the same:
  - overview export
  - latest-history bundle export
  - cross-workspace history archive export
  - workspace timeline current-page export
  - workspace timeline archive export
  - workspace search current-page export
  - workspace search archive export
  - history detail output / JSON download
- normalize button ordering across the page
- normalize success and failure notice wording across the page
- extract one local shared browser-download helper inside `web/src/pages/Terminals.tsx`
- keep the existing page-level `actionKey` / `actionError` / `actionNotice` state model

## Out Of Scope

- no new API route
- no response-contract or filename-contract change
- no new menu, modal, dropdown, or export center
- no terminal relevance or search behavior change
- no new frontend test framework
- no download queue, retry state machine, or background-job behavior

## Context

`M8.5.58` through `M8.5.60` filled the remaining terminal operator export gaps. The current `/terminals` page now exposes all needed operator-facing export actions, but the UI still reflects the order in which those capabilities were added:

- top-level export buttons are not ordered by scope progression
- timeline/search/detail sections each use slightly different export wording patterns
- download handlers repeat the same browser blob workflow many times
- success and error notices are correct but stylistically inconsistent

At this point the highest-value follow-up is not another new export surface. It is a small consistency pass that reduces operator friction and keeps future additive export work from further fragmenting the page.

## Approaches Considered

### 1. Only rename buttons and notices

Pros:

- lowest risk
- smallest patch

Cons:

- leaves repeated download logic untouched
- future export additions will keep copying the same browser-download flow

### 2. Normalize action language and extract one shared page-local download helper (recommended)

Pros:

- improves operator-facing consistency without expanding scope
- removes repeated blob-download code from multiple handlers
- preserves the existing page-level action-state model
- keeps all API contracts and existing action entry points intact

Cons:

- still leaves export actions distributed across four page sections

### 3. Build a dedicated export hub or grouped action menu

Pros:

- strongest structural consistency

Cons:

- much larger UX change
- higher regression risk on a page that is already operationally useful
- unnecessary before there is evidence that the current distributed layout is insufficient

## Recommended Approach

Use approach 2.

Treat this as a UI consistency and local-code-shape cleanup pass, not a product-surface expansion. Keep the existing sections and actions, but make them read and behave like one coherent export system.

## UX Design

### Overview Section

Keep the three top-level actions in the `Session Summary` section, but order them from smallest scope to largest scope:

- `Export Overview JSON`
- `Export Latest Histories JSON`
- `Export History Archive JSON`

This matches the progression from inventory -> latest snapshot bundle -> full archive bundle.

### Timeline Section

Keep the two timeline actions, but present them as the same scope progression used elsewhere:

- `Export Current Page JSON`
- `Export Archive JSON`

### Search Section

Keep the two search actions, also ordered from bounded result set to full result set:

- `Export Search Page JSON`
- `Export Search Archive JSON`

### Detail Section

Keep the current pair:

- `Download Output`
- `Download JSON`

These remain distinct because the detail surface is exporting one specific snapshot in two formats rather than switching between page/archive scopes.

## Frontend Design

In `web/src/pages/Terminals.tsx`:

- add one shared local helper for the repeated browser download flow:
  - request blob
  - create object URL
  - trigger anchor click
  - revoke object URL
- add one small wrapper to standardize:
  - clearing stale `actionError` / `actionNotice`
  - setting `actionKey`
  - success notice text
  - fallback failure notice text
- keep each individual handler focused on:
  - which API client method it calls
  - which filename builder it uses
  - which success/failure copy it passes to the shared wrapper

No shared abstraction is needed outside this page. The goal is to reduce repetition only where it already exists.

## Error Handling

- keep using the current page-level `actionError` and `actionNotice`
- clear stale notice/error state at the start of every export/download action
- preserve existing direct error-message passthrough when an `Error` object exists
- make fallback error copy scope-specific instead of overly generic

## API / Backend Impact

None.

This milestone does not change:

- `web/src/api/client.ts` route contracts
- any FastAPI route
- any response schema
- attachment filenames
- RBAC or workspace-access rules
- history persistence, search, or relevance ordering

## Testing Strategy

There is no dedicated frontend test harness in `web/`, so this pass will rely on minimal-scope regression verification:

- `cd web && npm run lint`
- `cd web && npm run build`
- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `git diff --check`

Because there is no backend contract change, new backend tests are not required for this milestone.

## Risks And Mitigations

- Risk: a helper extraction accidentally changes existing download behavior.
  - Mitigation: keep the helper page-local, preserve the exact blob-download flow, and do not change filename builders or client methods.
- Risk: a wider UI refactor spills into unrelated terminal interactions.
  - Mitigation: limit edits to export/download handlers and button ordering only.
- Risk: the patch grows into a redesign.
  - Mitigation: explicitly avoid menus, new state models, and cross-section componentization in this session.

## Rollout

Frontend-only additive polish on top of the current operator surface. No migration, no backend deployment concern, and no compatibility break.
