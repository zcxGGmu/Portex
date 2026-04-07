# Session Plan (2026-04-06) - M8.5.62 Terminal Cross-Workspace History Archive Filters

## Goal
- Continue post-`M8.5.61` terminal operator development by adding minimal owner/session/time filters to the top-level cross-workspace history archive export on `/terminals`, with a matching small top-level UI, without changing overview export, latest-history export, workspace-scoped history surfaces, or terminal-history semantics.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current top-level archive implementation
- [x] Confirm the next step should stay on the top-level cross-workspace archive path
- [x] Write focused `M8.5.62` design doc
- [x] Write focused `M8.5.62` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing service/route/OpenAPI coverage for top-level archive filters
- [x] Implement filtered top-level archive backend behavior
- [x] Add `/terminals` top-level archive filter UI and client wiring
- [x] Run focused regression plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added RED coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for grouped archive filter forwarding, empty-group omission, invalid time bounds, response `filters` metadata, and OpenAPI query parameter exposure.
- Extended `services/terminal_sessions.py` so `list_history_snapshot_archives_by_groups(...)` now validates and applies `owner_user_id`, `session_id_prefix`, `snapshot_from`, and `snapshot_to` with the same helper semantics already used by workspace-scoped timeline/search/export surfaces.
- Extended `app/routes/terminals.py` so `GET /terminals/history/archive` accepts the same four optional query parameters, maps invalid bounds through the existing terminal error boundary, and echoes applied filter values in a top-level `filters` object without changing the grouped archive payload, filename, RBAC, or `404` empty-result behavior.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` with an archive-only filter state slice and compact top-level UI inputs for owner, session prefix, and local datetime bounds; only `Export History Archive JSON` consumes these filters, while overview and latest-history exports remain unfiltered.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit for this session: `feat(terminal): add M8.5.62 cross-workspace history archive filters`

# Session Plan (2026-04-06) - M8.5.61 Terminal Export UX Consistency

## Goal
- Continue post-`M8.5.60` terminal operator development by making the existing `/terminals` export/download actions more consistent in wording, ordering, and local implementation shape without changing backend contracts, filenames, RBAC, or terminal-history behavior.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current `/terminals` export slices
- [x] Confirm the next step should stay on operator-surface UX consistency instead of adding another export capability
- [x] Write focused `M8.5.61` design doc
- [x] Write focused `M8.5.61` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add a small RED signal for the shared frontend download helper refactor
- [x] Implement the `/terminals` export/download UX consistency pass
- [x] Run focused regression plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-04-06-m8-5-61-terminal-export-ux-consistency-design.md` and `docs/plans/2026-04-06-m8-5-61-terminal-export-ux-consistency.md` to lock the frontend-only UX consistency scope before touching code.
- Created the RED signal by switching one `/terminals` export handler to a not-yet-defined shared helper, then verified `cd web && npm run build` failed with `TS2304: Cannot find name 'runTerminalDownloadAction'`.
- Refactored `web/src/pages/Terminals.tsx` so overview, latest-history, cross-workspace archive, timeline current-page/archive, search current-page/archive, and detail output/JSON actions now reuse one shared browser download flow plus one shared action-state wrapper.
- Reordered `/terminals` export buttons into consistent bounded-to-broader scope order: overview -> latest histories -> history archive at the top level, current page -> archive for timeline, and search page -> search archive for search results.
- Normalized detail download copy to `Download Output` / `Download JSON` backed by consistent success/failure notice wording, without changing any FastAPI route, response payload, filename builder, RBAC boundary, or page-level action-state model.
- Verification executed:
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `git diff --check`
- Planning commit completed in this session: `9a3d2ad` (`docs(plans): add M8.5.61 terminal export UX consistency plan`).
- Feature commit completed in this session: `b870f70` (`feat(web): add M8.5.61 terminal export UX consistency`).
- Planned handoff sync commit for this doc update: `docs(handoff): sync M8.5.61 terminal export UX consistency context`.

# Session Plan (2026-03-30) - M8.5.60 Terminal Cross-Workspace History Archive Export

## Goal
- Continue post-`M8.5.59` terminal operator development by adding a cross-workspace downloadable JSON archive for all terminal-history snapshots across canonical web workspaces on `/terminals`, extending the current latest-history bundle into a full transcript archive without changing existing workspace-scoped export contracts.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current terminal top-level export/archive slices
- [x] Confirm the next step should broaden from latest-history bundle to full cross-workspace archive instead of only doing UX polish
- [x] Write focused `M8.5.60` design doc
- [x] Write focused `M8.5.60` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing service/route/OpenAPI coverage for cross-workspace history archive export
- [x] Implement additive backend cross-workspace history archive behavior
- [x] Add frontend client wiring and `/terminals` cross-workspace archive action
- [x] Run focused verification plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-30-m8-5-60-terminal-cross-workspace-history-archive-export-design.md` and `docs/plans/2026-03-30-m8-5-60-terminal-cross-workspace-history-archive-export.md` to lock the cross-workspace grouped archive scope before code changes.
- Added RED coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for the new grouped archive helper, top-level archive route, auth/role behavior, and OpenAPI exposure.
- Extended `services/terminal_sessions.py` with `list_history_snapshot_archives_by_groups(...)`, reusing the existing per-workspace merged snapshot semantics while grouping full snapshot lists by workspace folder.
- Added `GET /terminals/history/archive` in `app/routes/terminals.py`, returning a grouped JSON archive across canonical web workspaces with workspace metadata, per-workspace totals, and full `TerminalSessionHistoryDetailResponse`-shaped items.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so the overview surface now exposes `Export History Archive JSON`, while preserving the existing overview export, latest-history bundle export, and all workspace-scoped export actions.
- Overview export, latest-history bundle export, detail export, timeline/search current-page export, timeline/search archive export, terminal relevance ordering, the `81`-case offline baseline, `latest.json`, `/sessions/current/history`, and RBAC/workspace-access semantics remain unchanged.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit completed in this session: `086fbe0` (`feat(terminal): add M8.5.60 cross-workspace history archive export`).
- Planned handoff sync commit for this doc update: `docs(handoff): sync M8.5.60 cross-workspace history archive export context`.

# Session Plan (2026-03-29) - M8.5.59 Terminal Latest History Bundle Export

## Goal
- Continue post-`M8.5.58` terminal operator development by adding a cross-workspace downloadable JSON bundle for the latest terminal-history snapshot of each workspace on `/terminals`, bridging the gap between overview-only export and heavier cross-workspace transcript archive work.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current terminal overview/history export slices
- [x] Confirm the next step should add a cross-workspace latest-history bundle instead of jumping directly to a full transcript archive
- [x] Write focused `M8.5.59` design doc
- [x] Write focused `M8.5.59` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing service/route/OpenAPI coverage for latest-history bundle export
- [x] Implement additive backend latest-history bundle export behavior
- [x] Add frontend client wiring and `/terminals` latest-history bundle export action
- [x] Run focused verification plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-29-m8-5-59-terminal-latest-history-bundle-export-design.md` and `docs/plans/2026-03-29-m8-5-59-terminal-latest-history-bundle-export.md` to lock the cross-workspace latest-history bundle scope before code changes.
- Added RED coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for the new latest-history helper, bundle route, auth/role behavior, and OpenAPI exposure.
- Extended `services/terminal_sessions.py` with `list_latest_history_snapshots()`, mirroring the current merged latest-history summary semantics while keeping full snapshot payloads.
- Added `GET /terminals/history/export` in `app/routes/terminals.py`, returning a JSON bundle of the latest terminal-history snapshot for each workspace with history, joined with overview workspace metadata.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so the overview surface now exposes `Export Latest Histories JSON`, while preserving the existing overview export and all workspace-scoped export actions.
- Overview export, detail export, timeline/search current-page export, timeline/search archive export, terminal relevance ordering, the `81`-case offline baseline, `latest.json`, `/sessions/current/history`, and RBAC/workspace-access semantics remain unchanged.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit completed in this session: `89d696a` (`feat(terminal): add M8.5.59 latest history bundle export`).
- Planned handoff sync commit for this doc update: `docs(handoff): sync M8.5.59 latest history bundle export context`.

# Session Plan (2026-03-29) - M8.5.58 Terminal Overview Export

## Goal
- Continue post-`M8.5.57` terminal operator development by adding a downloadable JSON export for the top-level `/terminals` overview surface, so operators can preserve the current cross-workspace session/history inventory without changing existing timeline/search/detail/archive contracts.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current terminal overview/export slices
- [x] Confirm the next step should fill the remaining top-level overview export gap before larger cross-workspace transcript archive work
- [x] Write focused `M8.5.58` design doc
- [x] Write focused `M8.5.58` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing route/OpenAPI coverage for overview export
- [x] Implement additive backend overview export behavior
- [x] Add frontend client wiring and `/terminals` overview JSON export action
- [x] Run focused verification plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-29-m8-5-58-terminal-overview-export-design.md` and `docs/plans/2026-03-29-m8-5-58-terminal-overview-export.md` to lock the top-level overview export scope before code changes.
- Added RED coverage in `tests/app/routes/test_terminal_routes.py` and `tests/app/routes/test_api_routes.py` for the new overview export route, auth/role behavior, and OpenAPI exposure.
- Added `GET /terminals/export` in `app/routes/terminals.py`, reusing the existing overview payload construction and returning the current `TerminalWorkspaceListResponse` as a JSON attachment.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so the overview surface now exposes `Export Overview JSON`, reusing the existing blob-download flow and page-level action/error state.
- Timeline/search/detail/archive export behavior, terminal relevance ordering, the `81`-case offline baseline, `latest.json`, `/sessions/current/history`, and RBAC/workspace-access semantics remain unchanged.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit completed in this session: `c710a74` (`feat(terminal): add M8.5.58 overview export`).
- Planned handoff sync commit for this doc update: `docs(handoff): sync M8.5.58 overview export context`.

# Session Plan (2026-03-29) - M8.5.57 Terminal History Search Archive Export

## Goal
- Continue post-`M8.5.56` terminal operator development by adding an all-pages downloadable JSON archive for the current terminal-history search result set on `/terminals`, reusing existing search query/filter/sort semantics while preserving current-page export, timeline archive, detail export, relevance, and RBAC contracts.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current terminal search/archive slices
- [x] Confirm the next step should cross the current-page boundary on the search operator surface
- [x] Write focused `M8.5.57` design doc
- [x] Write focused `M8.5.57` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing route/OpenAPI coverage for filtered all-pages search archive export
- [x] Implement additive backend filtered search archive export behavior
- [x] Add frontend client wiring and `/terminals` search archive JSON export action
- [x] Run focused verification plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-29-m8-5-57-terminal-history-search-archive-export-design.md` and `docs/plans/2026-03-29-m8-5-57-terminal-history-search-archive-export.md` to lock the search all-pages archive scope before code changes.
- Added RED coverage in `tests/app/routes/test_terminal_routes.py` and `tests/app/routes/test_api_routes.py` for the new search archive route, auth/error behavior, and OpenAPI parameter exposure.
- Added `GET /terminals/{group_id}/sessions/history/search/archive` in `app/routes/terminals.py`, reusing `search_history_by_group(...)` in an all-results fetch path and returning the full filtered search result set as a JSON attachment with query, sort, filters, total, and existing match/snippet payloads.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so the search panel now exposes `Export Search Archive JSON`, while preserving the existing current-page search export button and shared action/error state.
- Timeline archive export, timeline current-page export, search current-page export, detail download `format=text|json`, terminal relevance ordering, the `81`-case offline baseline, `latest.json`, `/sessions/current/history`, and RBAC/workspace-access semantics remain unchanged.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit completed in this session: `60656f7` (`feat(terminal): add M8.5.57 history search archive export`).
- Planned handoff sync commit for this doc update: `docs(handoff): sync M8.5.57 history search archive export context`.

# Session Plan (2026-03-29) - M8.5.56 Terminal History Archive Export

## Goal
- Continue post-`M8.5.55` terminal operator development by adding an all-pages downloadable JSON archive for the current filtered terminal-history timeline on `/terminals`, reusing existing timeline filter semantics while preserving current-page export, detail export, relevance, and RBAC contracts.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current terminal export/archive slices
- [x] Confirm the next step should cross the current-page boundary and stay on the timeline operator surface
- [x] Write focused `M8.5.56` design doc
- [x] Write focused `M8.5.56` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing service/route/OpenAPI coverage for filtered all-pages archive export
- [x] Implement additive backend filtered archive export behavior
- [x] Add frontend client wiring and `/terminals` archive JSON export action
- [x] Run focused verification plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-29-m8-5-56-terminal-history-archive-export-design.md` and `docs/plans/2026-03-29-m8-5-56-terminal-history-archive-export.md` to lock the all-pages timeline archive scope before code changes.
- Added RED coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for the new full filtered snapshot helper, archive route, auth/error behavior, and OpenAPI parameter exposure.
- Extended `services/terminal_sessions.py` with `list_history_snapshots_by_group(...)`, reusing the existing merged snapshot ordering and filter path to return the full filtered timeline slice for one workspace.
- Added `GET /terminals/{group_id}/sessions/history/archive` in `app/routes/terminals.py`, returning a JSON attachment with full filter metadata, total count, and all matching `TerminalSessionHistoryDetailResponse`-shaped items.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so the timeline panel now exposes `Export Archive JSON`, while preserving the existing current-page export button and shared action/error state.
- Current-page timeline export, search current-page export, detail download `format=text|json`, terminal relevance ordering, the `81`-case offline baseline, `latest.json`, `/sessions/current/history`, and RBAC/workspace-access semantics remain unchanged.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit completed in this session: `b549d6a` (`feat(terminal): add M8.5.56 history archive export`).
- Planned handoff sync commit for this doc update: `docs(handoff): sync M8.5.56 history archive export context`.

# Session Plan (2026-03-29) - M8.5.55 Terminal History Search Export

## Goal
- Continue post-`M8.5.54` terminal operator development by adding a bounded downloadable JSON export for the current terminal-history search result page on `/terminals`, reusing existing search query/filter/pagination semantics while preserving timeline/detail/relevance/RBAC contracts.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current terminal search/export slices
- [x] Confirm the next step should stay on operator-surface export work and remain narrower than workspace-wide archive export
- [x] Write focused `M8.5.55` design doc
- [x] Write focused `M8.5.55` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing route/OpenAPI coverage for bounded search-result export
- [x] Implement additive backend bounded search-result export behavior
- [x] Add frontend client wiring and `/terminals` current search-page JSON export action
- [x] Run focused verification plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-29-m8-5-55-terminal-history-search-export-design.md` and `docs/plans/2026-03-29-m8-5-55-terminal-history-search-export.md` to lock the bounded search-export scope before code changes.
- Added RED coverage in `tests/app/routes/test_terminal_routes.py` and `tests/app/routes/test_api_routes.py` for the new search export route, auth/error behavior, and OpenAPI parameter exposure.
- Added `GET /terminals/{group_id}/sessions/history/search/export` in `app/routes/terminals.py`, reusing `search_history_by_group(...)` and returning the current search page as a JSON attachment with query, sort, filters, pagination metadata, and existing match/snippet payloads.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so the search panel now exposes `Export Search Page JSON`, reusing the existing blob-download flow and page-level action/error state.
- `M8.5.54` timeline bulk export, detail download `format=text|json`, terminal relevance ordering, the `81`-case offline baseline, `latest.json`, `/sessions/current/history`, and RBAC/workspace-access semantics remain unchanged.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit completed in this session: `5b034c1` (`feat(terminal): add M8.5.55 history search export`).
- Planned handoff sync commit for this doc update: `docs(handoff): sync M8.5.55 history search export context`.

# Session Plan (2026-03-29) - M8.5.54 Terminal History Bulk JSON Export

## Goal
- Continue post-`M8.5.53` terminal operator development by adding a bounded downloadable JSON export for the current filtered terminal-history page on `/terminals`, reusing existing timeline filters/pagination while exporting multiple full snapshot detail records and preserving detail/search/relevance/RBAC contracts.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current terminal timeline/detail export slices
- [x] Confirm the next step should stay on operator-surface export work and remain narrower than workspace-wide archive export
- [x] Write focused `M8.5.54` design doc
- [x] Write focused `M8.5.54` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing route/service/OpenAPI coverage for bounded bulk history export
- [x] Implement additive backend bounded bulk history export behavior
- [x] Add frontend client wiring and `/terminals` current-page JSON export action
- [x] Run focused verification plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-29-m8-5-54-terminal-history-bulk-json-export-design.md` and `docs/plans/2026-03-29-m8-5-54-terminal-history-bulk-json-export.md` to lock the bounded bulk-export scope before code changes.
- Added RED coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for the new bounded bulk-detail page helper, export route, auth/error behavior, and OpenAPI parameter exposure.
- Extended `services/terminal_sessions.py` with `list_history_snapshot_page_by_group(...)`, reusing the existing merged snapshot ordering and filter path while adding only bounded page metadata (`limit`, `offset`, `total`, `has_more`) for full snapshot records.
- Added `GET /terminals/{group_id}/sessions/history/export` in `app/routes/terminals.py`, returning a JSON attachment that includes current filter metadata plus multiple `TerminalSessionHistoryDetailResponse`-shaped items for the selected page.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so the timeline panel now exposes `Export Current Page JSON`, reusing the existing blob-download flow and page-level action/error state.
- `latest.json`, `/sessions/current/history`, detail download `format=text|json`, terminal relevance ordering, the `81`-case offline baseline, and RBAC/workspace-access semantics remain unchanged.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit completed in this session: `302b19f` (`feat(terminal): add M8.5.54 history bulk export`).
- Planned handoff sync commit for this doc update: `docs(handoff): sync M8.5.54 history bulk export context`.

# Session Plan (2026-03-27) - Restart Context Sync After M8.5.53

## Goal
- Refresh `docs/progress.md` and `AGENTS.md` so the restart-oriented handoff points at the latest `M8.5.53` sync state on `main`, then commit the doc-only update.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current branch status
- [x] Update `docs/progress.md` with the latest restart-oriented anchors
- [x] Update `AGENTS.md` with the latest handoff reference notes
- [x] Refresh the current `tasks/todo.md` session record for this doc-only sync
- [x] Check doc consistency and diff hygiene
- [x] Commit changes with a detailed message

## Review
- Refreshed `docs/progress.md` so the restart header now points at the latest `M8.5.53` handoff commit `a14ca20`, while keeping the current functional state and next-step guidance intact.
- Refreshed `AGENTS.md` so its baseline snapshot date and restart metadata now point at the latest `M8.5.53` handoff sync, without changing milestone content or execution guidance.
- Refreshed `tasks/todo.md` with this doc-only sync record so the next session can distinguish `M8.5.53` functional work from the follow-up restart-context maintenance.
- This sync is doc-only: no terminal export behavior, relevance baseline, API contract, UI, or RBAC behavior changed.
- Consistency check: `git diff --check` passed before commit.
- Planned commit message for this sync: `docs(handoff): refresh restart context after M8.5.53`.

# Session Plan (2026-03-26) - M8.5.53 Terminal History Detail Metadata Export

## Goal
- Continue post-`M8.5.52` terminal operator development by extending terminal history detail download with an additive JSON metadata export, while keeping raw text download as the default and preserving all existing terminal relevance, detail, and RBAC contracts.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current terminal detail/download slices
- [x] Confirm the next terminal step should stay on operator surface work instead of returning to the converged relevance baseline
- [x] Write focused `M8.5.53` design doc
- [x] Write focused `M8.5.53` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing route/OpenAPI coverage for format-aware terminal history download
- [x] Implement additive backend `format=text|json` terminal history download behavior
- [x] Add frontend client wiring and `/terminals` JSON metadata download action
- [x] Run focused verification plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-26-m8-5-53-terminal-history-detail-metadata-export-design.md` and `docs/plans/2026-03-26-m8-5-53-terminal-history-detail-metadata-export.md` to lock the additive operator-surface scope before code changes.
- Added RED coverage in `tests/app/routes/test_terminal_routes.py` and `tests/app/routes/test_api_routes.py` for `format=json`, invalid-format `422`, JSON-path `404`, and OpenAPI download-parameter exposure while keeping the existing raw text path intact.
- Extended `GET /terminals/{group_id}/sessions/history/{session_id}/download` in `app/routes/terminals.py` with `format=text|json` support. `text` remains the default raw transcript attachment; `json` returns the existing history detail payload as a downloadable `application/json` attachment.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so the history detail panel now exposes both `Download Output` and `Download JSON`, reusing the existing blob-download flow and shared action/error state.
- `services/terminal_sessions.py`, terminal relevance ordering, the `81`-case offline baseline, `latest.json`, `/sessions/current/history`, and terminal RBAC/search semantics remain unchanged.
- Verification executed:
  - `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit completed in this session: `0402678` (`feat(terminal): add M8.5.53 history detail metadata export`).
- Planned handoff sync commit for this doc update: `docs(handoff): sync M8.5.53 history detail metadata export context`.

# Session Plan (2026-03-26) - M8.5.52 Terminal History Detail Download

## Goal
- Continue post-convergence terminal development by adding a raw terminal-history download action on `/terminals`, so operators can export one persisted history snapshot without changing existing timeline/search/detail contracts or ranking behavior.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current terminal detail route/UI slices
- [x] Inspect the existing terminal history detail service/route/frontend path and choose the smallest additive download contract
- [x] Write focused `M8.5.52` design doc
- [x] Write focused `M8.5.52` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing backend route/OpenAPI coverage for terminal history download
- [x] Implement additive backend terminal history download route
- [x] Add frontend client wiring and `/terminals` detail download action
- [x] Run focused verification plus frontend lint/build and diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md` if needed, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-26-m8-5-52-terminal-history-detail-download-design.md` and `docs/plans/2026-03-26-m8-5-52-terminal-history-detail-download.md` to lock the additive operator-surface scope before touching backend or frontend code.
- Added RED coverage in `tests/app/routes/test_terminal_routes.py` and `tests/app/routes/test_api_routes.py` for the new terminal history download route, including auth, success, missing-session `404`, and OpenAPI exposure.
- Implemented `GET /terminals/{group_id}/sessions/history/{session_id}/download` in `app/routes/terminals.py`, reusing the existing accessible-workspace and snapshot-lookup path and returning a sanitized `text/plain` attachment filename.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so `/terminals` history detail now exposes a `Download Output` action backed by the existing blob-download browser flow.
- `services/terminal_sessions.py`, the `81`-case offline relevance baseline, `latest.json`, `/sessions/current/history`, and terminal RBAC/search semantics remain unchanged in this session.
- Verification executed:
  - `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit completed in this session: `b044de6` (`feat(terminal): add M8.5.52 history detail download`).
- Planned handoff sync commit for this doc update: `docs(handoff): sync M8.5.52 history detail download context`.

# Session Plan (2026-03-26) - Restart Context Sync After Convergence Audit

## Goal
- Refresh `docs/progress.md` and `AGENTS.md` so the restart-oriented handoff points at the latest convergence-audit sync state on `main`, then commit the doc-only update.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current branch status
- [x] Update `docs/progress.md` with the latest restart-oriented anchors
- [x] Update `AGENTS.md` with the latest handoff reference notes
- [x] Refresh the current `tasks/todo.md` session record for this doc-only sync
- [x] Check doc consistency and diff hygiene
- [x] Commit changes with a detailed message

## Review
- Refreshed `docs/progress.md` so the restart header now points at the latest convergence-audit handoff commit `2ee97f9`, while keeping the current `M8.5.51` + `81`-case baseline, latest functional commit, and next-step guidance intact.
- Refreshed `AGENTS.md` so its restart metadata now points at the latest handoff sync commit `2ee97f9`, while preserving the approved convergence-audit baseline and restart instructions.
- Refreshed `tasks/todo.md` with this doc-only sync record so the next session can distinguish baseline convergence work from a follow-up handoff refresh.
- This sync is doc-only: no terminal ranking logic, offline fixture, API, UI, or RBAC behavior changed.
- Consistency check: `git diff --check` passed before commit.
- Planned commit message for this sync: `docs(handoff): refresh restart context after convergence audit`.

# Session Plan (2026-03-26) - Terminal Relevance Baseline Convergence Audit

## Goal
- Audit the current `81`-case offline terminal relevance baseline against landed `M8.5.17` ~ `M8.5.51` service semantics, then either document convergence or patch only a real non-duplicate offline gap.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, current terminal relevance fixture/tests, and recent commits
- [x] Write focused convergence-audit design doc
- [x] Write focused convergence-audit implementation plan doc
- [x] Add this session checklist before implementation
- [x] Audit `tests/services/test_terminal_sessions.py` against `tests/fixtures/terminal_relevance_baseline.json` and decide whether any non-duplicate gap remains
- [x] If and only if the audit finds a real gap, add the smallest missing fixture/test coverage without touching `services/terminal_sessions.py`
- [x] Run the appropriate verification commands for the actual diff
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit planning updates and final handoff sync with detailed messages

## Review
- Added `docs/plans/2026-03-26-terminal-relevance-offline-baseline-convergence-audit-design.md` and `docs/plans/2026-03-26-terminal-relevance-offline-baseline-convergence-audit.md` to lock the approved scope before deciding whether any more offline relevance expansion is justified.
- Audited `M8.5.17` ~ `M8.5.51` service semantics against the current `81`-case fixture and confirmed there is no remaining non-duplicate offline gap to add right now. In particular, `M8.5.50` direct count + pagination are already fixed by `m8-5-50-mixed-other-count` and `m8-5-50-mixed-other-count-pagination`; `M8.5.51` direct offset + pagination are already fixed by `m8-5-51-mixed-other-offset` and `m8-5-51-mixed-other-offset-pagination`; mixed-other no-single-space fallback is already fixed by `no-single-space-fallback` and `m8-5-51-no-single-space-fallback-pagination`.
- This session intentionally does not change `services/terminal_sessions.py`, `tests/fixtures/terminal_relevance_baseline.json`, or `tests/scripts/test_evaluate_terminal_relevance.py`; the baseline is treated as converged until new evidence appears.
- Verification executed:
  - `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q`
  - `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=81`, `pass_count=81`, `pass_rate/top1_accuracy/mrr = 1.000`)
  - `git diff --check`
- Planning commit: `70cb8dd` (`docs(plans): add offline relevance convergence audit plan`).
- This session intentionally has no feature commit because the convergence audit found no new fixture or ranking change to land; the closing handoff commit is `docs(handoff): sync offline relevance convergence audit context`.

# Session Plan (2026-03-26) - Restart Context Sync

## Goal
- Refresh `docs/progress.md` and `AGENTS.md` so the restart-oriented handoff matches the latest foundational-ranking baseline and current branch state, then commit the doc sync.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current branch status
- [x] Update `docs/progress.md` with the latest restart-oriented status
- [x] Update `AGENTS.md` with the latest baseline and handoff reference notes
- [x] Refresh the current `tasks/todo.md` session record for this doc-only sync
- [x] Check doc consistency and diff hygiene
- [x] Commit changes with a detailed message

## Review
- Refreshed `docs/progress.md` so the restart header now points at the latest foundational-ranking handoff commit on the branch while keeping the current `81`-case offline baseline, verification evidence, and next-step guidance intact.
- Refreshed `AGENTS.md` so its baseline snapshot date and restart metadata now point at the latest foundational-ranking handoff sync commit `46fcf2e`, while preserving the current `M8.5.51` + `81`-case offline baseline snapshot.
- Refreshed `tasks/todo.md` with this doc-only sync record so the next session can distinguish restart-context maintenance from fixture/ranking work.
- This sync is doc-only: no fixture, ranking logic, API, UI, or RBAC behavior changed.
- Consistency check: `git diff --check` passed before commit.

# Session Plan (2026-03-25) - Offline Relevance Foundational Ranking Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by fixing the remaining foundational `M8.5.17` relevance semantics into the offline harness before considering any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the foundational `M8.5.17` service-level tests
- [x] Confirm the current 77-case fixture still lacks the non-duplicate foundational ranking cases for concentrated-vs-sparse ordering, first-match offset tie-break, weak recency, and base pagination
- [x] Write the design doc and implementation plan docs for this foundational ranking expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with the four foundational ranking cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the current 77-case fixture still lacked four non-duplicate foundational `M8.5.17` semantics: concentrated-vs-sparse ordering, first-match offset tie-break, weak recency, and base pagination over the globally ranked result set.
- Added `docs/plans/2026-03-25-terminal-relevance-offline-baseline-foundational-relevance-expansion-design.md` and `docs/plans/2026-03-25-terminal-relevance-offline-baseline-foundational-relevance-expansion.md` to lock scope before touching fixture data.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 81-case RED expectations, captured the expected failure against the committed 77-case fixture, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four service-test-derived scenarios: clustered-match priority, first-match offset tie-break, weak-recency tie-break, and foundational pagination.
- This batch intentionally avoided `services/terminal_sessions.py`; it adds offline evidence only, preserving ranking behavior, terminal APIs, RBAC boundaries, `latest.json`, and `/sessions/current/history`.
- Planning commit: `17b1fc1` (`docs(plans): add offline relevance foundational ranking plan`).
- Feature commit: `cdf21cb` (`feat(terminal): expand offline relevance foundational ranking fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=81`, `pass_count=81`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-25) - Offline Relevance Direct Whitespace-Family Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by exhausting the remaining direct whitespace-family service-test gaps before considering any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant whitespace-family service-level tests
- [x] Confirm the current 70-case fixture already covers pagination and no-single-space fallback for the whitespace families, and isolate the remaining non-duplicate gaps to the direct count/offset comparisons for `M8.5.43` ~ `M8.5.49`
- [x] Write the design doc and implementation plan docs for this direct whitespace-family expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with the seven remaining direct whitespace-family cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the current 70-case fixture had already exhausted whitespace-family pagination and no-single-space fallback coverage; the remaining non-duplicate service-level gaps were the seven direct count/offset comparisons for `M8.5.43` ~ `M8.5.49`.
- Added `docs/plans/2026-03-25-terminal-relevance-offline-baseline-direct-whitespace-family-expansion-design.md` and `docs/plans/2026-03-25-terminal-relevance-offline-baseline-direct-whitespace-family-expansion.md` to lock scope before touching fixture data.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 77-case RED expectations, captured the expected failure against the committed 70-case fixture, then expanded `tests/fixtures/terminal_relevance_baseline.json` with seven direct service-test-derived scenarios: tab separator-quality, tab offset tie-break, multi-space separator-quality, multi-space offset tie-break, space-prefixed mixed-whitespace separator-quality, space-prefixed mixed-whitespace offset tie-break, and other-leading whitespace offset tie-break.
- This batch intentionally avoided `services/terminal_sessions.py`; it adds offline evidence only, preserving ranking behavior, terminal APIs, RBAC boundaries, `latest.json`, and `/sessions/current/history`.
- Planning commit: `9a35949` (`docs(plans): add offline relevance direct whitespace-family plan`).
- Feature commit: `272b487` (`feat(terminal): expand offline relevance direct whitespace-family fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=77`, `pass_count=77`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-25) - Restart Context Sync

## Goal
- Refresh `docs/progress.md` and `AGENTS.md` so the restart-oriented handoff matches the latest whitespace-fallback baseline and current branch state, then commit the doc sync.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current branch status
- [x] Update `docs/progress.md` with the latest restart-oriented status
- [x] Update `AGENTS.md` with the latest baseline and handoff reference notes
- [x] Refresh the current `tasks/todo.md` session record for this doc-only sync
- [x] Check doc consistency and diff hygiene
- [x] Commit changes with a detailed message

## Review
- Refreshed `docs/progress.md` so the restart header now points at the latest whitespace-fallback handoff commit on the branch while keeping the current `70`-case offline baseline, verification evidence, and next-step guidance intact.
- Refreshed `AGENTS.md` so its restart metadata now points at the latest handoff sync commit `8ef608c`, preserving the current `M8.5.51` + `70`-case offline baseline snapshot.
- This sync is doc-only: no fixture, ranking logic, API, UI, or RBAC behavior changed.
- Consistency check: `git diff --check` passed before commit.

# Session Plan (2026-03-25) - Offline Relevance Whitespace Fallback Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding the remaining whitespace-family no-single-space fallback branches before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant whitespace-family service-level tests
- [x] Confirm the current 66-case fixture already covers the last planned pagination gaps, and isolate the actual uncovered branches to the tab-prefixed / multi-space / space-prefixed mixed-whitespace / other-leading whitespace no-single-space fallback cases
- [x] Write the design doc and implementation plan docs for this whitespace fallback expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with the four whitespace-family no-single-space fallback cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the current 66-case fixture had already exhausted the last planned payload/whitespace pagination gaps, so this batch stayed baseline-first and targeted the remaining non-duplicate whitespace-family fallback evidence instead of duplicating pagination cases.
- Added `docs/plans/2026-03-25-terminal-relevance-offline-baseline-whitespace-fallback-expansion-design.md` and `docs/plans/2026-03-25-terminal-relevance-offline-baseline-whitespace-fallback-expansion.md` to lock the fallback-only scope before changing fixture data.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 70-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four service-test-derived scenarios: tab-prefixed payload fallback, multi-space payload fallback, space-prefixed mixed-whitespace fallback, and other-leading whitespace fallback when no single-space plain exact-tag signal exists.
- This batch intentionally avoided `services/terminal_sessions.py`; it adds offline evidence only, preserving ranking behavior, terminal APIs, RBAC boundaries, `latest.json`, and `/sessions/current/history`.
- Planning commit: `913a6b1` (`docs(plans): add offline relevance whitespace fallback plan`).
- Feature commit: `f4ff3fa` (`feat(terminal): expand offline relevance whitespace fallback fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=70`, `pass_count=70`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-25) - Offline Relevance Final Payload Pagination Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by closing the final uncovered payload/whitespace-family pagination gaps before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant remaining payload/whitespace pagination service-level tests
- [x] Write the design doc and implementation plan docs for this final payload pagination expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with multi-space-payload and space-prefixed-mixed-whitespace-payload pagination cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 64 to 66 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-25-terminal-relevance-offline-baseline-final-payload-pagination-expansion-design.md` and `docs/plans/2026-03-25-terminal-relevance-offline-baseline-final-payload-pagination-expansion.md` to lock scope, case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 66-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with two service-test-derived scenarios: `M8.5.45` multi-space-payload pagination and `M8.5.47` space-prefixed-mixed-whitespace-payload pagination.
- This batch is intentionally only two cases because adjacent payload-family pagination samples were already represented in the fixture; forcing a 4-case batch here would only duplicate evidence.
- Planning commit: `946f202` (`docs(plans): add offline relevance final payload pagination plan`).
- Feature commit: `91cdb9c` (`feat(terminal): expand offline relevance final payload pagination fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=66`, `pass_count=66`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-25) - Offline Relevance Payload And Offset Pagination Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding the next uncovered payload-family pagination samples plus the remaining square-bracket plain-offset pagination sample before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant payload/offset pagination service-level tests
- [x] Write the design doc and implementation plan docs for this payload/offset pagination expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with payloadless-separator, payloadless-offset, tab-prefixed-payload, and square-bracket-plain-offset pagination cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 60 to 64 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-25-terminal-relevance-offline-baseline-payload-and-offset-pagination-expansion-design.md` and `docs/plans/2026-03-25-terminal-relevance-offline-baseline-payload-and-offset-pagination-expansion.md` to lock scope, case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 64-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four service-test-derived scenarios: `M8.5.41` payloadless-separator pagination, `M8.5.42` payloadless-offset pagination, `M8.5.43` tab-prefixed-payload pagination, and square-bracket plain exact-tag offset pagination.
- This batch keeps the baseline coherent around the payload/offset tail of the exact-tag quality chain, while also clearing the last explicitly-called-out square-bracket plain-offset pagination gap.
- Planning commit: `85a449b` (`docs(plans): add offline relevance payload and offset pagination plan`).
- Feature commit: `4276c59` (`feat(terminal): expand offline relevance payload and offset pagination fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=64`, `pass_count=64`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-25) - Offline Relevance Late Quality Pagination Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding the next uncovered later-stage quality-family pagination samples before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant later quality pagination service-level tests
- [x] Write the design doc and implementation plan docs for this later quality pagination expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with delimited-log-marker, exact-tag-punctuation-noise, single-space plain exact-tag, and separator-noise pagination cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 56 to 60 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-25-terminal-relevance-offline-baseline-late-quality-pagination-expansion-design.md` and `docs/plans/2026-03-25-terminal-relevance-offline-baseline-late-quality-pagination-expansion.md` to lock scope, case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 60-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four service-test-derived scenarios: `M8.5.24` delimited-log-marker pagination, `M8.5.35` exact-tag-punctuation-noise pagination, `M8.5.39` single-space plain exact-tag pagination, and `M8.5.40` separator-noise pagination.
- This batch keeps the baseline coherent inside one later quality chain: it extends pagination evidence deeper into the exact-tag / separator-quality refinements without mixing unrelated family-precedence cases.
- Planning commit: `5b1bb1e` (`docs(plans): add offline relevance late quality pagination plan`).
- Feature commit: `597f25d` (`feat(terminal): expand offline relevance late quality pagination fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=60`, `pass_count=60`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-25) - Offline Relevance Mid Chain Pagination Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding the next uncovered mid-chain pagination samples before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant mid-chain pagination service-level tests
- [x] Write the design doc and implementation plan docs for this mid-chain pagination expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with log-marker, punctuation-wrap, exact-tag, and exact-tag-marker pagination cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 52 to 56 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-25-terminal-relevance-offline-baseline-mid-chain-pagination-expansion-design.md` and `docs/plans/2026-03-25-terminal-relevance-offline-baseline-mid-chain-pagination-expansion.md` to lock scope, case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 56-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four service-test-derived scenarios: `M8.5.21` log-marker pagination, `M8.5.22` punctuation-wrap pagination, `M8.5.23` exact-tag pagination, and `M8.5.25` exact-tag-marker pagination.
- This batch keeps the baseline layered and non-duplicative: it extends pagination evidence one stage deeper into the middle of the relevance chain without revisiting already-covered pairwise or fallback semantics.
- Planning commit: `afff472` (`docs(plans): add offline relevance mid-chain pagination plan`).
- Feature commit: `69d39f9` (`feat(terminal): expand offline relevance mid-chain pagination fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=56`, `pass_count=56`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-25) - Offline Relevance Additive Fallback And Early Pagination Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding one remaining non-duplicate additive fallback plus the next early pagination samples before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant additive fallback / pagination service-level tests
- [x] Write the design doc and implementation plan docs for this additive fallback and early pagination expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with no-exact-tag-wrapper fallback, whole-word pagination, line-boundary pagination, and line-start-quality pagination cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 48 to 52 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-25-terminal-relevance-offline-baseline-additive-fallback-and-early-pagination-expansion-design.md` and `docs/plans/2026-03-25-terminal-relevance-offline-baseline-additive-fallback-and-early-pagination-expansion.md` to lock scope, case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 52-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four service-test-derived scenarios: `M8.5.22` no-exact-tag-wrapper fallback, `M8.5.18` whole-word pagination, `M8.5.19` line-boundary pagination, and `M8.5.20` line-start-quality pagination.
- This batch keeps the baseline non-duplicative: `no delimited log marker` fallback remains intentionally excluded because the existing `exact-tag-wrapper-delimiter-quality` case already captures the same ordering evidence.
- Planning commit: `570aff0` (`docs(plans): add offline relevance additive fallback and early pagination plan`).
- Feature commit: `4769d84` (`feat(terminal): expand offline relevance additive fallback and early pagination fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=52`, `pass_count=52`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-25) - Offline Relevance Early Whole Word Positive Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding the remaining early whole-word and line-start-whole-word positive samples before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant early whole-word service-level tests
- [x] Write the design doc and implementation plan docs for this early whole-word positive expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with whole-word priority, whole-word offset tie-break, line-start whole-word priority, and line-start whole-word offset tie-break cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 44 to 48 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-25-terminal-relevance-offline-baseline-early-whole-word-positive-expansion-design.md` and `docs/plans/2026-03-25-terminal-relevance-offline-baseline-early-whole-word-positive-expansion.md` to lock scope, case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 48-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four service-test-derived scenarios: whole-word priority, whole-word offset tie-break, line-start whole-word priority, and line-start whole-word offset tie-break.
- While selecting the batch, `no delimited log marker` fallback was explicitly rejected as the next fixture candidate because its transcript and ordering semantics are already represented by the existing `exact-tag-wrapper-delimiter-quality` case; this keeps the offline evidence set non-duplicative.
- Planning commit: `88c3e59` (`docs(plans): add offline relevance early whole-word positive expansion plan`).
- Feature commit: `c4e55a7` (`feat(terminal): expand offline relevance early whole-word positive fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=48`, `pass_count=48`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-25) - Offline Relevance Early Fallback And Delimiter Quality Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding early fallback and same-family delimiter-quality samples before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant early-stage / delimiter-quality service-level tests
- [x] Write the design doc and implementation plan docs for this early fallback and delimiter-quality expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with no-whole-word fallback, no-line-start-whole-word fallback, exact-tag wrapper delimiter quality, and raw-marker delimiter quality cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md` and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 40 to 44 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-25-terminal-relevance-offline-baseline-early-fallback-and-delimiter-quality-expansion-design.md` and `docs/plans/2026-03-25-terminal-relevance-offline-baseline-early-fallback-and-delimiter-quality-expansion.md` to lock scope, case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 44-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four service-test-derived scenarios: `M8.5.18` no-whole-word fallback, `M8.5.19` no-line-start-whole-word fallback, exact-tag wrapper delimiter quality, and raw-marker delimiter quality.
- Planning commit: `d926bbb` (`docs(plans): add offline relevance early fallback and delimiter quality plan`).
- Feature commit: `d0f2b42` (`feat(terminal): expand offline relevance early fallback and delimiter quality fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=44`, `pass_count=44`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-24) - Restart Context Sync

## Goal
- Sync the restart-oriented handoff docs so the next Codex session can immediately resume from the current 40-case offline terminal relevance baseline.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, `tasks/todo.md`, and recent commits
- [x] Rewrite `docs/progress.md` into a concise restart entry centered on the current `M8.5.51` + 40-case offline baseline state
- [x] Update `AGENTS.md` baseline snapshot, latest hashes, and `/sync` wording to match the 2026-03-24 handoff state
- [x] Run minimal verification for the doc-only diff (`git diff --check`, `git status --short`)
- [x] Commit the handoff sync

## Review
- Rewrote `docs/progress.md` into a short restart-oriented handoff doc focused on the current `M8.5.51` + 40-case offline relevance baseline, the latest planning/feature/handoff commits, the verified command set, and the immediate next baseline-first step.
- Updated `AGENTS.md` so its baseline snapshot, terminal-quality tooling references, active planning/handoff hashes, and `/sync` guidance now point at the 2026-03-24 brace/angle pairwise handoff state instead of the earlier 8-case baseline snapshot.
- This batch is doc-only: no fixture, ranking logic, route/API/UI, or RBAC behavior changed.

# Session Plan (2026-03-24) - Offline Relevance Brace And Angle Pairwise Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding the remaining brace/angle direct pairwise and fallback samples before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant brace/angle service-level tests
- [x] Write the design doc and implementation plan docs for this brace/angle pairwise expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with brace-wrapper direct pairwise, brace-plain direct pairwise, no-brace-plain fallback, and angle-plain offset tie-break cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md` and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 36 to 40 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-24-terminal-relevance-offline-baseline-brace-and-angle-pairwise-expansion-design.md` and `docs/plans/2026-03-24-terminal-relevance-offline-baseline-brace-and-angle-pairwise-expansion.md` to lock scope, brace/angle pairwise case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 40-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four brace/angle-side direct-pair or fallback scenarios: brace-wrapper pairwise, brace-plain pairwise, no-brace-plain fallback, and angle-plain offset tie-break.
- Initial draft duplicated two already-represented semantics; that was corrected before finalizing the batch so the added cases now cover genuinely new baseline evidence.
- Planning commit: `84f6e4c` (`docs(plans): add offline relevance brace and angle pairwise expansion plan`).
- Feature commit: `04553e8` (`feat(terminal): expand offline relevance brace and angle pairwise fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=40`, `pass_count=40`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-24) - Offline Relevance Brace And Angle Fallback Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding the remaining brace/angle fallback and branch-specific samples before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant brace/angle service-level tests
- [x] Write the design doc and implementation plan docs for this brace/angle fallback expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with brace plain offset tie-break, angle plain pagination, no-brace-wrapper fallback, and no-angle-plain fallback cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md` and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 32 to 36 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-24-terminal-relevance-offline-baseline-brace-and-angle-fallback-expansion-design.md` and `docs/plans/2026-03-24-terminal-relevance-offline-baseline-brace-and-angle-fallback-expansion.md` to lock scope, brace/angle fallback case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 36-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four brace/angle-side fallback or branch-specific scenarios derived from landed service tests: brace plain offset tie-break, angle plain pagination, no-brace-wrapper fallback, and no-angle-plain fallback.
- Planning commit: `38f9385` (`docs(plans): add offline relevance brace and angle fallback expansion plan`).
- Feature commit: `1171501` (`feat(terminal): expand offline relevance brace and angle fallback fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=36`, `pass_count=36`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-24) - Offline Relevance Brace And Angle Branch Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding brace/angle-side marker and plain-wrapper branch samples before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant brace/angle service-level tests
- [x] Write the design doc and implementation plan docs for this brace/angle branch expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with brace-wrapper marker pagination, brace-wrapper marker offset tie-break, brace plain exact-tag pagination, and angle plain exact-tag offset pagination
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md` and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 28 to 32 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-24-terminal-relevance-offline-baseline-brace-and-angle-branch-expansion-design.md` and `docs/plans/2026-03-24-terminal-relevance-offline-baseline-brace-and-angle-branch-expansion.md` to lock scope, brace/angle branch case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 32-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four brace/angle-side scenarios derived from landed service tests: brace-wrapper marker pagination, brace-wrapper marker offset tie-break, brace plain exact-tag pagination, and angle plain exact-tag offset pagination.
- Planning commit: `c7fc16e` (`docs(plans): add offline relevance brace and angle branch expansion plan`).
- Feature commit: `bd16927` (`feat(terminal): expand offline relevance brace and angle branch fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=32`, `pass_count=32`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-24) - Offline Relevance Non-Square Marker Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding non-square marker branch pagination and offset samples before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant `M8.5.29` / `M8.5.30` service-level tests
- [x] Write the design doc and implementation plan docs for this non-square marker expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with non-square colon pagination, non-square colon offset tie-break, non-square dash pagination, and non-square dash offset tie-break cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md` and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 24 to 28 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-24-terminal-relevance-offline-baseline-non-square-marker-expansion-design.md` and `docs/plans/2026-03-24-terminal-relevance-offline-baseline-non-square-marker-expansion.md` to lock scope, non-square marker case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 28-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four `M8.5.29` / `M8.5.30` scenarios derived from landed service tests: non-square colon pagination, non-square colon offset tie-break, non-square dash pagination, and non-square dash offset tie-break.
- Planning commit: `c9c6ef1` (`docs(plans): add offline relevance non-square marker expansion plan`).
- Feature commit: `76cecc3` (`feat(terminal): expand offline relevance non-square marker fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=28`, `pass_count=28`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-24) - Offline Relevance Offset Tie-Break Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding offset-specific marker/plain-wrapper tie-break samples before proposing any new ranking logic.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant service-level offset tests
- [x] Write the design doc and implementation plan docs for this offset tie-break expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with exact-tag colon-marker offset, square-bracket dash-marker offset, paren plain-wrapper offset, and square-bracket plain exact-tag offset cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md` and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 20 to 24 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-24-terminal-relevance-offline-baseline-offset-tie-break-expansion-design.md` and `docs/plans/2026-03-24-terminal-relevance-offline-baseline-offset-tie-break-expansion.md` to lock scope, offset tie-break case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 24-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four offset-specific tie-break scenarios derived from landed service tests: exact-tag colon-marker offset, square-bracket dash-marker offset, paren plain-wrapper offset, and square-bracket plain exact-tag offset.
- Parallel exploration confirmed the next uncovered priorities after this batch likely shift to non-square marker pagination/offset samples and a few remaining plain-wrapper branch-specific pagination cases, but did not block this implementation.
- Planning commit: `ca0be06` (`docs(plans): add offline relevance offset tie-break expansion plan`).
- Feature commit: `150a412` (`feat(terminal): expand offline relevance offset tie-break fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=24`, `pass_count=24`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-24) - Offline Relevance Marker And Plain Wrapper Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding high-value marker-family and plain-wrapper-family pagination samples before proposing any new tie-break.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the relevant service-level marker/plain-wrapper tests
- [x] Write the design doc and implementation plan docs for this marker/plain-wrapper baseline expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with exact-tag colon-marker, square-bracket dash-marker, square-bracket exact-tag, and paren plain-wrapper pagination cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md` and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 16 to 20 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-24-terminal-relevance-offline-baseline-marker-and-plain-wrapper-expansion-design.md` and `docs/plans/2026-03-24-terminal-relevance-offline-baseline-marker-and-plain-wrapper-expansion.md` to lock scope, marker/plain-wrapper case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 20-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four marker/plain-wrapper pagination scenarios derived from landed service tests: exact-tag colon-marker pagination, square-bracket dash-marker pagination, square-bracket exact-tag pagination, and paren plain-wrapper pagination.
- Planning commit: `e64f835` (`docs(plans): add offline relevance marker and plain wrapper expansion plan`).
- Feature commit: `841e3e2` (`feat(terminal): expand offline relevance marker and plain wrapper fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=20`, `pass_count=20`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-24) - Offline Relevance Baseline Whitespace Family Expansion

## Goal
- Continue terminal relevance development from the current offline benchmark by expanding the remaining plain exact-tag whitespace-family branches into offline baseline coverage before proposing any new tie-break.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, the current fixture, and the service-level whitespace-family tests
- [x] Write the design doc and implementation plan docs for this whitespace-family baseline expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with payloadless, tab-prefixed payload, multi-space payload, and space-prefixed mixed-whitespace payload cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md` and `tasks/todo.md` review notes, then commit with detailed planning/feature/handoff messages

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 12 to 16 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-24-terminal-relevance-offline-baseline-whitespace-family-expansion-design.md` and `docs/plans/2026-03-24-terminal-relevance-offline-baseline-whitespace-family-expansion.md` to lock scope, signal-family selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 16-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four whitespace-family scenarios derived from landed service tests: payloadless separator quality, tab-prefixed payload offset pagination, multi-space payload offset pagination, and space-prefixed mixed-whitespace payload offset pagination.
- Planning commit: `6226cea` (`docs(plans): add offline relevance whitespace family expansion plan`).
- Feature commit: `eeb388e` (`feat(terminal): expand offline relevance whitespace family fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=16`, `pass_count=16`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-24) - Offline Relevance Baseline Realistic Edge Expansion

## Goal
- Continue terminal relevance development from the current `M8.5.51` baseline by expanding higher-signal realistic edge coverage in the offline benchmark before considering any new tie-break.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, and the current terminal relevance baseline slices
- [x] Write the design doc and implementation plan docs for this baseline expansion
- [x] Add RED expectations for the expanded fixture size and case set in `tests/scripts/test_evaluate_terminal_relevance.py`
- [x] Expand `tests/fixtures/terminal_relevance_baseline.json` with wrapper-marker family, single-space separator quality, exact-tag punctuation-noise, and `M8.5.49` other-leading whitespace pagination cases
- [x] Run offline baseline, focused regression, full regression, lint/build, and `git diff --check`
- [x] Update `docs/progress.md` and `tasks/todo.md` review notes, then commit with a detailed message

## Review
- Confirmed the next terminal step should remain baseline-first: no new ranking rule was added, and the offline benchmark was expanded from 8 to 12 deterministic cases before any post-`M8.5.51` tie-break discussion.
- Added `docs/plans/2026-03-24-terminal-relevance-offline-baseline-realistic-edge-expansion-design.md` and `docs/plans/2026-03-24-terminal-relevance-offline-baseline-realistic-edge-expansion.md` to lock scope, case selection, and verification before changing the fixture.
- Updated `tests/scripts/test_evaluate_terminal_relevance.py` to 12-case RED expectations, then expanded `tests/fixtures/terminal_relevance_baseline.json` with four new realistic-edge scenarios: non-square wrapper marker family ordering, single-space separator quality ladder, exact-tag punctuation-noise cleanliness, and `M8.5.49` other-leading whitespace pagination.
- Fresh environment verification exposed a real dependency gap: `pip install -e '.[dev]'` did not install `greenlet`, which broke existing async SQLAlchemy test teardown. Added `greenlet>=3.0.0` to `pyproject.toml` and revalidated from the editable install.
- Planning commit: `7c1c4c7` (`docs(plans): add offline relevance realistic edge expansion plan`).
- Feature commit: `ab90bbc` (`feat(terminal): expand offline relevance realistic edge fixtures`).
- Fresh verification passed: `.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q` (RED->GREEN), `.venv/bin/python scripts/evaluate_terminal_relevance.py --format text` (`case_count=12`, `pass_count=12`, `pass_rate/top1_accuracy/mrr = 1.000`), `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`740 passed`), `.venv/bin/ruff check .`, `cd web && npm ci && npm run lint && npm run build`, and `git diff --check`.

# Session Plan (2026-03-22) - Post-M8.5.39 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.39`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Refine the planning docs once the initial count-based approach proved redundant in the existing tuple
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.40` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.40` plain exact-tag separator-noise demotion refinement for terminal history search.
- Initial planning shape was adjusted before implementation: the first count-based separator-noise idea was redundant against existing exact-tag and single-space counters, so the final approved design narrowed to a conditional earliest non-single-space noise offset tie-break.
- Added and then refined `docs/plans/2026-03-22-m8-5-40-terminal-plain-exact-tag-separator-noise-demotion-design.md` and `docs/plans/2026-03-22-m8-5-40-terminal-plain-exact-tag-separator-noise-demotion.md` to lock the final offset-based scope and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for later non-single-space plain exact-tag noise outranking earlier noise when single-space plain exact-tag hits already exist, `M8.5.39` fallback when no single-space plain exact-tag exists, and global pagination under the new `M8.5.40` ordering.
- Extended `services/terminal_sessions.py` with `conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset`, the corresponding sentinel, and a narrow helper that recognizes non-marker plain exact-tag hits not covered by the `M8.5.39` single-space helper; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commits: `94aebc2` (`docs(plans): add M8.5.40 plain separator-noise plan`) and `88b2d9a` (`docs(plans): refine M8.5.40 separator-noise tie-break`).
- Feature commit: `1262bae` (`feat(terminal): add M8.5.40 separator-noise demotion`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`704 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-21) - Post-M8.5.38 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.38`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.39` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.39` plain exact-tag single-space separator preference refinement for terminal history search.
- Design direction approved: keep marker families, square-bracket family preference, `M8.5.34` paren plain precedence, `M8.5.35` exact-tag punctuation-noise demotion, `M8.5.36` brace plain exact-tag precedence, `M8.5.37` angle plain offset tie-break, and `M8.5.38` plain square-bracket offset tie-break intact, then add one more narrow non-marker exact-tag refinement for explicit single-space separator quality preference.
- Added `docs/plans/2026-03-21-m8-5-39-terminal-plain-exact-tag-single-space-separator-preference-design.md` and `docs/plans/2026-03-21-m8-5-39-terminal-plain-exact-tag-single-space-separator-preference.md` to lock scope, single-space separator rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for single-space plain exact-tag preference over tab/looser whitespace separators, `M8.5.38` fallback when no single-space plain exact-tag exists, and global pagination under the new `M8.5.39` ordering.
- Extended `services/terminal_sessions.py` with `line_start_plain_exact_tag_single_space_separator_match_count`, `first_line_start_plain_exact_tag_single_space_separator_offset`, the corresponding sentinel, and a narrow helper that only recognizes non-marker exact-tag lines whose closing wrapper is followed by a single ASCII space and then immediate non-whitespace text; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `0af6a17` (`docs(plans): add M8.5.39 plain exact-tag single-space plan`).
- Feature commit: `3378c02` (`feat(terminal): add M8.5.39 plain exact-tag single-space preference`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`701 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-21) - Post-M8.5.37 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.37`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.38` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.38` square-bracket plain exact-tag offset tie-break refinement for terminal history search.
- Design direction approved: keep marker families, square-bracket family preference, `M8.5.34` paren plain precedence, `M8.5.35` exact-tag punctuation-noise demotion, `M8.5.36` brace plain exact-tag precedence, and `M8.5.37` angle plain offset tie-break intact, then add one more narrow non-marker exact-tag refinement for explicit plain square-bracket earliest-offset tie-break behavior.
- Added `docs/plans/2026-03-21-m8-5-38-terminal-square-bracket-plain-exact-tag-offset-tie-break-design.md` and `docs/plans/2026-03-21-m8-5-38-terminal-square-bracket-plain-exact-tag-offset-tie-break.md` to lock scope, plain square-bracket offset rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for plain square-bracket exact-tag offset tie-break, `M8.5.37` fallback when no plain square-bracket exact-tag exists, and global pagination under the new `M8.5.38` ordering.
- Extended `services/terminal_sessions.py` with `first_line_start_square_bracket_plain_exact_tag_offset` plus the corresponding sentinel and narrow plain square-bracket helper/count; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `b0667a8` (`docs(plans): add M8.5.38 square-bracket plain exact-tag offset plan`).
- Feature commit: `ce7f93c` (`feat(terminal): add M8.5.38 square-bracket plain exact-tag offset tie-break`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`698 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-21) - Post-M8.5.36 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.36`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.37` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.37` angle-wrapper plain exact-tag offset tie-break refinement for terminal history search.
- Design direction approved: keep marker families, square-bracket priority, `M8.5.34` paren plain precedence, `M8.5.35` exact-tag punctuation-noise demotion, and `M8.5.36` brace plain exact-tag precedence intact, then add one more narrow non-marker exact-tag refinement for explicit angle plain exact-tag earliest-offset tie-break behavior.
- Added `docs/plans/2026-03-21-m8-5-37-terminal-angle-wrapper-plain-exact-tag-offset-tie-break-design.md` and `docs/plans/2026-03-21-m8-5-37-terminal-angle-wrapper-plain-exact-tag-offset-tie-break.md` to lock scope, angle plain exact-tag offset rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for angle plain exact-tag offset tie-break, `M8.5.36` fallback when no angle plain exact-tag exists, and global pagination under the new `M8.5.37` ordering.
- Extended `services/terminal_sessions.py` with `first_line_start_angle_wrapper_plain_exact_tag_offset` plus the corresponding sentinel and count helper return shape; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `dc1775f` (`docs(plans): add M8.5.37 angle plain exact-tag offset plan`).
- Feature commit: `4ff848c` (`feat(terminal): add M8.5.37 angle plain exact-tag offset tie-break`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`695 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-21) - Post-M8.5.35 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.35`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.36` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.36` brace-wrapper plain exact-tag precedence refinement for terminal history search.
- Design direction approved: keep marker families, square-bracket priority, `M8.5.34` paren plain precedence, and `M8.5.35` exact-tag punctuation-noise demotion intact, then add one more narrow non-marker exact-tag refinement for explicit brace plain exact-tag count/offset tie-break behavior.
- Added `docs/plans/2026-03-21-m8-5-36-terminal-brace-wrapper-plain-exact-tag-precedence-design.md` and `docs/plans/2026-03-21-m8-5-36-terminal-brace-wrapper-plain-exact-tag-precedence.md` to lock scope, brace plain exact-tag rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for brace plain exact-tag offset tie-break, `M8.5.35` fallback when no brace plain exact-tag exists, and global pagination under the new `M8.5.36` ordering.
- Extended `services/terminal_sessions.py` with `line_start_brace_wrapper_plain_exact_tag_match_count`, `first_line_start_brace_wrapper_plain_exact_tag_offset`, and a narrow helper derived from the existing exact-tag / exact-tag-marker rules; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `2e90c03` (`docs(plans): add M8.5.36 brace plain exact-tag plan`).
- Feature commit: `fb4effd` (`feat(terminal): add M8.5.36 brace plain exact-tag precedence`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`692 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-21) - Post-M8.5.34 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.34`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.35` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.35` exact-tag punctuation-noise demotion refinement for terminal history search.
- Design direction approved: keep marker families, square-bracket priority, and the existing plain exact-tag wrapper ordering intact, then add one more narrow conditional demotion so snapshots with exact-tag hits stop gaining accidental credit from tighter-wrapper punctuation noise.
- Added `docs/plans/2026-03-21-m8-5-35-terminal-exact-tag-punctuation-noise-demotion-design.md` and `docs/plans/2026-03-21-m8-5-35-terminal-exact-tag-punctuation-noise-demotion.md` to lock scope, conditional punctuation-noise rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for clean-exact-tag-over-noisy-exact-tag ordering, fewer-exact-tag-noises ordering, `M8.5.34` fallback when no exact-tag exists, and global pagination under the new `M8.5.35` ordering.
- Extended `services/terminal_sessions.py` with `conditional_non_exact_tag_punctuation_wrap_match_count`, derived from the existing exact-tag and punctuation-wrap counts; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `2829cdf` (`docs(plans): add M8.5.35 exact-tag punctuation-noise plan`).
- Feature commit: `67fcc71` (`feat(terminal): add M8.5.35 exact-tag punctuation-noise demotion`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`689 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-21) - Post-M8.5.33 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.33`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.34` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.34` paren-wrapper plain exact-tag precedence refinement for terminal history search.
- Design direction approved: keep marker families, square-bracket priority, and `M8.5.33` angle demotion intact, then add one more narrow non-marker exact-tag refinement so `(query) text` outranks `{query} text` without widening into a broader wrapper-family model.
- Added `docs/plans/2026-03-21-m8-5-34-terminal-paren-wrapper-plain-exact-tag-precedence-design.md` and `docs/plans/2026-03-21-m8-5-34-terminal-paren-wrapper-plain-exact-tag-precedence.md` to lock scope, paren plain exact-tag rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for paren-plain-exact-tag-over-brace ordering, paren plain exact-tag offset tie-break, `M8.5.33` fallback when no paren plain exact-tag exists, and global pagination under the new `M8.5.34` ordering.
- Extended `services/terminal_sessions.py` with `line_start_paren_wrapper_plain_exact_tag_match_count`, `first_line_start_paren_wrapper_plain_exact_tag_offset`, and a narrow helper derived from the existing exact-tag and exact-tag-marker rules; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `37a2951` (`docs(plans): add M8.5.34 paren plain exact-tag plan`).
- Feature commit: `4e02071` (`feat(terminal): add M8.5.34 paren plain exact-tag precedence`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`685 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-21) - Post-M8.5.32 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.32`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.33` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.33` angle-wrapper plain exact-tag demotion refinement for terminal history search.
- Design direction approved: keep marker families and square-bracket priority intact, then add one more narrow non-marker exact-tag refinement so `<query> text` falls behind `(query) text` and `{query} text` without introducing a new `()` versus `{}` ordering.
- Added `docs/plans/2026-03-21-m8-5-33-terminal-angle-wrapper-exact-tag-demotion-design.md` and `docs/plans/2026-03-21-m8-5-33-terminal-angle-wrapper-exact-tag-demotion.md` to lock scope, angle-wrapper demotion rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for brace-plain-exact-tag-over-angle ordering, paren-plain-exact-tag-over-angle ordering, `M8.5.32` marker-family fallback when no angle plain exact-tag exists, and global pagination under the new `M8.5.33` ordering.
- Extended `services/terminal_sessions.py` with `line_start_angle_wrapper_plain_exact_tag_match_count` and a narrow helper derived from the existing exact-tag and exact-tag-marker rules; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `1688f7e` (`docs(plans): add M8.5.33 angle-wrapper exact-tag plan`).
- Feature commit: `ad8e426` (`feat(terminal): add M8.5.33 angle-wrapper exact-tag demotion`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`681 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-21) - Post-M8.5.31 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.31`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.32` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.32` brace-wrapper marker precedence refinement for terminal history search.
- Design direction approved: keep raw-marker, square-bracket, and paren-wrapper priority intact, then add one more narrow wrapper-pair precedence so `{query}: text` and `{query} - text` outrank `<query>...` marker forms inside the non-square wrapper family.
- Added `docs/plans/2026-03-21-m8-5-32-terminal-brace-wrapper-marker-precedence-design.md` and `docs/plans/2026-03-21-m8-5-32-terminal-brace-wrapper-marker-precedence.md` to lock scope, brace-wrapper rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for brace-wrapper-over-angle ordering, brace-wrapper offset tie-break, `M8.5.31` fallback when no brace-wrapper marker exists, and global pagination under the new `M8.5.32` ordering.
- Extended `services/terminal_sessions.py` with `line_start_brace_wrapper_marker_match_count`, `first_line_start_brace_wrapper_marker_offset`, and a narrow helper derived from the existing exact-tag marker rule; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `ec19e37` (`docs(plans): add M8.5.32 brace-wrapper precedence plan`).
- Feature commit: `7888b84` (`feat(terminal): add M8.5.32 brace-wrapper precedence`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`677 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-21) - Post-M8.5.30 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.30`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.31` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.31` paren-wrapper marker precedence refinement for terminal history search.
- Design direction approved: keep raw-marker and square-bracket priority intact, then add one more narrow wrapper-pair precedence so `(query): text` and `(query) - text` outrank `{query}...` and `<query>...` marker forms inside the non-square wrapper family.
- Added `docs/plans/2026-03-21-m8-5-31-terminal-paren-wrapper-marker-precedence-design.md` and `docs/plans/2026-03-21-m8-5-31-terminal-paren-wrapper-marker-precedence.md` to lock scope, paren-wrapper rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for paren-wrapper-over-brace/angle ordering, paren-wrapper offset tie-break, `M8.5.30` fallback when no paren-wrapper marker exists, and global pagination under the new `M8.5.31` ordering.
- Extended `services/terminal_sessions.py` with `line_start_paren_wrapper_marker_match_count`, `first_line_start_paren_wrapper_marker_offset`, and a narrow helper derived from the existing exact-tag marker rule; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `06730cd` (`docs(plans): add M8.5.31 paren-wrapper precedence plan`).
- Feature commit: `7dc9940` (`feat(terminal): add M8.5.31 paren-wrapper precedence`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`673 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-21) - Post-M8.5.29 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.29`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.30` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.30` non-square-bracket exact-tag dash-marker placement refinement for terminal history search.
- Design direction approved: keep raw-marker, square-bracket, and colon-marker priority intact, then add one more narrow tie-break so `(query) - text` / `{query} - text` / `<query> - text` can win after shared square-bracket dash-marker baselines have already tied stronger signals.
- Added `docs/plans/2026-03-21-m8-5-30-terminal-non-square-bracket-exact-tag-dash-marker-placement-design.md` and `docs/plans/2026-03-21-m8-5-30-terminal-non-square-bracket-exact-tag-dash-marker-placement.md` to lock scope, non-square dash-marker placement rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for shared-square-dash-baseline non-square-dash ordering, non-square dash-marker offset tie-break, `M8.5.29` fallback when no non-square dash-marker exists, and global pagination under the new `M8.5.30` ordering.
- Extended `services/terminal_sessions.py` with `line_start_non_square_bracket_exact_tag_dash_marker_match_count`, `first_line_start_non_square_bracket_exact_tag_dash_marker_offset`, and a narrow helper derived from the existing exact-tag marker and square-bracket exact-tag rules; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `1872a93` (`docs(plans): add M8.5.30 non-square dash-marker placement plan`).
- Feature commit: `e6bf5f2` (`feat(terminal): add M8.5.30 non-square dash-marker placement`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`669 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-20) - Post-M8.5.28 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.28`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.29` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.29` non-square-bracket exact-tag colon-marker priority refinement for terminal history search.
- Design direction approved: keep raw-marker, square-bracket, and colon-marker priority intact, then add one more narrow tie-break so `(query): text` / `{query}: text` / `<query>: text` can win after shared square-bracket colon-marker baselines have already tied stronger signals.
- Added `docs/plans/2026-03-20-m8-5-29-terminal-non-square-bracket-exact-tag-colon-marker-priority-design.md` and `docs/plans/2026-03-20-m8-5-29-terminal-non-square-bracket-exact-tag-colon-marker-priority.md` to lock scope, non-square colon-marker rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for shared-square-colon-baseline non-square-colon ordering, non-square colon-marker offset tie-break, `M8.5.28` fallback when no non-square colon-marker exists, and global pagination under the new `M8.5.29` ordering.
- Extended `services/terminal_sessions.py` with `line_start_non_square_bracket_exact_tag_colon_marker_match_count`, `first_line_start_non_square_bracket_exact_tag_colon_marker_offset`, and a narrow helper derived from the existing exact-tag colon-marker and square-bracket exact-tag rules; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `ed891bb` (`docs(plans): add M8.5.29 non-square colon-marker priority plan`).
- Feature commit: `16685cd` (`feat(terminal): add M8.5.29 non-square colon-marker priority`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`665 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-20) - Post-M8.5.27 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.27`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.28` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.28` square-bracket exact-tag dash-marker priority refinement for terminal history search.
- Design direction approved: keep raw-marker and colon-marker priority intact, then add one more narrow tie-break so `[query] - text` beats generic exact-tag noise and earlier non-square-bracket marker placement when stronger signals are already tied.
- Added `docs/plans/2026-03-20-m8-5-28-terminal-square-bracket-exact-tag-dash-marker-priority-design.md` and `docs/plans/2026-03-20-m8-5-28-terminal-square-bracket-exact-tag-dash-marker-priority.md` to lock scope, dash-marker rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for square-bracket-dash-marker-over-generic-exact-tag-noise ordering, square-bracket dash-marker offset tie-break, `M8.5.27` fallback when no square-bracket dash-marker exists, and global pagination under the new `M8.5.28` ordering.
- Extended `services/terminal_sessions.py` with `line_start_square_bracket_exact_tag_dash_marker_match_count`, `first_line_start_square_bracket_exact_tag_dash_marker_offset`, and a narrow dash-marker helper derived from the existing exact-tag marker + square-bracket exact-tag rules; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `1c75bac` (`docs(plans): add M8.5.28 square-bracket dash-marker priority plan`).
- Feature commit: `85d8891` (`feat(terminal): add M8.5.28 square-bracket dash-marker priority`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`661 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-20) - Post-M8.5.26 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.26`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.27` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.27` exact-tag colon-marker relevance refinement for terminal history search.
- Design direction approved: keep raw-marker and stronger wrapper signals intact, then prefer exact-tag colon-marker forms such as `[query]: text` over exact-tag dash-marker forms such as `[query] - text`.
- Added `docs/plans/2026-03-20-m8-5-27-terminal-exact-tag-colon-marker-relevance-design.md` and `docs/plans/2026-03-20-m8-5-27-terminal-exact-tag-colon-marker-relevance.md` to lock scope, colon-marker rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for colon-marker-over-dash-marker ordering, colon-marker offset tie-break, `M8.5.26` fallback when no exact-tag colon-marker exists, and global pagination under the new `M8.5.27` ordering.
- Extended `services/terminal_sessions.py` with `line_start_exact_tag_colon_marker_match_count`, `first_line_start_exact_tag_colon_marker_offset`, and a narrow colon-marker helper derived from the existing line-start exact-tag marker rule; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `692622c` (`docs(plans): add M8.5.27 exact-tag colon-marker relevance plan`).
- Feature commit: `cbde3f1` (`feat(terminal): add M8.5.27 exact-tag colon-marker relevance`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`657 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-20) - Post-M8.5.25 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.25`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.26` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.26` square-bracket exact-tag priority refinement for terminal history search.
- Design direction approved: keep raw-marker and stronger wrapper signals intact, then prefer square-bracket exact-tag forms such as `[query] text`, `[query]: text`, and `[query] - text` over other wrapper exact-tag forms such as `(query) text`.
- Added `docs/plans/2026-03-20-m8-5-26-terminal-square-bracket-exact-tag-priority-design.md` and `docs/plans/2026-03-20-m8-5-26-terminal-square-bracket-exact-tag-priority.md` to lock scope, square-bracket rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for square-bracket-over-other-wrapper ordering, square-bracket offset tie-break, `M8.5.25` fallback when no square-bracket exact-tag exists, and global pagination under the new `M8.5.26` ordering.
- Extended `services/terminal_sessions.py` with `line_start_square_bracket_exact_tag_match_count`, `first_line_start_square_bracket_exact_tag_offset`, and a narrow square-bracket helper derived from the existing line-start exact-tag rule; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `0a22370` (`docs(plans): add M8.5.26 square-bracket exact-tag priority plan`).
- Feature commit: `17ab845` (`feat(terminal): add M8.5.26 square-bracket exact-tag priority`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`653 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-20) - Post-M8.5.24 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.24`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.25` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.25` exact-tag marker relevance refinement for terminal history search.
- Design direction approved: keep raw-marker priority intact, then prefer wrapper marker forms such as `[query]: text` and `[query] - text` over plain exact-tag wrapper forms such as `[query] text`.
- Added `docs/plans/2026-03-20-m8-5-25-terminal-exact-tag-marker-relevance-design.md` and `docs/plans/2026-03-20-m8-5-25-terminal-exact-tag-marker-relevance.md` to lock scope, exact-tag marker rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for exact-tag-marker-over-plain-exact-tag ordering, exact-tag marker offset tie-break, `M8.5.24` fallback when no exact-tag marker exists, and global pagination under the new `M8.5.25` ordering.
- Extended `services/terminal_sessions.py` with `line_start_exact_tag_marker_match_count`, `first_line_start_exact_tag_marker_offset`, and a narrow exact-tag marker helper derived from the existing line-start exact-tag rule; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `724d34b` (`docs(plans): add M8.5.25 exact-tag marker relevance plan`).
- Feature commit: `8dd1ad2` (`feat(terminal): add M8.5.25 exact-tag marker relevance`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`649 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-20) - Post-M8.5.23 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.23`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.24` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.24` delimited log-marker relevance refinement for terminal history search.
- Design direction approved: keep raw log-marker priority over wrapper families, then prefer delimiter-bounded raw marker forms such as `query: text` and strict `query - text` over glued `query:text` and `query -text` forms.
- Added `docs/plans/2026-03-20-m8-5-24-terminal-delimited-log-marker-relevance-design.md` and `docs/plans/2026-03-20-m8-5-24-terminal-delimited-log-marker-relevance.md` to lock scope, delimiter-boundary rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for delimited-raw-marker-over-glued-marker ordering, delimited raw-marker offset tie-break, `M8.5.23` fallback when no delimited raw marker exists, and global pagination under the new `M8.5.24` ordering.
- Extended `services/terminal_sessions.py` with `line_start_delimited_log_marker_match_count`, `first_line_start_delimited_log_marker_offset`, and a narrow delimited raw-marker helper derived from the existing line-start raw log-marker rule; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `fb141e4` (`docs(plans): add M8.5.24 delimited log-marker relevance plan`).
- Feature commit: `ab24843` (`feat(terminal): add M8.5.24 delimited log-marker relevance`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`645 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-20) - Post-M8.5.22 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.22`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.23` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.23` exact-tag line-start relevance refinement for terminal history search.
- Design direction approved: keep `M8.5.21` raw log-marker priority intact, then prefer delimiter-aware exact-tag wrapper forms such as `[query] text`, `[query]: text`, and `[query] - text` over tighter non-delimited wrapper forms such as `[query]text`.
- Added `docs/plans/2026-03-20-m8-5-23-terminal-exact-tag-line-start-relevance-design.md` and `docs/plans/2026-03-20-m8-5-23-terminal-exact-tag-line-start-relevance.md` to lock scope, delimiter rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for exact-tag-over-tight-wrapper ordering, exact-tag offset tie-break, `M8.5.22` fallback when no exact-tag exists, and global pagination under the new `M8.5.23` ordering.
- Extended `services/terminal_sessions.py` with `line_start_exact_tag_match_count`, `first_line_start_exact_tag_offset`, and a narrow exact-tag helper derived from the existing line-start punctuation-wrapper rule; `newest` / `oldest`, route/UI/snippet/DTO, `latest.json`, `/sessions/current/history`, and RBAC all remain unchanged.
- Planning commit: `940eac2` (`docs(plans): add M8.5.23 exact-tag line-start relevance plan`).
- Feature commit: `cd2e80e` (`feat(terminal): add M8.5.23 exact-tag line-start relevance`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`641 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-06) - Docs Sync

## Goal
- Sync the latest project state into `docs/progress.md` and `AGENTS.md`, then commit the documentation refresh.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, and recent session state
- [x] Update `docs/progress.md` with the latest restart-oriented status
- [x] Update `AGENTS.md` with the latest baseline and operator notes
- [x] Check doc consistency and diff hygiene
- [x] Commit changes with a detailed message

## Review
- `docs/progress.md` now reflects `M2` fully complete, current start point `M3.1.1`, and the latest provider connectivity verification notes.
- `AGENTS.md` now reflects the correct local HappyClaw reference path, the post-`M2` baseline, and the required `OPENAI_DEFAULT_MODEL=gpt-5.1` note for the tested compatible provider.
- Consistency check: `git diff --check` passed.
- Commit completed: `docs(handoff): refresh progress and agent guidance`.

# Session Plan (2026-03-19) - Post-M8.5.21 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.21`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md`, `AGENTS.md`, and `tasks/todo.md` with `M8.5.22` evidence
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.22` punctuation-aware line-start relevance refinement for terminal history search.
- Design direction approved: keep `M8.5.21` log-marker priority intact, then add one more narrow ranking signal for line-start `[query]` / `(query)` / `{query}` / `<query>` wrappers only.
- Added `docs/plans/2026-03-19-m8-5-22-terminal-punctuation-aware-line-start-relevance-design.md` and `docs/plans/2026-03-19-m8-5-22-terminal-punctuation-aware-line-start-relevance.md` to lock scope, wrapper rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for log-marker-over-wrapper ordering, wrapper-over-plain ordering, no-wrapper fallback, and global pagination under the new `M8.5.22` ordering.
- Extended `services/terminal_sessions.py` with `line_start_punctuation_wrap_match_count`, `first_line_start_punctuation_wrap_offset`, and a narrow wrapper helper that only recognizes line-start single-character pairs around the query.
- Planning commit: `ab35391` (`docs(plans): add M8.5.22 punctuation-aware line-start relevance plan`).
- Feature commit: `f543d77` (`feat(terminal): add M8.5.22 punctuation-aware line-start relevance`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm ci`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-19) - Docs Sync After M8.5.21

## Goal
- Refresh `docs/progress.md` and `AGENTS.md` so the restart-oriented handoff matches the latest `M8.5.21` baseline and next-step guidance, then commit the docs sync.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, recent commits, and current branch status
- [x] Tighten `docs/progress.md` restart wording around the current `M8.5.21` baseline
- [x] Tighten `AGENTS.md` restart wording around the current `M8.5.21` baseline
- [x] Check doc consistency and diff hygiene
- [x] Commit the documentation refresh

## Review
- Refined `docs/progress.md` so the restart summary points directly at the `a4154a7` + `bf40eca` `M8.5.21` chain and explicitly records that the next natural entry is a punctuation-aware line-start refinement.
- Refined `AGENTS.md` so the `M8.5.21` baseline now explicitly notes the narrow `query:` / strict `query -` marker scope and reminds future restarts to use branch `git log` when locating the latest handoff-only sync commit.

# Session Plan (2026-03-19) - Post-M8.5.20 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.20`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md` with evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.21` log-marker relevance refinement for terminal history search.
- Design direction approved: keep `M8.5.20` line-start-quality signals and add a narrower log-marker-aware preference only for line-start `q:` and strict `q -` forms.
- Added `docs/plans/2026-03-19-m8-5-21-terminal-log-marker-relevance-design.md` and `docs/plans/2026-03-19-m8-5-21-terminal-log-marker-relevance.md` to lock scope, marker rules, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for marker-over-plain ordering, marker tie-break, no-marker fallback, and global pagination under the new `M8.5.21` ordering.
- Extended `services/terminal_sessions.py` with `line_start_log_marker_match_count`, `first_line_start_log_marker_offset`, and a narrow marker helper that only recognizes line-start `query:` and strict `query -` forms after an existing line-start whole-word hit.
- Planning commit: `a4154a7` (`docs(plans): add M8.5.21 log-marker relevance plan`).
- Feature commit: `bf40eca` (`feat(terminal): add M8.5.21 log-marker relevance`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-19) - Post-M8.5.19 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.19`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md` with evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.20` line-start quality relevance refinement for terminal history search.
- Design direction approved: keep `M8.5.19` line-start signals, then add one more narrow ranking signal that prefers results with less non-line-start whole-word noise when line-start quality is otherwise similar.
- Added `docs/plans/2026-03-19-m8-5-20-terminal-line-start-quality-relevance-design.md` and `docs/plans/2026-03-19-m8-5-20-terminal-line-start-quality-relevance.md` to lock scope, ordering signal, and verification flow before implementation.
- Corrected the initial `M8.5.20` planning before implementation: `whole_word_match_count` had to move behind the new noise signal, otherwise `non_line_start_whole_word_match_count` would be dominated and the milestone would not change behavior.
- Corrected the planning a second time before implementation: the new noise signal must be conditional on `line_start_whole_word_match_count > 0`, otherwise the no-line-start path would stop cleanly falling back to `M8.5.19`.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for cleaner line-start ordering, preserved first-line-start tie-break, and global pagination under the new `M8.5.20` ordering.
- Extended `services/terminal_sessions.py` with `conditional_non_line_start_whole_word_match_count`, active only when line-start whole-word hits exist, while preserving the no-line-start fallback path from `M8.5.19`.
- Planning commits for this milestone: `b06b00b` (`docs(plans): add M8.5.20 line-start quality relevance plan`), `ac31ffe` (`docs(plans): refine M8.5.20 line-start quality ordering`), and `a167ffa` (`docs(plans): clarify M8.5.20 conditional noise fallback`).
- Feature commit: `ef60f28` (`feat(terminal): add M8.5.20 line-start quality relevance`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-19) - Post-M8.5.18 Continuation

## Goal
- Confirm the next formal milestone after `M8.5.18`, lock the design/plan, then implement and verify the approved refinement.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, recent commits, and current terminal search slices
- [x] Confirm the next milestone scope with the user
- [x] Propose and approve the design
- [x] Write the design doc and implementation plan docs
- [x] Implement the approved refinement with focused TDD
- [x] Run focused and regression verification
- [x] Update `docs/progress.md` with evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Confirmed the next backend-only milestone as `M8.5.19` line-boundary relevance refinement for terminal history search.
- Added `docs/plans/2026-03-19-m8-5-19-terminal-line-boundary-relevance-design.md` and `docs/plans/2026-03-19-m8-5-19-terminal-line-boundary-relevance.md` to lock scope, ranking signals, and verification flow before implementation.
- Added focused TDD coverage in `tests/services/test_terminal_sessions.py` for line-start whole-word ordering, line-start tie-break, no-line-start fallback, and global pagination.
- Extended `services/terminal_sessions.py` with `line_start_whole_word_match_count`, `first_line_start_whole_word_offset`, and a local line-start whole-word helper, while keeping `newest` / `oldest`, route/UI, snippets, `latest.json`, `/sessions/current/history`, and RBAC unchanged.
- Planning commit: `3b85d36` (`docs(plans): add M8.5.19 line-boundary relevance plan`).
- Feature commit: `5cbe11d` (`feat(terminal): add M8.5.19 line-boundary relevance`).
- Fresh verification passed: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`, `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.

# Session Plan (2026-03-09) - M5.2.1 Telegram Client

## Goal
- Complete `M5.2.1` by replacing the Telegram placeholder with a minimal async Bot API client skeleton.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and Telegram/Feishu IM slices
- [x] Write `M5.2.1` design and implementation plan docs
- [x] Add Telegram client tests first and verify they fail
- [x] Implement the minimal Telegram client skeleton for `getUpdates`
- [x] Run focused IM tests, full backend regression, and lint
- [x] Update `docs/progress.md` with `M5.2.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m5-2-1-telegram-client-design.md` and `docs/plans/2026-03-09-m5-2-1-telegram-client.md` to pin the milestone scope before implementation.
- Replaced the Telegram placeholder with an async `TelegramClient` that supports injected HTTP transport and minimal `get_updates()` polling.
- Added `tests/infra/im/test_telegram.py` covering success, request params, Telegram error payload mapping, and malformed response handling.
- Verification passed: `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`.
- Refreshed `.venv` with `.venv/bin/pip install -e ".[dev]"` before final regression because the environment was missing declared dependency `croniter`.
- Commit completed in this session: `feat(im): complete M5.2.1 telegram client skeleton`.

# Session Plan (2026-03-09) - M5.2.2 Telegram Message Handling

## Goal
- Complete `M5.2.2` by normalizing Telegram `message` updates into a minimal event object without expanding into routing, sending, or Markdown rendering.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `infra/im/telegram.py`, `tests/infra/im/test_telegram.py`, and `infra/im/feishu.py`
- [x] Write `M5.2.2` design and implementation plan docs
- [x] Add Telegram message-handling tests first and verify they fail
- [x] Implement the minimal `TelegramMessageEvent` and `handle_update()`
- [x] Run focused IM tests, full backend regression, and lint
- [x] Update `docs/progress.md` with `M5.2.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m5-2-2-telegram-message-handling-design.md` and `docs/plans/2026-03-09-m5-2-2-telegram-message-handling.md` before implementation to lock the milestone boundary.
- Extended `infra/im/telegram.py` with `TelegramMessageEvent` and a pure `handle_update()` parser that only normalizes top-level `message` updates.
- Expanded `tests/infra/im/test_telegram.py` to cover text normalization, unsupported update families returning `None`, non-text messages preserving IDs with `text=None`, and malformed message payload errors.
- Addressed review findings by rejecting boolean identifiers, wrapping transport / malformed payload failures in `TelegramClientError`, and making unsupported `send_message()` calls fail explicitly instead of silently returning `None`.
- Verification passed: `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`.
- Commit completed in this session: `feat(im): complete M5.2.2 telegram message handling`.

# Session Plan (2026-03-09) - M5.2.3 Telegram Markdown Conversion

## Goal
- Complete `M5.2.3` by adding a minimal Markdown-to-Telegram-HTML conversion helper for outbound text formatting.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `infra/im/telegram.py`, `tests/infra/im/test_telegram.py`, and the latest Telegram design notes
- [x] Write `M5.2.3` design and implementation plan docs
- [x] Add Telegram markdown conversion tests first and verify they fail
- [x] Implement the minimal `markdown_to_html()` helper
- [x] Run focused IM tests, full backend regression, and lint
- [x] Update `docs/progress.md` with `M5.2.3` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m5-2-3-telegram-markdown-conversion-design.md` and `docs/plans/2026-03-09-m5-2-3-telegram-markdown-conversion.md` to fix the Markdown conversion boundary before implementation.
- Extended `infra/im/telegram.py` with a pure `markdown_to_html()` helper that escapes raw HTML, protects code blocks / inline code / unsupported links with placeholders, and only converts the approved Telegram-safe subset.
- Expanded `tests/infra/im/test_telegram.py` to cover HTML escaping, inline formatting, fenced code blocks, incomplete markers, unsupported links, nested emphasis staying plain text, and code-span protection.
- Addressed review findings by making placeholder tokens collision-resistant and by blocking nested / cross-overlapping emphasis from generating invalid Telegram HTML.
- Verification passed: `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`.
- Commit completed in this session: `feat(im): complete M5.2.3 telegram markdown conversion`.

# Session Plan (2026-03-09) - M5.3.1 Unified Message

## Goal
- Complete `M5.3.1` by defining a minimal routeable `UnifiedMessage` DTO and adding Feishu/Telegram conversion helpers without rewiring message routing yet.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `domain/schemas.py`, `infra/im/feishu.py`, `infra/im/telegram.py`, and current message service slices
- [x] Write `M5.3.1` design and implementation plan docs
- [x] Add schema and channel-conversion tests first and verify they fail
- [x] Implement `UnifiedMessage` plus Feishu/Telegram `to_unified_message()` helpers
- [x] Run focused tests, full backend regression, and lint
- [x] Update `docs/progress.md` with `M5.3.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m5-3-1-unified-message-design.md` and `docs/plans/2026-03-09-m5-3-1-unified-message.md` to pin the DTO boundary before implementation.
- Added `UnifiedMessage` to `domain/schemas.py` with the minimal routeable fields `channel/chat_jid/sender_id/group_folder/content/message_id/timestamp`.
- Extended `FeishuMessageEvent` and `TelegramMessageEvent` with `timestamp` plus `to_unified_message()` so the current channel contracts remain intact and only gain a thin adapter layer.
- Added `tests/domain/test_schemas.py` and expanded Feishu/Telegram tests to cover text/non-text conversion and timestamp extraction.
- Verification passed: `.venv/bin/pytest -o addopts='' tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`.
- Commit completed in this session: `feat(messages): complete M5.3.1 unified message schema`.

# Session Plan (2026-03-09) - M5.3.2 Message Routing

## Goal
- Complete `M5.3.2` by adding a minimal routing layer that dispatches `UnifiedMessage` instances to injected Feishu, Telegram, or Web handlers.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `domain/schemas.py`, and current IM/message service slices
- [x] Write `M5.3.2` design and implementation plan docs
- [x] Add message-router tests first and verify they fail
- [x] Implement `MessageRouter` plus `MessageRouterError`
- [x] Run focused tests, full backend regression, and lint
- [x] Update `docs/progress.md` with `M5.3.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `services/message_router.py` with minimal injected-channel routing and `MessageRouterError`, without wiring real send paths, API routes, or WebSocket flows.
- Added `tests/services/test_message_router.py` covering Feishu/Telegram/Web dispatch, unknown-channel rejection, and downstream handler exception propagation.
- Verification ran: `.venv/bin/pytest -o addopts='' tests/services/test_message_router.py -q`, `.venv/bin/pytest -o addopts='' tests/services/test_message_router.py tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, and `git diff --check`.
- Code commit completed: `c91e7ee` `feat(messages): add minimal message router`.

# Session Plan (2026-03-09) - M5.4 Acceptance

## Goal
- Complete `M5.4` by verifying `M5.1` through `M5.3` against the acceptance checklist and updating the restart handoff to begin `M6.1.1`.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current IM/message slices, and prior acceptance patterns
- [x] Write `M5.4` design and implementation plan docs
- [x] Run focused `M5` acceptance verification
- [x] Run full backend regression, `ruff`, and frontend lint/build
- [x] Update `docs/progress.md` with `M5.4` evidence, conclusion, and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m5-4-acceptance-design.md` and `docs/plans/2026-03-09-m5-4-acceptance.md` to pin the acceptance scope before execution.
- Reused the existing Feishu, Telegram, `UnifiedMessage`, and `MessageRouter` test suite as the `M5` acceptance matrix, without extending the current IM runtime boundary.
- Verification ran: `.venv/bin/pytest -o addopts='' tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py tests/services/test_message_router.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Acceptance commit message for this milestone: `docs(acceptance): complete M5.4 milestone verification`.

# Session Plan (2026-03-09) - M6.1.1 Unit Tests

## Goal
- Complete `M6.1.1` by aligning `tests/unit/` with the TODO layout and filling it with focused pure-logic unit tests.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current test layout, and pure-logic candidate modules
- [x] Write `M6.1.1` design and implementation plan docs
- [x] Add `tests/unit/test_auth.py`, `tests/unit/test_models.py`, and `tests/unit/test_services.py`
- [x] Remove the legacy `tests/unit/test_auth_unit.py` filename
- [x] Fix any focused/full-suite collection issues introduced by the new layout
- [x] Run `tests/unit/ -v`, full backend regression, and `ruff`
- [x] Update `docs/progress.md` with `M6.1.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m6-1-1-unit-tests-design.md` and `docs/plans/2026-03-09-m6-1-1-unit-tests.md` to pin the unit-test scope before implementation.
- Replaced `tests/unit/test_auth_unit.py` with `tests/unit/test_auth.py`, and added new `tests/unit/test_models.py` plus `tests/unit/test_services.py` so `tests/unit/` now matches the TODO layout.
- Added `tests/unit/__init__.py` after full regression exposed a pytest import-name collision between `tests/unit/test_models.py` and `tests/domain/models/test_models.py`.
- Verification ran: `.venv/bin/pytest tests/unit/test_auth.py -v`, `.venv/bin/pytest tests/unit/ -v`, `.venv/bin/pytest -o addopts='' -q`, and `.venv/bin/ruff check .`.
- Commit message for this milestone: `test(unit): complete M6.1.1 unit test suite`.

# Session Plan (2026-03-09) - M6.1.2 Integration Tests

## Goal
- Complete `M6.1.2` by aligning `tests/integration/` with the TODO layout and adding the smallest meaningful API and WebSocket integration tests.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current app wiring, and existing route tests
- [x] Write `M6.1.2` design and implementation plan docs
- [x] Add `tests/integration/test_api.py`
- [x] Add `tests/integration/test_websocket.py`
- [x] Run focused integration verification
- [x] Run spec review and code-quality review on the new integration slice
- [x] Run full backend regression and `ruff`
- [x] Update `docs/progress.md` with `M6.1.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m6-1-2-integration-tests-design.md` and `docs/plans/2026-03-09-m6-1-2-integration-tests.md` to pin the integration-test scope before implementation.
- Added `tests/integration/test_api.py` for `GET /health` plus `register -> login -> /users/me` through the real FastAPI app wiring.
- Added `tests/integration/test_websocket.py` for the real `/ws/{group_folder}` route, covering a deterministic `run.started` event and same-socket cancel -> `run.failed` under fake runtime control.
- Verification ran: `.venv/bin/pytest -o addopts='' tests/integration/test_api.py tests/integration/test_websocket.py -q`, `.venv/bin/pytest -o addopts='' -q`, and `.venv/bin/ruff check .`.
- Review agents reported `spec-compliant` and `no findings`; residual risk remains intentionally narrow API coverage plus fake-runtime-backed WebSocket integration.
- Commit message for this milestone: `test(integration): complete M6.1.2 integration test suite`.

# Session Plan (2026-03-09) - M6.1.3 CI/CD

## Goal
- Complete `M6.1.3` by adding the minimal GitHub Actions workflow needed to run the current backend and frontend verification commands on push and pull_request.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current verification commands, and root/web dependency config
- [x] Write `M6.1.3` design and implementation plan docs
- [x] Add `.github/workflows/test.yml`
- [x] Add `pytest-cov` to `pyproject.toml` dev dependencies
- [x] Run spec review and code-quality review on the CI slice
- [x] Install updated dev dependencies locally
- [x] Run workflow-equivalent backend and frontend commands locally
- [x] Update `docs/progress.md` with `M6.1.3` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-09-m6-1-3-ci-cd-design.md` and `docs/plans/2026-03-09-m6-1-3-ci-cd.md` to pin the CI scope before implementation.
- Added `.github/workflows/test.yml` with two minimal jobs: backend (`pytest tests/ -v --cov`, `ruff check .`) and frontend (`npm ci`, `npm run lint`, `npm run build`).
- Added `pytest-cov>=6.0.0` to `pyproject.toml` so the TODO-specified backend CI command is valid.
- Verification ran: `.venv/bin/python -m pip install -e ".[dev]"`, `.venv/bin/pytest tests/ -v --cov`, `.venv/bin/ruff check .`, `cd web && npm ci`, `cd web && npm run lint`, and `cd web && npm run build`.
- Review agents reported `spec-compliant` and `no findings`; remaining risk is only that the workflow has been validated locally, not executed on a remote GitHub Actions runner in this environment.
- Commit message for this milestone: `build(ci): complete M6.1.3 workflow setup`.

# Session Plan (2026-03-10) - M6.2.1 README

## Goal
- Complete `M6.2.1` by replacing the placeholder root README with a practical project entrypoint for readers, operators, and contributors.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current repository commands, and the existing README
- [x] Write `M6.2.1` design and implementation plan docs
- [x] Rewrite `README.md` using the approved layered structure
- [x] Run spec review and code-quality review on the README slice
- [x] Run backend regression, `ruff`, and frontend lint/build
- [x] Update `docs/progress.md` with `M6.2.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-2-1-readme-design.md` and `docs/plans/2026-03-10-m6-2-1-readme.md` to pin the README scope before implementation.
- Replaced the placeholder `README.md` with a layered project entrypoint covering positioning, current status, features, quick start, development commands, project structure, architecture, current boundaries, document links, and upstream reference.
- Review agents reported `spec-compliant` and `no findings`; wording stays conservative around IM maturity, Docker verification, and GitHub Actions remote execution evidence.
- Verification ran: `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Commit message for this milestone: `docs(readme): complete M6.2.1 project readme`.

# Session Plan (2026-03-10) - M6.2.2 API Docs

## Goal
- Complete `M6.2.2` by making the current FastAPI-generated `/docs` useful for the existing HTTP API surface without creating a separate API portal.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current FastAPI routes, and current schema/test coverage
- [x] Write `M6.2.2` design and implementation plan docs
- [x] Add OpenAPI-focused tests first and verify they fail
- [x] Enrich app/route/schema OpenAPI metadata for the current HTTP API
- [x] Run spec review and code-quality review on the API docs slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.2.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-2-2-api-docs-design.md` and `docs/plans/2026-03-10-m6-2-2-api-docs.md` to pin the API-docs scope before implementation.
- Added `app/openapi.py` plus app/route/schema metadata so `/docs` now exposes a real HTTP API description, stable tag groupings, documented error responses, and clearer DTO field semantics.
- Added `/openapi.json` contract coverage to `tests/app/routes/test_api_routes.py`, covering global description, tag descriptions, route error responses, placeholder message semantics, key schema descriptions, and the concrete group-member delete response model.
- Multi-agent exploration was used for scope discovery; two review-agent follow-ups timed out under interrupt, so the final spec/code-quality pass was completed with manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Commit message for this milestone: `docs(api): complete M6.2.2 api docs`.

# Session Plan (2026-03-10) - M6.2.3 Deployment Docs

## Goal
- Complete `M6.2.3` by adding a deployment guide for the currently verified local process setup, while clearly marking Docker Compose as an unverified draft.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `README.md`, and the current runtime/config entrypoints
- [x] Write `M6.2.3` design and implementation plan docs
- [x] Add a failing test for the invite `expires_at` doc-accuracy fix
- [x] Add a failing test for direct `scripts/init_db.py` execution
- [x] Correct the invite `expires_at` API-doc wording to match current behavior
- [x] Fix `scripts/init_db.py` so the documented direct command works
- [x] Write the deployment guide and update README links/status wording as needed
- [x] Run multi-agent spec/code-quality review on the deployment-doc slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.2.3` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-2-3-deployment-docs-design.md` and `docs/plans/2026-03-10-m6-2-3-deployment-docs.md` to pin the deployment-doc scope before implementation, then re-planned once deployment smoke verification exposed that `scripts/init_db.py` was not directly executable as documented.
- Added `docs/deployment.md` covering prerequisites, runtime environment variables, verified local process deployment steps, smoke verification, data/persistence notes, and an explicitly unverified Docker Compose draft.
- Corrected the invite `expires_at` API-doc wording in `domain/schemas.py` and locked it with an OpenAPI test in `tests/app/routes/test_api_routes.py`.
- Fixed `scripts/init_db.py` so the documented direct command works from the repository root and added a subprocess-level regression test in `tests/scripts/test_init_db.py`.
- Multi-agent scope/spec review returned `spec-compliant`; the code-quality reviewer timed out under interrupt, so the final quality pass was completed with manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/app/routes/test_api_routes.py tests/scripts/test_init_db.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, `.venv/bin/python scripts/init_db.py`, backend `/health` smoke against live `uvicorn`, frontend `/` smoke against `npm run preview`, and `git diff --check`.
- Commit message for this milestone: `docs(deploy): complete M6.2.3 deployment guide`.

# Session Plan (2026-03-10) - M6.3.1 Database Indexes

## Goal
- Complete `M6.3.1` by adding the three TODO-defined database indexes and verifying that fresh SQLite initialization creates them.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current model definitions, and DB init tests
- [x] Write `M6.3.1` design and implementation plan docs
- [x] Add failing tests for model metadata indexes and SQLite-created indexes
- [x] Implement the minimal model-level index declarations
- [x] Run multi-agent spec/code-quality review on the index slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.3.1` evidence and next step
- [ ] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-3-1-db-indexes-design.md` and `docs/plans/2026-03-10-m6-3-1-db-indexes.md` to pin the index scope before implementation.
- Added the three TODO-defined indexes at the model layer: `idx_messages_chat_jid`, `idx_messages_timestamp`, and `idx_tasks_next_run`.
- Extended `tests/domain/models/test_models.py` to assert the new SQLAlchemy metadata indexes and `tests/scripts/test_init_db.py` to verify fresh SQLite initialization creates the named indexes on the expected columns.
- Multi-agent spec review returned `spec-compliant`; a later code-quality review correctly identified that existing SQLite tables were not backfilling the new indexes, so `scripts/init_db.py` was updated and a regression test was added for the existing-table upgrade path.
- Verification ran: `.venv/bin/pytest tests/domain/models/test_models.py tests/scripts/test_init_db.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Commit message for this milestone: `perf(db): complete M6.3.1 indexes`.

# Session Plan (2026-03-10) - M6.3.2 Connection Pool

## Goal
- Complete `M6.3.2` by making the async SQLAlchemy engine use an explicit, valid connection-pool configuration for the current SQLite-first repository setup.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current DB engine/session files, and the latest DB milestone notes
- [x] Write `M6.3.2` design and implementation plan docs
- [x] Add failing tests for the default file-backed SQLite pool contract and in-memory SQLite behavior
- [x] Implement the minimal engine-construction helper and reuse it for override engines
- [x] Run multi-agent spec/code-quality review on the DB pool slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.3.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-3-2-connection-pool-design.md` and `docs/plans/2026-03-10-m6-3-2-connection-pool.md` to pin the milestone boundary before implementation.
- Extended `tests/infra/db/test_database.py` with a red-green cycle for the default file-backed SQLite pool contract plus four in-memory SQLite URL variants; the first green pass exposed a review-found gap around `sqlite+aiosqlite://` and `file:...mode=memory`, which was then locked with a second red-green cycle.
- Added `create_database_engine()` in `infra/db/database.py` so the repository now uses explicit `20/10` queue-pool sizing for file-backed SQLite while keeping in-memory SQLite variants on `StaticPool`; `scripts/init_db.py` now reuses the same helper for override engines.
- Multi-agent review was used for scope discovery and code review. The first review round found the missing in-memory URL variants and checklist/doc alignment gap; after that fix, follow-up quick reviewers timed out, so the final pass used manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/infra/db/test_database.py tests/scripts/test_init_db.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Commit message for this milestone: `perf(db): complete M6.3.2 connection pool`.

# Session Plan (2026-03-10) - M6.3.3 User Memory Cache

## Goal
- Complete `M6.3.3` by adding the smallest justified cache layer: a process-local read cache for user-global `AGENTS.md` memory.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, current memory-service code, and current cache-related repository boundaries
- [x] Brainstorm scope and alternatives for `M6.3.3`
- [x] Write `M6.3.3` design and implementation plan docs
- [x] Add failing tests for user-memory cache miss, hit, and write-through behavior
- [x] Implement the minimal `MemoryService` cache
- [x] Run multi-agent spec/code-quality review on the memory-cache slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.3.3` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-10-m6-3-3-user-memory-cache-design.md` and `docs/plans/2026-03-10-m6-3-3-user-memory-cache.md` to pin the milestone boundary before implementation.
- Extended `tests/services/test_memory_service.py` with a red-green cycle for three cache behaviors: missing-file cache miss, existing-file cache hit, and `update_user_memory()` write-through refresh. These tests first failed for the intended reasons before the implementation was added.
- Updated `services/memory.py` with a private `_user_memory_cache` so `get_user_memory()` now acts as a read-through cache and `update_user_memory()` refreshes the cache after a successful file write; `append_daily_memory()` and `search_memory()` remain unchanged.
- Multi-agent implementation/review was used for Task 1 red tests and Task 2 spec review. Several quality-review agents timed out, so the final quality pass was completed with manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/services/test_memory_service.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Commit message for this milestone: `perf(memory): complete M6.3.3 user memory cache`.

# Session Plan (2026-03-11) - M6.4.1 Security Scan

## Goal
- Complete `M6.4.1` by adding the smallest repository-local security scanning workflow that is executable in the current environment and wired into the existing verification flow.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, and `docs/TODO.md`
- [x] Brainstorm the `M6.4.1` scope and confirm the minimal approach with the user
- [x] Write `M6.4.1` design and implementation plan docs
- [x] Add failing tests for the security-scan entrypoint
- [x] Implement the minimal scan script and current finding cleanup
- [x] Run multi-agent spec/code-quality review on the security-scan slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.4.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-4-1-security-scanning-design.md` and `docs/plans/2026-03-11-m6-4-1-security-scanning.md` to pin the milestone boundary before implementation.
- Added `tests/scripts/test_security_scan.py` and `scripts/security_scan.py` so the repository now has a local Python entrypoint for Ruff `S`-rule scanning of runtime-oriented code directories.
- Updated `.github/workflows/test.yml`, `README.md`, and `AGENTS.md` so backend CI and local operator docs all point at the same `scripts/security_scan.py` command.
- Replaced two `assert`-based schema guards in `domain/schemas.py` with explicit `ValueError` checks, and added a narrow inline suppression for the `EventType.TOKEN_DELTA` false positive in `portex/contracts/events.py`.
- Multi-agent implementation and review were used for the scan-entrypoint and runtime-finding slices. Two broader review agents timed out under interrupt; a follow-up quick review reported no blocking findings, and the final quality pass was completed with manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/scripts/test_security_scan.py tests/domain/test_schemas.py -v`, `.venv/bin/python scripts/security_scan.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/python -m pip install -e ".[dev]"`, `.venv/bin/pytest tests/ -v --cov`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Commit message for this milestone: `build(security): complete M6.4.1 security scan`.

# Session Plan (2026-03-11) - M6.4.2 Dependency Audit

## Goal
- Complete `M6.4.2` by adding the smallest repository-local Python dependency-audit workflow using `pip-audit`, while preserving the `M6.4.1` static security scan chain.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and the latest `M6.4.1` docs
- [x] Brainstorm the `M6.4.2` scope and confirm the repo-local `pip-audit` approach with the user
- [x] Write `M6.4.2` design and implementation plan docs
- [x] Add failing tests for the dependency-audit entrypoint
- [x] Implement the minimal audit script and dev dependency wiring
- [x] Run multi-agent spec/code-quality review on the dependency-audit slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.4.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-4-2-dependency-audit-design.md` and `docs/plans/2026-03-11-m6-4-2-dependency-audit.md` to pin the milestone boundary before implementation.
- Added `tests/scripts/test_dependency_audit.py` and `scripts/dependency_audit.py` so the repository now has a local Python entrypoint for `pip-audit` against the current project dependency set.
- Updated `pyproject.toml` to include `pip-audit>=2.9.0`, refreshed `.venv`, and wired the new command into `.github/workflows/test.yml`, `README.md`, and `AGENTS.md`.
- Fresh `pip-audit` initially reported `ecdsa 0.19.1 / CVE-2024-23342` with no fix version. `pip index versions ecdsa` still showed `0.19.1` as latest, so the final script now carries one explicit ignore constant instead of hiding the exception in CI-only config.
- Multi-agent review returned `spec-compliant` and `no findings`; the only recorded residual risk is the explicit `ecdsa/CVE-2024-23342` ignore, which is now documented for future revisit.
- Verification ran: `.venv/bin/pytest tests/scripts/test_dependency_audit.py -v`, `.venv/bin/python scripts/dependency_audit.py`, `.venv/bin/python scripts/security_scan.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/pytest tests/ -v --cov`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Commit message for this milestone: `build(security): complete M6.4.2 dependency audit`.

# Session Plan (2026-03-11) - M6.4.3 Security Headers

## Goal
- Complete `M6.4.3` by adding the smallest useful HTTP security-header middleware to the current FastAPI app without expanding into CSP or broader browser policy work.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and the latest security milestone docs
- [x] Brainstorm the `M6.4.3` scope and confirm the minimal-header approach with the user
- [x] Write `M6.4.3` design and implementation plan docs
- [x] Add failing tests for the header contract
- [x] Implement the minimal security-header middleware and app wiring
- [x] Run multi-agent spec/code-quality review on the security-header slice
- [x] Run focused verification, full backend regression, `ruff`, and frontend `lint/build`
- [x] Update `docs/progress.md` with `M6.4.3` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-4-3-security-headers-design.md` and `docs/plans/2026-03-11-m6-4-3-security-headers.md` to pin the milestone boundary before implementation.
- Extended `tests/app/routes/test_api_routes.py` and `tests/integration/test_api.py` with a red-green cycle that locked the new security-header contract on `/health` plus CORS preflight responses.
- Added `app/middleware/security.py` with a lightweight ASGI `SecurityHeadersMiddleware`, exported it via `app/middleware/__init__.py`, and registered it in `app/main.py` outside the current CORS layer so preflight responses inherit the same headers.
- Spec review returned `spec-compliant`; the broader code-review subagent timed out under interrupt, so the final quality pass used manual diff review plus fresh verification evidence.
- Verification ran: `.venv/bin/pytest tests/app/routes/test_api_routes.py tests/integration/test_api.py -q`, `.venv/bin/python scripts/security_scan.py`, `.venv/bin/python scripts/dependency_audit.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/pytest tests/ -v --cov`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Commit message for this milestone: `feat(security): complete M6.4.3 security headers`.

# Session Plan (2026-03-11) - M6.5.1 Version Planning

## Goal
- Complete `M6.5.1` by documenting the first release-version strategy without creating tags, changing package/runtime version strings, or building release artifacts.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `README.md`, and current version metadata
- [x] Brainstorm the `M6.5.1` scope and confirm the planning-only approach with the user
- [x] Write `M6.5.1` design and implementation plan docs
- [x] Update repo-facing docs with the chosen version strategy
- [x] Run review plus repository verification
- [x] Update `docs/progress.md` with `M6.5.1` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-5-1-version-planning-design.md` and `docs/plans/2026-03-11-m6-5-1-version-planning.md` to pin the milestone boundary before implementation.
- Kept `pyproject.toml` and runtime version strings unchanged at `0.1.0`, and documented the planning decision that the first formal release tag target is `v1.0.0`.
- Updated `README.md`, `AGENTS.md`, and `docs/progress.md` so restart-oriented docs now distinguish planned release tag `v1.0.0` from current package/runtime version `0.1.0`, and move the next starting point to `M6.5.2`.
- Verification ran: `rg -n "M6\\.5\\.1|M6\\.5\\.2|v1\\.0\\.0|0\\.1\\.0" README.md AGENTS.md docs/progress.md`, `git diff --check`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Commit message for this milestone: `docs(release): complete M6.5.1 version planning`.

# Session Plan (2026-03-11) - M6.5.2 Release Tag

## Goal
- Complete `M6.5.2` by updating milestone handoff docs, creating the annotated release tag `v1.0.0`, and moving the next starting point to `M6.5.3` without starting artifact-building work.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, release-planning docs, and current git/tag state
- [x] Write `M6.5.2` design and implementation plan docs
- [x] Update repo-facing docs and session tracking for post-`M6.5.2` state
- [x] Run repository verification and prepare the `M6.5.2` completion commit
- [x] Create and verify local annotated tag `v1.0.0`
- [x] Push and verify remote tag `v1.0.0`
- [x] Update `docs/progress.md` with `M6.5.2` evidence and next step
- [x] Commit the milestone with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-5-2-release-tag-design.md` and `docs/plans/2026-03-11-m6-5-2-release-tag.md` to pin the milestone boundary before executing the tag.
- Updated `README.md` and `AGENTS.md` so repo-facing restart guidance now advances from `M6.5.2` to `M6.5.3` while keeping the intentional `v1.0.0` tag versus `0.1.0` runtime/package split visible.
- Verification ran: `git diff --check`, `git rev-parse --verify refs/tags/v1.0.0` (before creation), `git ls-remote --tags origin v1.0.0 v1.0.0^{}` (before and after push), `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git show --stat --oneline v1.0.0`.
- Local annotated tag `v1.0.0` currently points to `dba45f3` (`docs(release): complete M6.5.2 release tag`), and `origin` now exposes `refs/tags/v1.0.0` plus `refs/tags/v1.0.0^{}` for the same commit.
- Note: the release tag was pushed first so `v1.0.0` stays anchored on `dba45f3`; any later `main` commits in this slice are handoff-only follow-ups.

# Session Plan (2026-03-11) - M6.5.3 Release Artifacts

## Goal
- Advance `M6.5.3` by adding a repository-root release-image build path, preserving the frontend `web/dist/` artifact flow, and recording any remaining Docker-runtime blocker explicitly.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, release docs, and current git/runtime environment
- [x] Brainstorm the `M6.5.3` scope and choose the minimal root-image approach under the current no-Docker environment
- [x] Write `M6.5.3` design and implementation plan docs
- [x] Add failing tests for the root Docker build path and build wrapper
- [x] Implement the root Docker artifact path (`Dockerfile`, `.dockerignore`, `scripts/build_docker.py`, `Makefile`)
- [x] Update release/deployment docs for the new artifact boundary
- [x] Run static verification, full regression, and frontend artifact checks
- [x] Attempt real Docker verification and record blocker or success
- [x] Update `docs/progress.md` with `M6.5.3` evidence and next step
- [x] Commit the phase result with a detailed message

## Review
- Added `docs/plans/2026-03-11-m6-5-3-release-artifacts-design.md` and `docs/plans/2026-03-11-m6-5-3-release-artifacts.md` to pin the milestone boundary before implementation.
- Added `tests/scripts/test_build_docker.py` and extended `tests/container/agent_runner/test_container_files.py` so the root release-image path, `.dockerignore`, and wrapper CLI contract are all statically locked.
- Added a root `Dockerfile` and `.dockerignore`, replaced the placeholder `scripts/build_docker.py` with a real wrapper, and updated `Makefile` to expose both `build-release-image` and runner-specific image builds.
- Updated `README.md`, `AGENTS.md`, and `docs/deployment.md` so operator docs now point at the new release-image build entrypoint and explicitly state that real Docker verification still depends on local Docker availability.
- Verification ran: `git diff --check`, `.venv/bin/pytest tests/scripts/test_build_docker.py tests/container/agent_runner/test_container_files.py -q`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, `test -f web/dist/index.html`, `docker version --format '{{.Client.Version}}|{{.Server.Version}}'`, `docker build -t portex:v1.0.0 .`, and `docker image inspect portex:v1.0.0 --format '{{.Id}}'`.
- Review gates: spec review returned `no blocking spec findings`; the quality-review subagent timed out, so the final quality pass used manual diff review plus focused/full verification evidence, with no blocking issues found.
- Current blocker: the repository-root image build path is implemented, but this environment still lacks the `docker` command, so `docker build -t portex:v1.0.0 .` and image inspection remain unverified and `M6.5.3` cannot yet be honestly marked complete.

# Session Plan (2026-03-11) - README Refresh

## Goal
- Refresh the public README so it explains the Portex name and product positioning, replaces internal milestone references with a public support/todo view, adds architecture/workflow diagrams, and ships a Chinese counterpart README.

## Checklist
- [x] Re-read `README.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and the runtime/message slices that determine the current public architecture story
- [x] Brainstorm the README refresh direction and get approval on the layered bilingual approach
- [x] Write the README refresh design doc
- [x] Write the README refresh implementation plan doc
- [x] Rewrite `README.md` with the naming story, public capability matrix, public todo list, and Mermaid diagrams
- [x] Add `README.zh-CN.md` as a near-parity Chinese counterpart with language switch links
- [x] Run review plus repository verification for the documentation slice
- [x] Update `docs/progress.md` and this session review
- [x] Commit the documentation refresh with a detailed message

## Review
- Added `docs/plans/2026-03-11-readme-refresh-design.md` and `docs/plans/2026-03-11-readme-refresh.md` to lock the public README refresh scope before editing.
- Rewrote `README.md` around `Portex = Portal + Codex`, public-facing support and todo lists, and three Mermaid diagrams that reflect the current web runtime and IM normalization boundary.
- Added `README.zh-CN.md` as a near-parity Chinese counterpart with language switch links and the same overall information architecture.
- Review outcome: one doc-quality reviewer found no blocking issues; one technical reviewer caught two Mermaid overstatements, and both were corrected before final verification.
- Fresh repository verification exposed a pre-existing duplicate test definition in `tests/scripts/test_build_docker.py`; removed the stale duplicate so both `pytest` and `ruff` returned to green.
- Verification ran: `rg -n "M[0-9]" README.md README.zh-CN.md`, `git diff --check`, `.venv/bin/pytest tests/scripts/test_build_docker.py -q`, `.venv/bin/ruff check tests/scripts/test_build_docker.py`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check .`, `cd web && npm run lint`, and `cd web && npm run build`.
- Commit message: `docs(readme): refresh public project entrypoint`

# Session Plan (2026-03-11) - README Project Icon

## Goal
- Add a technical-styled cartoon crab icon for Portex and surface it at the top of the English and Chinese README files.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, current README files, and recent repo state
- [x] Brainstorm the icon direction with the user and get approval on the `Portal Crab` concept
- [x] Write the project-icon design and implementation plan docs
- [x] Add a focused failing test for the shared README/logo contract
- [x] Create the shared SVG logo asset
- [x] Integrate the icon into `README.md` and `README.zh-CN.md`
- [x] Run focused verification and diff hygiene checks
- [x] Update `docs/progress.md` with the README logo follow-up
- [x] Commit the documentation/logo update with a detailed message

## Review
- Added `docs/plans/2026-03-11-portex-project-icon-design.md` and `docs/plans/2026-03-11-portex-project-icon.md` to pin the README icon scope before implementation.
- Added the shared logo asset `assets/portex-crab-logo.svg` in the approved `Portal Crab` direction and surfaced it near the top of both README entrypoints.
- Updated the README repository maps so the new root `assets/` directory is explicitly documented in both languages.
- Extended `tests/container/agent_runner/test_container_files.py` with README/logo static contract checks after an initial test-first spike showed this repo-root file-contract suite was the better long-term home than `tests/scripts/`.
- Verification ran: `rg -n "assets/portex-crab-logo\\.svg|Portex project logo" README.md README.zh-CN.md`, `.venv/bin/pytest tests/container/agent_runner/test_container_files.py -v`, `.venv/bin/pytest -o addopts='' -q`, `.venv/bin/ruff check tests/container/agent_runner/test_container_files.py`, `.venv/bin/ruff check .`, and `git diff --check`.
- Review note: two independent code-review explorer subagents timed out on the working tree; the final quality gate used manual diff review plus the fresh focused/full verification evidence above, with no blocking issues found.
- Commit message: `docs(readme): add Portex project icon`

# Session Plan (2026-03-11) - Portex vs HappyClaw Gap Audit

## Goal
- Compare the current Portex implementation against `/home/zcxggmu/workspace/hello-projs/agents/happyclaw` and turn the remaining product gap into a restart-friendly backlog.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `README.md`, and key Portex runtime / route / frontend files
- [x] Re-read the HappyClaw README plus representative backend/frontend files for routes, chat UX, config, IM, tasks, memory, skills, MCP, and monitoring
- [x] Identify what Portex already matches versus what is still intentionally minimal
- [x] Group the remaining differences into priority buckets that can guide the next implementation phases
- [x] Record the comparison result in `tasks/todo.md`

## Review
- Portex already aligns on the broad foundation: Python backend + React frontend, Web chat, WebSocket run/stream/cancel flow, auth/invites/RBAC, task CRUD + logs, file-backed memory primitives, Feishu/Telegram client foundations, unified message DTO + minimal router, CI/tests/security scan/dependency audit, and the root release-image build entrypoint.
- Portex is still materially behind HappyClaw on the primary product chain: end-to-end IM delivery is not wired, `/messages` is still a queued placeholder, the current Web happy path still runs directly through `OpenAIAgentsRuntime`, and the queue / host-mode / container-mode execution plane is not yet integrated into a full per-user workspace runtime.
- HappyClaw also has a much broader admin/product surface that Portex does not yet expose: file-management APIs and UI, Web terminal, monitoring/status APIs, usage stats, richer settings/config flows, memory management APIs/UI, skill management, MCP server management, IM binding flows, and setup wizard pages.
- HappyClaw currently supports an additional QQ channel plus a larger set of IM/runtime behaviors (pairing, slash commands, long-message handling, richer attachments, reaction/card-style responses). Portex currently only has Feishu + Telegram foundations, and even Telegram outbound send is still intentionally unimplemented.
- Frontend completeness is one of the largest visible gaps: Portex currently has `chat/login/register/settings`, while HappyClaw has setup pages, monitor/usage/memory/skills/MCP/users pages, a much richer chat view with files/skills/members/terminal panels, and explicit mobile/PWA optimizations.
- Portex is stronger than HappyClaw in engineering hygiene: explicit milestone docs, restart-oriented handoff discipline, OpenAPI contract coverage, a large Python test suite, repo-local security scan/dependency audit, and verified CI-equivalent commands. The gap is mostly product/runtime breadth, not basic project rigor.

### Recommended Order

- First finish `M6.5.3` on a machine with Docker so the current milestone is honestly closed.
- Then prioritize the product gaps in this order: end-to-end IM chain, real execution plane, workspace/group model, operator surfaces, richer frontend.

### Proposed Milestones

#### `M7` HappyClaw Parity Alignment

**Goal**
- Turn the current Portex scaffold into a product that closes the major runtime and operator-surface gaps versus HappyClaw, while preserving Portex’s Python + OpenAI Agents SDK architecture.

**Milestone Map**
- `M7.1` Main runtime chain parity
- `M7.2` Execution plane parity
- `M7.3` Workspace and group model parity
- `M7.4` Operator surface parity
- `M7.5` Chat and frontend parity
- `M7.6` Channel and ecosystem parity decisions

#### `M7.1` Main Runtime Chain Parity

- [x] `M7.1.1` Replace the current `/messages` queued placeholder with a real dispatch entry that can route a normalized inbound message into the active execution path.
- [x] `M7.1.2` Define the source-of-truth mapping from inbound channel message -> `group_folder` / `chat_jid` / execution target instead of stopping at the current `UnifiedMessage` DTO boundary.
- [x] `M7.1.3` Wire Feishu inbound message events into the real trigger path, not only the current normalization/test layer.
- [x] `M7.1.4` Wire Telegram inbound message events into the real trigger path, not only the current normalization/test layer.
- [x] `M7.1.5` Implement outbound Telegram reply delivery so the inbound -> agent -> outbound loop can actually close.
- [x] `M7.1.6` Replace the current “minimal message router only” boundary with a real per-channel response fan-out path.
- [x] `M7.1.7` Persist enough request/run metadata to correlate one inbound IM message with one agent run and one outbound response.
- [x] `M7.1.8` Add integration coverage for the end-to-end IM delivery chain instead of stopping at DTO/router contracts.

#### `M7.2` Execution Plane Parity

- [x] `M7.2.1` Replace `services/group_queue.py` placeholder logic with a real per-group queue and lifecycle coordinator.
- [x] `M7.2.2` Connect the existing host/container execution slices to the actual runtime trigger flow instead of leaving them as mostly isolated adapters.
- [x] `M7.2.3` Define the runtime selection contract so Web chat, IM chat, scheduled tasks, and future sub-session flows all resolve through one execution-plane rule set.
- [x] `M7.2.4` Introduce session/workspace lifecycle state so one running workspace can accept follow-up messages instead of always behaving like a fresh stateless trigger.
- [x] `M7.2.5` Implement safe cancellation and timeout handling across the real queue + executor boundary, not only the direct `OpenAIAgentsRuntime` path.
- [x] `M7.2.6` Add execution status and recovery signals so queued/running/failed states are observable outside the current direct WebSocket stream.
- [x] `M7.2.7` Add focused tests for queue ordering, executor selection, follow-up injection, cancellation, timeout, and recovery behavior.

#### `M7.3` Workspace And Group Model Parity

- [x] `M7.3.1` Replace the current demo `group-demo` group list with a real persisted group/workspace listing model.
- [x] `M7.3.2` Define the Portex equivalent of HappyClaw’s main workspace / bound chat / per-user home workspace model.
- [x] `M7.3.3` Add explicit workspace ownership and binding metadata so IM chats can be attached to a user’s main workspace or future sub-workspaces.
- [x] `M7.3.4` Extend the current group/member model so it can represent real working sessions instead of only the minimal membership CRUD boundary.
- [x] `M7.3.5` Decide whether Portex will support sub-agent / multi-session tabs like HappyClaw, and if yes, add the minimal data model needed for that.
- [ ] `M7.3.6` Add API routes for listing, creating, updating, and binding workspaces/groups that reflect the chosen model.

#### `M7.4` Operator Surface Parity

- [ ] `M7.4.1` Add a real monitor/status API and page for queue state, executor state, and runtime health instead of only `/health`.
- [ ] `M7.4.2` Add file-management APIs for workspace browsing, upload, download, preview, edit, and delete with the same path-safety rigor as the current execution security model.
- [ ] `M7.4.3` Add memory-management APIs/UI on top of the current file-backed memory service instead of leaving memory as a backend/runner-only primitive.
- [ ] `M7.4.4` Add skills-management APIs/UI instead of relying only on runner-side default tool registration.
- [ ] `M7.4.5` Add MCP server management APIs/UI if Portex intends to match HappyClaw’s user-managed MCP surface.
- [ ] `M7.4.6` Expand settings/configuration flows beyond the current account summary page: provider config, channel config, registration policy, appearance, and system settings.
- [ ] `M7.4.7` Add usage/audit/operator pages where Portex wants parity, or explicitly mark them as intentionally out of scope.

#### `M7.5` Chat And Frontend Parity

- [ ] `M7.5.1` Expand the current `ChatPanel` from a narrow message/thinking/tool view into a richer workspace shell with room for files, members, skills, and execution controls.
- [ ] `M7.5.2` Add file upload and attachment UX to Web chat, not just text-only message submission.
- [ ] `M7.5.3` Add richer room/workspace switching UX instead of the current fixed `group-demo` WebSocket target.
- [ ] `M7.5.4` Add IM binding UX if Portex will bind external chats to internal workspaces like HappyClaw.
- [ ] `M7.5.5` Decide whether to add a terminal panel; if yes, define the execution-mode and permission boundaries first.
- [ ] `M7.5.6` Add setup/onboarding pages if Portex wants parity with HappyClaw’s multi-step first-run experience.
- [ ] `M7.5.7` Add mobile/PWA work only after the core operator/runtime surfaces stop being placeholders.

#### `M7.6` Channel And Ecosystem Parity Decisions

- [ ] `M7.6.1` Decide explicitly whether QQ is part of Portex parity scope or intentionally excluded.
- [ ] `M7.6.2` If QQ is in scope, define the minimal parity target first: C2C, group @Bot, pairing/binding, outbound reply, and image handling.
- [ ] `M7.6.3` Decide how much of HappyClaw’s slash-command behavior should exist in Portex versus staying out of scope.
- [ ] `M7.6.4` Decide whether Portex needs richer IM artifacts like Feishu cards, reactions, and long-message chunking parity.
- [ ] `M7.6.5` Decide which HappyClaw-specific surfaces should remain intentionally unmatched because Portex uses a different runtime stack or product direction.

### Sequencing Notes

- `M7.1` and `M7.2` are the actual parity-critical gaps. Without them, Portex still has strong scaffolding but not the same product-grade execution system.
- `M7.3` is the bridge between “minimal demo routes” and a real multi-user workspace product.
- `M7.4` and `M7.5` are the largest visible product-surface differences when comparing the two repositories side by side.
- `M7.6` should not be started until the project explicitly decides which HappyClaw features are true parity targets versus reference-only inspiration.

# Session Plan (2026-03-11) - M7.1 Main Runtime Chain Planning

## Goal
- Define the first real post-`M6` parity milestone by turning `M7.1` into concrete design and implementation docs without accidentally swallowing `M7.2` queue work or `M7.3` workspace-model work.

## Checklist
- [x] Re-read the current message/runtime boundaries in `app/routes/messages.py`, `app/routes/websocket.py`, `services/agent_trigger.py`, `services/message_router.py`, `domain/schemas.py`, and the earlier `M5.3.2` routing docs
- [x] Confirm the `M7.1` scope choice: close the IM runtime chain on top of the current runtime stack, but defer queue/workspace redesign
- [x] Write the `M7.1` design doc
- [x] Write the `M7.1` implementation plan doc

## Review
- Added `docs/plans/2026-03-11-m7-1-main-runtime-chain-parity-design.md` to lock `M7.1` as “close the current inbound -> runtime -> outbound chain on top of today’s runtime,” explicitly excluding full queue/workspace parity.
- Added `docs/plans/2026-03-11-m7-1-main-runtime-chain-parity.md` with task-by-task execution guidance for a future implementation session.
- The chosen design keeps `M7.1` narrow on purpose: add a real dispatch service, add minimal channel ingestion adapters, add Telegram outbound delivery, replace the `/messages` placeholder, and add focused/integration coverage.
- Explicitly deferred from `M7.1`: real per-group execution plane lifecycle (`M7.2`), final workspace/group topology (`M7.3`), richer operator surfaces (`M7.4`), and frontend product-surface expansion (`M7.5`).
- Suggested future implementation order inside `M7.1`: dispatch service -> IM ingestion adapters -> real `/messages` dispatch -> integration coverage -> docs/handoff refresh.

# Session Plan (2026-03-12) - M6.5.3 Release Artifact Completion

## Goal
- Close formal `M6.5.3` by stabilizing the Docker-missing blocker path, independently re-verifying the real release-image build on the current host, and refreshing restart docs with the final evidence.

## Checklist
- [x] Re-read the current `M6.5.3` build wrapper, tests, and blocker notes
- [x] Add or tighten the failing test for a stable missing-Docker error message
- [x] Implement the minimal `scripts/build_docker.py` change to normalize the message
- [x] Run focused verification for the build wrapper and static release-artifact slice
- [x] Run the broader backend/frontend regression commands relevant to this milestone
- [x] Independently verify the current host rootless Docker path and fresh release-image build
- [x] Update `docs/TODO.md`, `docs/progress.md`, `AGENTS.md`, `README.md`, `README.zh-CN.md`, and `docs/deployment.md` with the final `M6.5.3` state
- [x] Commit the milestone-completion result cleanly

## Review
- Tightened `tests/scripts/test_build_docker.py` so the missing-Docker path now matches the real `subprocess.run()` failure shape (`FileNotFoundError(2, ..., "docker")`) instead of a synthetic message-only exception, and normalized `scripts/build_docker.py` stderr to the stable operator-facing string `docker command not found` while preserving the existing `127` exit code.
- Independent verification overturned the old blocker assumption: the current host already has a working user-space rootless Docker path under `~/bin`, with `DOCKER_HOST=unix:///run/user/1000/docker.sock`; fresh `docker version`, `.venv/bin/python scripts/build_docker.py --tag portex:v1.0.0`, `docker image ls --no-trunc`, and `docker image inspect` all succeeded.
- Refreshed `docs/TODO.md`, `docs/progress.md`, `AGENTS.md`, `README.md`, `README.zh-CN.md`, and `docs/deployment.md` so the repository now consistently records `M6.5.3` and `M6` as complete, while keeping `M7.1` as a user-gated next step rather than an automatic continuation.
- Final verification ran fresh after the doc sync: `git diff --check`; `.venv/bin/pytest tests/scripts/test_build_docker.py tests/container/agent_runner/test_container_files.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`; `test -f web/dist/index.html`; `PATH="$HOME/bin:$PATH" DOCKER_HOST=unix:///run/user/1000/docker.sock docker version --format '{{.Client.Version}}|{{.Server.Version}}'`; `PATH="$HOME/bin:$PATH" DOCKER_HOST=unix:///run/user/1000/docker.sock .venv/bin/python scripts/build_docker.py --tag portex:v1.0.0`; `PATH="$HOME/bin:$PATH" DOCKER_HOST=unix:///run/user/1000/docker.sock docker image inspect portex:v1.0.0 --format '{{.Id}}'`.
- Commit completed in this session: `docs(release): complete M6.5.3 artifact verification`.

# Session Plan (2026-03-12) - M7.1 Runtime Dispatch Refinement

## Goal
- Start `M7.1` on the user-approved narrow path: add a structured runtime-result boundary, then close the inbound IM/http -> runtime -> outbound reply chain without absorbing WebSocket unification or execution-plane redesign.

## Checklist
- [x] Re-read the current runtime, IM, message route, and persistence slices
- [x] Write the refined `M7.1` design doc
- [x] Write the refined `M7.1` implementation plan doc
- [x] Commit the design/plan refinement
- [x] Add failing tests for the structured runtime-result and dispatch-service contract
- [x] Implement the first `M7.1` batch and verify it

## Review
- Added `docs/plans/2026-03-12-m7-1-runtime-dispatch-refinement-design.md` and `docs/plans/2026-03-12-m7-1-runtime-dispatch-refinement.md` to lock the user-approved narrower `M7.1` execution order: structured runtime-result path first, then dispatch/IM adapters, without swallowing WebSocket unification or `M7.2`.
- Added `services/message_dispatch.py` plus a structured `run_agent_execution()` path in `services/agent_trigger.py`, so non-WebSocket callers can reuse the current runtime stack and receive `run_id/status/final_output/error/timeout_ms` without parsing broadcast strings.
- Added app-level Feishu and Telegram ingestion routes in `app/routes/im.py`, real Telegram outbound text sending, a real `/messages` dispatch path, and minimal message-correlation metadata persisted through `services/message_service.py` into the existing `attachments` field.
- Added `tests/services/test_message_dispatch.py`, `tests/app/routes/test_im_routes.py`, `tests/app/routes/test_message_routes.py`, and `tests/integration/test_message_flow.py`, and extended existing runtime/route/Telegram tests to lock the `M7.1` chain end to end.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest -o addopts='' tests/services/test_agent_trigger.py tests/services/test_message_dispatch.py tests/services/test_message_service.py tests/app/routes/test_im_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/im/test_telegram.py tests/infra/im/test_feishu.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`.
- Session commits completed: `docs(plans): refine M7.1 runtime dispatch design`, `feat(messages): add main runtime dispatch service`, `feat(messages): persist dispatch metadata`, `feat(im): add M7.1 ingestion adapters`, `feat(messages): replace message placeholder route`, `test(messages): add M7.1 integration coverage`, `docs(handoff): record M7.1 completion`.

# Session Plan (2026-03-12) - M7.2 Execution Plane Parity

## Goal
- Start `M7.2` on the approved coordinator-first path: add one per-group execution coordinator, one backend-selection policy, and one shared submission contract for Web/IM/tasks without swallowing `M7.3` workspace-model work or `M7.4` operator surfaces.

## Checklist
- [x] Re-read the current execution-plane entrypoints and backend helpers
- [x] Write the `M7.2` design doc
- [x] Write the `M7.2` implementation plan doc
- [x] Commit the `M7.2` planning docs
- [x] Add failing tests for the coordinator/policy contract
- [x] Implement the first `M7.2` batch and verify it

## Review
- Added `docs/plans/2026-03-12-m7-2-execution-plane-parity-design.md` and `docs/plans/2026-03-12-m7-2-execution-plane-parity.md` to lock the approved coordinator-first `M7.2` scope: one in-process execution coordinator, one backend policy, and one shared submission contract for Web/IM/tasks, while explicitly deferring workspace topology and operator UI.
- Added `services/execution_coordinator.py`, `services/execution_policy.py`, and replaced the old `services/group_queue.py` placeholder with a compatibility alias to the real coordinator core.
- Added `tests/services/test_execution_coordinator.py` and `tests/services/test_execution_policy.py`, covering per-group FIFO, different-group independence, session reuse, fresh session creation, queued and running cancellation, timeout, invalid mode failure, and missing-backend failure.
- Hardened running cancellation so the coordinator records terminal `cancelled` state immediately, cancels the in-flight execution task, and only performs backend cancellation as a best-effort background action; also added minimal completed-run retention so coordinator-owned state does not grow without bound in the obvious happy path.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_message_dispatch.py tests/integration/test_websocket.py -q`.
- Session commits completed so far: `docs(plans): define M7.2 execution plane parity`, `feat(execution): add M7.2 coordinator core`, `fix(execution): harden coordinator cancellation`.

# Session Plan (2026-03-12) - M7.2.2 Execution Backend Adapters

## Goal
- Continue from the documented parity handoff point by connecting the current in-process, host-process, and container runner slices to the coordinator contract, and rewire WebSocket plus IM/HTTP dispatch through that coordinator without swallowing scheduled-task execution in the same pass.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, the `M7.2` design docs, and the current execution/runtime entrypoints
- [x] Write the focused `M7.2.2` design doc
- [x] Write the focused `M7.2.2` implementation plan doc
- [x] Add failing tests for execution backends and coordinator-backed entrypoint wiring
- [x] Implement unified execution backends and default coordinator wiring
- [x] Rewire WebSocket and default IM/HTTP dispatch through the coordinator
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.2` slice with a detailed message

## Review
- Added `docs/plans/2026-03-12-m7-2-2-execution-backend-adapters-design.md` to lock this slice as “backend adapters + Web/IM/HTTP rewiring”, explicitly deferring scheduled-task submission to the next execution-plane sub-step.
- Added `docs/plans/2026-03-12-m7-2-2-execution-backend-adapters.md` with a TDD-first implementation order: backend tests first, then adapter implementation, then route/service rewiring, then verification and handoff refresh.
- Added `services/execution_backends.py` and `services/execution_runtime.py`, so the coordinator now owns three request-scoped backends: OpenAI runtime reuse, host-process runner parsing, and `docker run -i` container execution parsing.
- Rewired `app/routes/websocket.py` and default `MessageDispatchService` wiring in `app/routes/im.py` to submit `ExecutionRequest` objects through the coordinator instead of calling direct runtime helpers.
- Extended focused coverage with `tests/services/test_execution_backends.py`, coordinator-backed dispatch tests, WebSocket coordinator-route tests, message-route default wiring tests, integration WebSocket parity checks, and the new `ProcessExecutor.cancel()` test.
- Fixed three review-driven regressions before final verification: inbound-message persistence now happens before coordinator submission, WebSocket now synthesizes `run.failed` for OpenAI-backed failed results that never streamed a terminal event, and outer cancellation now calls `runtime.cancel()` before tearing down the consumer task.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest -o addopts='' tests/services/test_agent_trigger.py tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_im_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/exec/test_process.py tests/infra/exec/test_container_manager.py tests/infra/exec/test_docker.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`.
- Session commit completed: `feat(execution): complete M7.2.2 backend adapters`.

# Session Plan (2026-03-13) - M7.2.3 Execution Selection And Scheduled Tasks

## Goal
- Continue from the documented parity handoff point by routing scheduled tasks through the coordinator and by letting current request-body callers pass a real execution-mode preference into the execution plane, without expanding into group/workspace execution-mode persistence or WebSocket protocol redesign.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, the `M7.2` docs, and current task/message execution slices
- [x] Write the focused `M7.2.3` design doc
- [x] Write the focused `M7.2.3` implementation plan doc
- [x] Add failing tests for `execution_mode` propagation and scheduled-task coordinator wiring
- [x] Implement the minimal schema/service/route updates
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.3` slice with a detailed message

## Review
- Added `docs/plans/2026-03-13-m7-2-3-scheduled-tasks-and-mode-inputs-design.md` and `docs/plans/2026-03-13-m7-2-3-scheduled-tasks-and-mode-inputs.md` to lock this slice as “request-level execution-mode propagation + scheduled-task coordinator wiring”, explicitly deferring group/workspace execution-mode persistence and WebSocket payload changes.
- Extended `domain/models/task.py`, `domain/schemas.py`, `app/routes/messages.py`, `app/routes/tasks.py`, `services/message_dispatch.py`, and `services/task_service.py` so HTTP `/messages` plus scheduled-task contracts now accept optional `execution_mode`, and scheduled tasks execute through `ExecutionCoordinator` with `source="scheduled"`.
- Expanded `tests/services/test_message_dispatch.py`, `tests/services/test_task_service.py`, `tests/app/routes/test_message_routes.py`, `tests/app/routes/test_api_routes.py`, and `tests/domain/models/test_models.py` to lock explicit mode propagation, task execution-plane wiring, task-log timeout/error mapping, and the persisted task `execution_mode` contract.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/domain/models/test_models.py -q` (`75 passed, 38 warnings in 8.12s`); `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/domain/models/test_models.py tests/integration/test_message_flow.py -q` (`98 passed, 38 warnings in 10.03s`); `.venv/bin/pytest -o addopts='' -q` (`353 passed, 53 warnings in 13.90s`); `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`.
- Commit for this slice: `feat(execution): complete M7.2.3 scheduled task mode inputs`.

# Session Plan (2026-03-13) - M7.2.4 Session Workspace Lifecycle

## Goal
- Continue from the current parity handoff point by introducing a minimal coordinator-owned workspace/session lifecycle so follow-up turns reuse a real persisted execution session in the default OpenAI path, without expanding into `M7.3`'s persistent workspace model or new reset APIs.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, the `M7.2` docs, and the current execution/runtime slices
- [x] Compare the current Portex lifecycle behavior against the HappyClaw reference implementation
- [x] Write the focused `M7.2.4` design doc
- [x] Write the focused `M7.2.4` implementation plan doc
- [x] Add failing tests for workspace lifecycle state and real session persistence
- [x] Implement coordinator-owned lifecycle state plus OpenAI session persistence/retry
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.4` slice with a detailed message

## Review
- Added `docs/plans/2026-03-13-m7-2-4-session-workspace-lifecycle-design.md` and `docs/plans/2026-03-13-m7-2-4-session-workspace-lifecycle.md` to lock this slice as “coordinator-owned workspace/session lifecycle + default OpenAI runtime real session persistence”, explicitly deferring `M7.3` persistent workspace topology and any new reset API.
- Added `services/workspace_lifecycle.py` and rewired `services/execution_coordinator.py` to replace the old `_session_ids` string cache with explicit workspace lifecycle state: preview session, success-only commit, invalidate, and one fresh retry after session-resume failure.
- Extended `infra/runtime/openai.py` to pass a real Agents SDK `SQLiteSession` into `Runner.run_streamed(...)`, storing session data under `data/sessions/{group_folder}/agents-sdk.sqlite3`; `services/execution_backends.py` now maps startup-time session-resume failures into a dedicated lifecycle error without misclassifying stream-time tool errors.
- Added `tests/services/test_workspace_lifecycle.py`, and expanded `tests/services/test_execution_coordinator.py`, `tests/infra/runtime/test_openai.py`, `tests/services/test_execution_backends.py`, and `tests/services/test_agent_trigger.py` to lock success-only commit, invalidate+retry, real session injection, and hermetic test behavior without repo-local `data/sessions/` pollution.
- Multi-agent review found one real risk in the first draft: stream-time `OSError/sqlite3.Error` was too broad and could trigger a false session reset. The implementation was tightened so only session initialization/startup failures can drive the fresh-retry path; no additional findings remained in the coordinator/workspace slice.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest tests/services/test_workspace_lifecycle.py tests/services/test_execution_coordinator.py tests/services/test_execution_backends.py tests/infra/runtime/test_openai.py tests/services/test_message_dispatch.py tests/services/test_task_service.py -q`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`.
- Session commits completed: `docs(plans): define M7.2.4 session workspace lifecycle`, `feat(execution): complete M7.2.4 workspace session lifecycle`.

# Session Plan (2026-03-13) - M7.2.5 Cancel Timeout Boundary

## Goal
- Continue from the current parity handoff point by hardening cancellation and timeout semantics across the real queue + executor boundary, so host/container cleanup remains reachable after outer coroutine cancellation and timeout no longer degrades into generic `failed` states.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, the `M7.2` docs, and the current execution/runtime slices
- [x] Compare the current Portex cancel/timeout boundary against the HappyClaw reference implementation
- [x] Write the focused `M7.2.5` design doc
- [x] Write the focused `M7.2.5` implementation plan doc
- [x] Add failing tests for cleanup-aware cancel/timeout handling
- [x] Implement backend handle retention plus timeout normalization
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.5` slice with a detailed message

## Review
- Added `docs/plans/2026-03-13-m7-2-5-cancel-timeout-boundary-design.md` and `docs/plans/2026-03-13-m7-2-5-cancel-timeout-boundary.md` to lock this slice as “cleanup-aware queue/executor boundary”, explicitly deferring `M7.2.6` state/recovery surfaces and HappyClaw’s wider `_interrupt` / `_close` protocol.
- Extended `services/execution_coordinator.py` so timeout no longer blocks on synchronous `await backend.cancel(...)`; the user-visible `timeout` result is now stored immediately and backend cleanup continues in the background, matching the existing running-cancel queue-release rule.
- Extended `infra/exec/process.py` and `services/execution_backends.py` so host/container cleanup remains reachable after outer coroutine cancellation: host outer cancel now sends an immediate kill signal, host/container active handles survive long enough for cleanup, and cleanup waits are bounded instead of hanging indefinitely on `process.wait()` / docker wrapper waits.
- Added `ProcessExecutionTimeoutError` and normalized host executor timeout into a real `timeout` result in `HostProcessBackend`, rather than leaking back out as a generic `failed`.
- Expanded `tests/services/test_execution_coordinator.py`, `tests/services/test_execution_backends.py`, and `tests/infra/exec/test_process.py` to lock timeout queue release, outer-cancel cleanup reachability, bounded cleanup waits, and stable timeout background-cancel assertions.
- Multi-agent review found two real follow-ups after the first implementation: cleanup waits were still unbounded, and outer host cancellation still depended on a second-step cancel call to stop the child. Both were fixed before final verification. An additional coordinator review pointed out that the old timeout test had become timing-dependent after moving cancel to the background, so the assertion was stabilized accordingly.
- Fresh verification ran: `git diff --check`; `.venv/bin/pytest tests/services/test_execution_backends.py tests/services/test_execution_coordinator.py tests/infra/exec/test_process.py -q`; `.venv/bin/pytest tests/integration/test_websocket.py tests/app/routes/test_websocket_routes.py tests/services/test_task_service.py -q`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/services/test_scheduler.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py tests/infra/exec/test_process.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`.
- Session commits completed: `docs(plans): define M7.2.5 cancel timeout boundary`, `fix(execution): complete M7.2.5 cancel timeout boundary`, `fix(execution): bound M7.2.5 cleanup waits`.

# Session Plan (2026-03-13) - M7.2.6 Status Recovery Signaling

## Goal
- Continue from the current parity handoff point by exposing execution status and minimal recovery signals outside the current direct WebSocket stream, without expanding into `M7.3` workspace persistence or `M7.4` operator dashboards.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, the `M7.2` docs, and current execution/runtime/routes slices
- [x] Write the focused `M7.2.6` design doc
- [x] Write the focused `M7.2.6` implementation plan doc
- [x] Add failing tests for coordinator run snapshots and external status query route
- [x] Implement minimal coordinator status/recovery snapshot surface and read-only execution status API
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.6` slice with a detailed message

## Review
- Added `docs/plans/2026-03-13-m7-2-6-status-recovery-signaling-design.md` and `docs/plans/2026-03-13-m7-2-6-status-recovery-signaling.md` to lock this slice as “coordinator snapshot + read-only status query”, explicitly deferring monitor surfaces and run persistence.
- Extended `services/execution_coordinator.py` with `ExecutionRunSnapshot` plus `get_run_snapshot()` and lifecycle updates (`queued/running/terminal`) including minimal recovery signaling (`recovery_attempted/recovery_reason/recovery_succeeded`) on resume-retry paths.
- Added `app/routes/executions.py` (`GET /executions/{run_id}`) and wired it through `app/main.py`/`app/routes/__init__.py`; extended `domain/schemas.py` and `app/openapi.py` with execution-status response contracts and OpenAPI tag metadata.
- Expanded `tests/services/test_execution_coordinator.py`, added `tests/app/routes/test_execution_routes.py`, and extended `tests/app/routes/test_api_routes.py` to lock snapshot lifecycle, recovery flags, auth/404 behavior, and OpenAPI contracts.
- Added a regression guard for invalid `requested_mode` snapshots: `GET /executions/{run_id}` now normalizes unknown mode values to `None` instead of throwing a response-validation `500`; covered by `test_execution_status_route_tolerates_unknown_requested_mode`.
- Added resource-level read protection for execution snapshots: only the run owner or `owner/admin` role can read `/executions/{run_id}`; non-owner authenticated requests now return `404`, covered by `test_execution_status_route_hides_other_users_runs`.
- Fresh verification ran: `.venv/bin/pytest tests/app/routes/test_execution_routes.py::test_execution_status_route_tolerates_unknown_requested_mode -q`; `.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_api_routes.py -q -ra`; `.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_websocket.py -q`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py tests/infra/exec/test_process.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`; `git diff --check`.
- Commit for this slice: `feat(execution): complete M7.2.6 status recovery signaling`.

# Session Plan (2026-03-13) - M7.2.7 Focused Execution-Plane Tests

## Goal
- Continue from `M7.2.6` by adding focused tests for queue ordering, executor selection, follow-up/session behavior, cancellation edges, timeout payload contract, and recovery signaling behavior, without expanding into new runtime features.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and current `M7.2` execution-plane slices
- [x] Write the focused `M7.2.7` design doc
- [x] Write the focused `M7.2.7` implementation plan doc
- [x] Add failing tests for queue ordering, executor selection, cancellation edges, timeout payload, and recovery behavior
- [x] Implement only minimal fixes required by red tests
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review
- [x] Commit the `M7.2.7` slice with a detailed message

## Review
- Added `docs/plans/2026-03-13-m7-2-7-focused-tests-design.md` and `docs/plans/2026-03-13-m7-2-7-focused-tests.md` to lock this slice as “focused behavior parity tests” without expanding into new execution features.
- Expanded `tests/services/test_execution_coordinator.py` with focused tests for same-group head-failure queue progression, cross-source serialization, requested-mode backend observability via snapshots, cancellation idempotent edges, recovery-retry failure signaling, and fresh-session no-retry signaling.
- Expanded `tests/app/routes/test_websocket_routes.py` with timeout payload contract coverage (`run.timeout` with `status=timeout` and `timeout_ms`).
- No production-code changes were needed for `M7.2.7`; new focused tests passed on top of the `M7.2.6` implementation.
- Fresh verification ran: `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/app/routes/test_websocket_routes.py`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_websocket.py`; `.venv/bin/pytest -o addopts='' tests/services/test_execution_coordinator.py tests/services/test_execution_policy.py tests/services/test_execution_backends.py tests/services/test_workspace_lifecycle.py tests/services/test_message_dispatch.py tests/services/test_task_service.py tests/app/routes/test_execution_routes.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_websocket_routes.py tests/integration/test_message_flow.py tests/integration/test_websocket.py tests/infra/runtime/test_openai.py tests/infra/exec/test_process.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `cd web && npm run lint`; `cd web && npm run build`; `git diff --check`.
- Commit for this slice: `test(execution): complete M7.2.7 focused parity coverage`.

# Session Plan (2026-03-13) - M7.3.1 Persisted Group Listing

## Goal
- Continue from the current parity handoff point by replacing the hard-coded `/groups` demo output with a real persisted registered-group listing model, and by lazily registering resolved HTTP/IM targets into that registry without defining the final workspace/home/binding topology.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, the `M7.1`/`M7.2` design docs, and current group/message/IM slices
- [x] Compare the current Portex group/workspace surface against the HappyClaw reference implementation
- [x] Write the focused `M7.3.1` design doc
- [x] Write the focused `M7.3.1` implementation plan doc
- [x] Add failing tests for the registry service, `/groups` listing, and dispatch registration hook
- [x] Implement the minimal persisted registry service and route/dispatch wiring
- [x] Run focused verification and broader regression
- [x] Update `docs/progress.md` and this session review

## Review
- Added `docs/plans/2026-03-13-m7-3-1-persisted-group-listing-design.md` and `docs/plans/2026-03-13-m7-3-1-persisted-group-listing.md` to lock this slice as “DB-backed registered-group list + lazy auto-registration”, explicitly deferring home workspace, IM binding metadata, and richer workspace APIs.
- Added `services/group_registry.py` plus `tests/services/test_group_registry.py`, turning `domain.models.group.RegisteredGroup` into a real async service boundary with `list_registered_groups()` and idempotent `ensure_registered_group(...)`.
- Rewired `app/routes/groups.py` so `GET /groups` now reads the registry instead of returning hard-coded `group-demo`, while preserving the current `group_id/name` response shape by mapping `group_id` to the persisted `folder`.
- Extended `services/message_dispatch.py` with an optional registration hook and rewired the default dependency path in `app/routes/im.py` so HTTP and IM dispatch lazily persist the current `chat_jid -> group_folder` target into `registered_groups` before execution continues.
- Expanded `tests/services/test_message_dispatch.py`, `tests/app/routes/test_message_routes.py`, and `tests/app/routes/test_api_routes.py` to lock registration order, default HTTP dispatch wiring, and the route-level registry-backed list contract.
- Fresh verification ran: `.venv/bin/pytest tests/services/test_group_registry.py tests/app/routes/test_api_routes.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py -q`; `.venv/bin/pytest tests/services/test_group_registry.py tests/services/test_message_dispatch.py tests/app/routes/test_message_routes.py tests/app/routes/test_api_routes.py tests/app/routes/test_im_routes.py tests/integration/test_message_flow.py tests/integration/test_api.py tests/integration/test_websocket.py -q`; `.venv/bin/pytest -o addopts='' -q`; `.venv/bin/ruff check .`; `git diff --check`.

# Session Plan (2026-03-16) - M8.3 Terminal Operator UX Implementation On Main

## Goal
- Continue from the current handoff state by implementing `M8.3` directly on `main`: add a read-only terminal overview API, a standalone `/terminals` operator page, and minimal `/chat?workspace=...` deep-link support, while preserving existing terminal control boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and `M8.3` design/plan docs
- [x] Add failing tests for terminal session listing read helper
- [x] Implement `TerminalSessionService.list_sessions()` and make focused service tests pass
- [x] Add failing route/OpenAPI tests for `GET /terminals`
- [x] Implement `GET /terminals` aggregation route and schemas
- [x] Add frontend red stage for `/terminals` route and navigation
- [x] Implement frontend terminals overview page + API hook/client
- [x] Add minimal `ChatPanel` workspace deep-link behavior
- [x] Run focused verification + repo regression + lint/build + diff hygiene
- [x] Update `docs/progress.md` and complete this review section
- [x] Commit milestone result with a detailed message

## Review
- Backend `M8.3` read surface is now on `main`: `TerminalSessionService.list_sessions()` + `GET /terminals` terminal overview route + `TerminalWorkspaceSummaryResponse`/`TerminalWorkspaceListResponse` schemas.
- Added dedicated route coverage in `tests/app/routes/test_terminal_monitor_routes.py`, expanded service coverage in `tests/services/test_terminal_sessions.py`, and extended OpenAPI contract coverage in `tests/app/routes/test_api_routes.py`.
- Frontend `M8.3` surface is now on `main`: `/terminals` page, operator-only navigation entry, `getTerminalOverview` client + `useTerminalOverviewQuery`, and minimal `/chat?workspace=...` initial workspace deep-link behavior in `ChatPanel`.
- `docs/progress.md` has been refreshed to move `M8.3` to completed-on-`main` state and reset restart guidance to post-`M8.3` continuation options.
- Fresh verification commands executed in this session:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py -q`
  - `.venv/bin/pytest tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`
  - `cd web && npm ci`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `.venv/bin/pytest -o addopts='' -q` (`564 passed`)
  - `.venv/bin/ruff check .`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.4 Terminal Light Controls

## Goal
- Continue post-`M8.3` by adding minimal terminal operator control actions on top of the new overview surface: allow operators to close their own active sessions and force-close active sessions through a dedicated API, without expanding into TTY fidelity/session persistence scope.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and `M8.3` docs
- [x] Write focused `M8.4` design doc
- [x] Write focused `M8.4` implementation plan doc
- [x] Add failing tests for force-close service and route contract
- [x] Implement backend force-close session capability and route
- [x] Add failing frontend build stage for terminals control actions
- [x] Implement `/terminals` close/force-close actions and API client updates
- [x] Run focused verification + frontend lint/build + full regression + hygiene checks
- [x] Update `docs/progress.md` and complete this review section
- [x] Commit milestone result with a detailed message

## Review
- Added `docs/plans/2026-03-16-m8-4-terminal-light-controls-design.md` and `docs/plans/2026-03-16-m8-4-terminal-light-controls.md` to lock M8.4 scope as “light control actions only”, explicitly deferring fidelity/session-persistence work.
- Extended backend terminal lifecycle with `TerminalSessionService.force_close_session_by_group()` and exposed `DELETE /terminals/{group_id}/sessions/force` in `app/routes/terminals.py`, preserving existing role/access gates and response contracts.
- Expanded backend coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py`; retained compatibility with existing terminal overview tests.
- Upgraded `web/src/pages/Terminals.tsx` from read-only to light-control UI: row-level `Close` (own active session) and `Force Close` (operator action), with action loading states and inline notice/error; wired via new `apiClient.forceCloseCurrentTerminalSession()` in `web/src/api/client.ts`.
- Recorded frontend red-green evidence for this slice: first introduced `forceCloseCurrentTerminalSession` call in page (missing client method) and confirmed `cd web && npm run build` failed; then implemented client + UI wiring and restored build green.
- Refreshed `docs/progress.md` to mark `M8.4` complete on `main` and move restart guidance to post-`M8.4` fidelity/session-management continuation.
- Fresh verification commands executed in this session:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `cd web && npm run build` (red stage expected fail before client method)
  - `cd web && npm run lint`
  - `cd web && npm run build` (green stage)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`566 passed`)
  - `.venv/bin/ruff check .`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.5.1 Terminal Output Replay On Reconnect

## Goal
- Start post-`M8.4` terminal fidelity/session-management work with a minimal high-value slice: keep recent terminal output in-memory per session and replay it on reconnect, so users can recover context after websocket reconnects without introducing persistent terminal storage.

## Checklist
- [x] Re-read terminal runtime slices and existing websocket/terminal panel behavior
- [x] Write focused `M8.5.1` design doc
- [x] Write focused `M8.5.1` implementation plan doc
- [x] Add failing tests for output history replay and bounded history behavior
- [x] Implement terminal session output history buffer + replay on attach
- [x] Integrate frontend transcript behavior for reconnect replay (avoid duplicate transcript buildup)
- [x] Run focused verification + frontend lint/build + full regression + hygiene checks
- [x] Update `docs/progress.md` and complete this review section
- [x] Commit milestone result with a detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-1-terminal-output-replay-design.md` and `docs/plans/2026-03-16-m8-5-1-terminal-output-replay.md` to lock this slice as “bounded in-memory output replay on reconnect”, explicitly deferring persistent transcript storage and wider TTY fidelity changes.
- Expanded `tests/services/test_terminal_sessions.py` with red-first coverage for reconnect replay and history-cap eviction; initial run failed as expected due missing `history_max_bytes`/replay logic.
- Implemented bounded output history in `services/terminal_sessions.py` by extending managed session state with rolling chunk buffer + byte accounting, recording output chunks in bridge-event handling, and replaying buffered output on `attach_session()`.
- Updated `web/src/components/chat/TerminalPanel.tsx` so reconnect clears the current workspace transcript before socket attach, letting server replay repopulate content without duplicate local buildup.
- Refreshed `docs/progress.md` to mark `M8.5.1` complete and move restart guidance to post-`M8.5.1` fidelity sub-slices.
- Fresh verification commands executed in this session:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` (red and green cycles)
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`568 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint && npm run build`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.5.2 Terminal Resize Fidelity

## Goal
- Continue post-`M8.5.1` fidelity work by replacing terminal resize no-op behavior with real PTY size propagation and dynamic frontend resize emission, while keeping current terminal ownership/session boundaries unchanged.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and `M8.5.1`/terminal runtime slices
- [x] Write focused `M8.5.2` design doc
- [x] Write focused `M8.5.2` implementation plan doc
- [x] Add failing bridge-focused tests for TTY startup and resize propagation
- [x] Implement PTY-backed `DockerExecTerminalBridge` resize behavior
- [x] Keep terminal service/websocket resize forwarding coverage green
- [x] Improve `TerminalPanel` to emit panel-based dynamic resize events
- [x] Run focused terminal verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md` with `M8.5.2` evidence and next-step guidance
- [x] Add session review notes in `tasks/todo.md`
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-2-terminal-resize-fidelity-design.md` and `docs/plans/2026-03-16-m8-5-2-terminal-resize-fidelity.md` to lock `M8.5.2` scope before implementation.
- Added `tests/services/test_terminal_bridge.py` with red-green coverage for interactive TTY startup flags and PTY resize ioctl propagation.
- Refactored `services/terminal_bridge.py` from pipe/no-op resize to PTY-backed bridge (`docker exec -it` + PTY output forwarding + `TIOCSWINSZ` resize).
- Updated `web/src/components/chat/TerminalPanel.tsx` to emit dynamic resize dimensions (ready + delayed ready + window resize throttling with dedupe), replacing fixed `120x32`.
- Updated `docs/progress.md` to move restart baseline to post-`M8.5.2`.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_bridge.py -q` (red first, then green)
  - `.venv/bin/pytest tests/services/test_terminal_bridge.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`570 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Commit: `87322e1` (`feat(terminal): complete M8.5.2 resize fidelity`).

# Session Plan (2026-03-16) - M8.5.3 Terminal History Read Surface

## Goal
- Continue post-`M8.5.2` session-management work by adding a minimal read-only terminal history API for the current workspace session, reusing existing bounded in-memory output history.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and latest terminal slices
- [x] Write focused `M8.5.3` design doc
- [x] Write focused `M8.5.3` implementation plan doc
- [x] Add failing tests for service history snapshot behavior
- [x] Add failing route tests for terminal history read endpoint
- [x] Add failing OpenAPI assertions for the new route contract
- [x] Implement `TerminalSessionService` history snapshot read helper
- [x] Add `TerminalSessionHistoryResponse` schema and wire route response model
- [x] Implement `GET /terminals/{group_id}/sessions/current/history`
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md` with `M8.5.3` evidence and next-step guidance
- [x] Add session review notes in `tasks/todo.md`
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-3-terminal-history-read-surface-design.md` and `docs/plans/2026-03-16-m8-5-3-terminal-history-read-surface.md` to lock this slice as “terminal history read surface only,” explicitly deferring cross-process persistence.
- Extended `services/terminal_sessions.py` with `TerminalSessionHistorySnapshot` and `get_history_by_group()` to expose a lock-protected in-memory history snapshot (`output`, `output_bytes`, `history_max_bytes`, `truncated`) for the current workspace session.
- Added `TerminalSessionHistoryResponse` in `domain/schemas.py` and exported it for OpenAPI/schema use.
- Added route `GET /terminals/{group_id}/sessions/current/history` in `app/routes/terminals.py`, reusing existing terminal role + workspace access checks and existing terminal error mapping.
- Expanded tests in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` with red-green coverage for service snapshot behavior, route auth/success/not-found behavior, and OpenAPI route contract.
- Updated `docs/progress.md` to mark `M8.5.3` complete and move next-step guidance to post-`M8.5.3` persistence.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`574 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Commit: `010cc40` (`feat(terminal): complete M8.5.3 history read surface`).

# Session Plan (2026-03-16) - M8.5.4 Terminal History Persistence Fallback

## Goal
- Continue post-`M8.5.3` session-management work by persisting latest terminal history snapshots and enabling `current/history` reads to fall back after process restart.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and latest terminal slices
- [x] Write focused `M8.5.4` design doc
- [x] Write focused `M8.5.4` implementation plan doc
- [x] Add failing tests for history persistence fallback across fresh service instances
- [x] Implement safe terminal history snapshot persistence helpers in `TerminalSessionService`
- [x] Persist snapshot on output updates and terminal-state transitions
- [x] Add disk fallback logic to `get_history_by_group()`
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md` with `M8.5.4` evidence and next-step guidance
- [x] Add session review notes in `tasks/todo.md`
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-4-terminal-history-persistence-fallback-design.md` and `docs/plans/2026-03-16-m8-5-4-terminal-history-persistence-fallback.md` to lock `M8.5.4` scope as “history persistence fallback only,” explicitly deferring active session recovery.
- Extended `services/terminal_sessions.py` with safe file-backed snapshot persistence under `data/terminal-history/<workspace>/latest.json`, including atomic write + path validation guardrails.
- Updated `TerminalSessionService.get_history_by_group()` to fall back to persisted snapshot when no in-memory session exists, preserving existing route/DTO contract.
- Wired snapshot refresh on output changes and terminal-state transitions (`closed`/`exited`) so persisted history reflects latest bounded buffer and status.
- Expanded `tests/services/test_terminal_sessions.py` with red-green restart-like fallback coverage (fresh service instance loads persisted snapshot).
- Updated `docs/progress.md` to mark `M8.5.4` complete and move next-step guidance to active session persistence/recovery.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` (red then green)
  - `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`575 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Commit: `0563192` (`feat(terminal): complete M8.5.4 history persistence fallback`).

# Session Plan (2026-03-16) - M8.5.5 Terminal Active Session Persistence/Recovery

## Goal
- Continue from `M8.5.4` by adding active terminal session persistence/recovery across process restart, while keeping existing HTTP/WebSocket contracts unchanged.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and latest terminal slices
- [x] Write focused `M8.5.5` design doc
- [x] Write focused `M8.5.5` implementation plan doc
- [x] Add failing tests for active-session restart recovery semantics (service + route)
- [x] Implement active session recovery in `TerminalSessionService` (startup rehydrate + lazy attach bridge + fallback close)
- [x] Persist snapshot on active lifecycle transitions (`created`/`attached`/`detached`)
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md` and complete this review section
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-5-terminal-active-session-recovery-design.md` and `docs/plans/2026-03-16-m8-5-5-terminal-active-session-recovery.md` to lock `M8.5.5` scope as “active session persistence/recovery only,” explicitly deferring persistence-aware multi-session inventory.
- Extended `services/terminal_sessions.py` with optional startup recovery (`recover_active_sessions`) that rehydrates persisted active snapshots as detached in-memory sessions, and with recovered-session lazy bridge attach + attach-failure close fallback.
- Added active lifecycle snapshot persistence for `created`/`attached`/`detached`, keeping restart semantics consistent even without fresh terminal output.
- Updated `services/execution_runtime.py` so runtime default terminal service enables active recovery, while `TerminalSessionService` default remains recovery-off to keep test isolation deterministic.
- Expanded `tests/services/test_terminal_sessions.py` and `tests/app/routes/test_terminal_routes.py` with red-green coverage for active-session restart recovery, owner attach of recovered sessions, cross-owner conflict continuity, and attach-failure fallback behavior.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py -q` (red then green)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`581 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.5.6 Persistence-Aware Terminal History Inventory

## Goal
- Continue from `M8.5.5` by exposing persisted terminal history inventory in the existing `/terminals` operator overview, without adding a new standalone inventory route.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and latest terminal slices
- [x] Write focused `M8.5.6` design doc
- [x] Write focused `M8.5.6` implementation plan doc
- [x] Add failing tests for history inventory contract (service + monitor route + openapi)
- [x] Implement backend inventory read model (`TerminalSessionService` + schemas + `/terminals` mapping)
- [x] Update frontend `/terminals` page to render history inventory metadata
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md` and complete this review section
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-6-terminal-history-inventory-design.md` and `docs/plans/2026-03-16-m8-5-6-terminal-history-inventory.md` to lock scope as “overview additive history inventory,” explicitly deferring dedicated inventory route and timeline/pagination.
- Extended `services/terminal_sessions.py` with `TerminalSessionHistorySummary` and `list_history_summaries()`, merging in-memory and persisted (`latest.json`) history metadata per workspace without returning transcript text.
- Extended `domain/schemas.py` and `app/routes/terminals.py` with additive overview `history` contract (`TerminalSessionHistorySummaryResponse`) and route mapping for `/terminals`.
- Updated `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so the operator page renders history metadata columns (`history session`, `history bytes`, `history truncated`) while preserving existing actions.
- Added red-green coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_monitor_routes.py`, and `tests/app/routes/test_api_routes.py` for merged inventory behavior, route payload mapping, and OpenAPI schema exposure.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`582 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.5.7 Terminal History Timeline/Pagination

## Goal
- Continue from `M8.5.6` by adding a multi-snapshot terminal history timeline with pagination for each workspace, while keeping existing `latest.json` and `/sessions/current/history` contracts backward-compatible.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, `tasks/lessons.md`, and latest terminal slices
- [x] Write focused `M8.5.7` design doc
- [x] Write focused `M8.5.7` implementation plan doc
- [x] Add failing tests for timeline pagination contract (service + route + openapi)
- [x] Implement backend multi-snapshot persistence/timeline read model with `latest.json` compatibility
- [x] Implement `GET /terminals/{group_id}/sessions/history` with `limit/offset` pagination
- [x] Add minimal frontend timeline query + `/terminals` on-demand timeline view
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-7-terminal-history-timeline-pagination-design.md` and `docs/plans/2026-03-16-m8-5-7-terminal-history-timeline-pagination.md` to lock scope as “multi-snapshot timeline/pagination,” explicitly preserving `latest.json` and `/sessions/current/history` compatibility.
- Extended `services/terminal_sessions.py` with snapshot archiving under `data/terminal-history/<workspace>/snapshots/`, timeline dedupe merge (`in-memory + latest + archived`), and paginated `list_history_timeline_by_group(limit, offset)` read model.
- Extended `domain/schemas.py` and `app/routes/terminals.py` with `TerminalSessionHistoryTimelineResponse` and `GET /terminals/{group_id}/sessions/history` (query `limit/offset`) while reusing existing terminal role/workspace access/error mapping.
- Extended `web/src/api/client.ts`, `web/src/hooks/useApi.ts`, `web/src/pages/Terminals.tsx`, and `web/src/index.css` with on-demand timeline fetch, per-workspace `View Timeline` action, and simple `Previous/Next` pagination controls.
- Added red-green timeline coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for pagination ordering, latest+archive dedupe, malformed archive tolerance, route auth/404 behavior, and OpenAPI path/schema exposure.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`588 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`

# Session Plan (2026-03-16) - M8.5.8 Terminal History Filters/Detail

## Goal
- Continue from `M8.5.7` by adding server-side timeline filters plus per-session history detail, while keeping existing `latest.json` and `/sessions/current/history` contracts backward-compatible.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and latest terminal slices
- [x] Write focused `M8.5.8` design doc
- [x] Write focused `M8.5.8` implementation plan doc
- [x] Add failing service tests for timeline filters and detail lookup
- [x] Implement backend timeline filters/detail read model
- [x] Add failing route/OpenAPI tests for filter/detail surface
- [x] Implement timeline filter query params and history detail route/schema
- [x] Drive frontend RED by referencing new filter/detail contract
- [x] Implement typed client/hooks and `/terminals` filter/detail UI
- [x] Run focused terminal/backend verification suite
- [x] Run full backend regression, Ruff, frontend lint/build, and diff hygiene checks
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with detailed message

## Review
- Added `docs/plans/2026-03-16-m8-5-8-terminal-history-filters-detail-design.md` and `docs/plans/2026-03-16-m8-5-8-terminal-history-filters-detail.md` to lock scope as “timeline filters + session detail,” explicitly preserving `latest.json` and `/sessions/current/history` compatibility while deferring full-text search.
- Extended `services/terminal_sessions.py` with additive `status` / `owner_user_id` / `session_id_prefix` server-side filters on `list_history_timeline_by_group(...)`, shared merged snapshot lookup, and `get_history_snapshot_by_group(...)` so timeline and detail reuse the same dedupe behavior across `in-memory + latest + archived`.
- Extended `domain/schemas.py` and `app/routes/terminals.py` with additive `snapshot_at` summary data, `TerminalSessionHistoryDetailResponse`, `GET /terminals/{group_id}/sessions/history/{session_id}`, and timeline filter query params. Added a compatibility fallback so legacy overview fake summaries without `snapshot_at` still serialize safely.
- Extended `web/src/api/client.ts`, `web/src/hooks/useApi.ts`, and `web/src/pages/Terminals.tsx` with timeline filter options, history detail query support, `snapshot_at` rendering, and an in-page detail panel on `/terminals`.
- Added red-green coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for service-level filtering/detail lookup, route filter passthrough, detail `404` mapping, and OpenAPI filter/detail contracts.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` (red then green)
  - `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `cd web && npm run build` (red then green after API/hook/page implementation)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`596 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`

# Session Plan (2026-03-17) - M8.5.11 Terminal Search Pagination/Cross-Session Match Navigation

## Goal
- Continue from the current `M8.5.8` main baseline by adding output search with paginated results and cross-session match navigation in terminal history detail, while preserving existing RBAC and history compatibility boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and `tasks/lessons.md`
- [x] Write focused `M8.5.11` design doc
- [x] Write focused `M8.5.11` implementation plan doc
- [x] Add failing backend tests for search service/route/openapi contracts
- [x] Implement backend search service model + schema + route
- [x] Drive frontend RED for search pagination/cross-session navigation
- [x] Implement frontend search panel and cross-session match navigation behavior
- [x] Run focused terminal regression suite
- [x] Run full backend/frontend verification plus diff hygiene
- [x] Update `docs/progress.md` and complete review notes
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-17-m8-5-11-terminal-search-pagination-cross-session-navigation-design.md` and `docs/plans/2026-03-17-m8-5-11-terminal-search-pagination-cross-session-navigation.md` to lock scope as “search-result pagination + cross-session match navigation,” while preserving `latest.json` and `/sessions/current/history` compatibility.
- Extended `services/terminal_sessions.py` with additive search read models (`TerminalSessionHistorySearchMatch`, `TerminalSessionHistorySearchPage`) plus `search_history_by_group(...)`, case-insensitive matching, snippet extraction, and deterministic result ordering/pagination.
- Extended `domain/schemas.py` and `app/routes/terminals.py` with additive search DTOs and `GET /terminals/{group_id}/sessions/history/search`, reusing existing terminal role/workspace access gates and error mapping.
- Extended terminal coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` with RED/GREEN assertions for search behavior, route contracts, and OpenAPI exposure.
- Extended frontend terminal search/navigation surface in `web/src/api/client.ts`, `web/src/hooks/useApi.ts`, and `web/src/pages/Terminals.tsx`: workspace output search panel, paginated search results, detail keyword highlighting, and previous/next traversal that can jump across matched sessions/pages.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`602 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`

# Session Plan (2026-03-17) - M8.5.12 Terminal Snippet-to-Offset Deep Link

## Goal
- Continue post-`M8.5.11` by adding snippet-level deep links so operators can jump from a specific search snippet directly to its corresponding match location in terminal history detail, while preserving RBAC and history compatibility boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and current terminal search/detail slices
- [x] Write focused `M8.5.12` design doc
- [x] Write focused `M8.5.12` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing backend tests for snippet position metadata (service + route + OpenAPI)
- [x] Implement additive backend snippet metadata contracts (`match_index`, `match_offset`, `text`)
- [x] Implement frontend snippet click deep link to exact detail match
- [x] Run focused terminal regression suite
- [x] Run full backend/frontend verification plus diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `docs/plans/2026-03-17-m8-5-12-terminal-snippet-offset-deeplink-design.md` and `docs/plans/2026-03-17-m8-5-12-terminal-snippet-offset-deeplink.md` to lock scope as “snippet-to-offset deep link,” while preserving `latest.json` and `/sessions/current/history` compatibility.
- Extended `services/terminal_sessions.py` with additive snippet metadata in search results: `snippet_matches` (`text`, `match_index`, `match_offset`) while keeping compatibility `snippets`.
- Extended `domain/schemas.py` and `app/routes/terminals.py` with `TerminalSessionHistorySearchSnippetResponse` and additive `snippet_matches` mapping for `GET /terminals/{group_id}/sessions/history/search`.
- Added red-green coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for service metadata, route payload contract, and OpenAPI schema exposure.
- Extended `web/src/api/client.ts` and `web/src/pages/Terminals.tsx` so search snippets are clickable and deep-link detail selection by `match_offset` with `match_index` fallback.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q` (red then green)
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`602 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Commit: completed in this session with `feat(terminal): complete M8.5.12 snippet offset deep links`.

# Session Plan (2026-03-17) - M8.5.13 Terminal Search Filter Alignment

## Goal
- Continue post-`M8.5.12` by aligning terminal-history search with the existing timeline filters (`status`, `owner_user_id`, `session_id_prefix`) while preserving RBAC and history compatibility boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and current terminal search/timeline slices
- [x] Write focused `M8.5.13` design doc
- [x] Write focused `M8.5.13` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing backend tests for filtered search behavior (service + route + OpenAPI)
- [x] Implement additive backend search filter contracts
- [x] Drive frontend RED for filter-aligned search query state
- [x] Implement frontend search filter alignment on `/terminals`
- [x] Run focused terminal regression suite
- [x] Run full backend/frontend verification plus diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Extended `services/terminal_sessions.py` so `search_history_by_group(...)` accepts additive `status`, `owner_user_id`, and `session_id_prefix` filters and reuses `_filter_history_snapshots(...)` before output matching; filtered-empty snapshot sets now preserve the intended `TerminalSessionNotFoundError` path.
- Extended `app/routes/terminals.py` so `GET /terminals/{group_id}/sessions/history/search` accepts the same three optional query parameters as the timeline route and forwards them without changing the response DTO shape.
- Added backend coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for independent service filter behavior, filtered-empty `404`, route pass-through, and OpenAPI parameter exposure.
- Extended `web/src/api/client.ts`, `web/src/hooks/useApi.ts`, and `web/src/pages/Terminals.tsx` so terminal-history search reuses the current timeline filter state, includes those filters in the query key/request params, and resets search pagination/navigation state when filters change.
- Verification executed:
  - `npm run build` in `web/` RED before frontend wiring: TypeScript rejected extra `status` property on `useTerminalHistorySearchQuery(...)` options.
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q` (`606 passed`)
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commit: `93f5385` (`feat(terminal): complete M8.5.13 search filter alignment`).

# Session Plan (2026-03-17) - M8.5.14 Terminal Time-Range Filters

## Goal
- Continue post-`M8.5.13` by adding inclusive `snapshot_from` / `snapshot_to` filters to terminal history timeline and search, with local minute-granularity controls on `/terminals`, while preserving RBAC and history compatibility boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and current terminal timeline/search slices
- [x] Write focused `M8.5.14` design doc
- [x] Write focused `M8.5.14` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing backend tests for timeline/search time-range filtering (service + route + OpenAPI)
- [x] Implement additive backend time-range filter contracts
- [x] Drive frontend RED for time-range filter query state
- [x] Implement frontend time-range controls on `/terminals`
- [x] Run focused terminal regression suite
- [x] Run full backend/frontend verification plus diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Extended `services/terminal_sessions.py` and `app/routes/terminals.py` so timeline/search both accept inclusive `snapshot_from` / `snapshot_to` filters and reject invalid ranges with `400` via `ValueError`.
- Added backend coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for inclusive lower/upper bounds, bounded windows, invalid ranges, route pass-through, and OpenAPI parameter exposure.
- Extended `web/src/api/client.ts`, `web/src/hooks/useApi.ts`, and `web/src/pages/Terminals.tsx` so `/terminals` exposes minute-granularity `datetime-local` inputs, converts local values to UTC request params, and keeps timeline/search on one shared filter state.
- Verification executed:
  - `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
  - `.venv/bin/pytest -o addopts='' -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
  - `git diff --check`
- Feature commits: `7515207` (`feat(terminal): add M8.5.14 backend time-range filters`) and `a628cc9` (`feat(web): add M8.5.14 time-range filter controls`).

# Session Plan (2026-03-17) - M8.5.14 Handoff Refresh

## Goal
- Sync the current restart-oriented state after the final `M8.5.14` landing so the next Codex restart can resume from the latest baseline without re-deriving commit context.

## Checklist
- [x] Re-read `docs/progress.md`, `docs/TODO.md`, `AGENTS.md`, and recent commits
- [x] Refresh `docs/progress.md` latest baseline anchors
- [x] Refresh `AGENTS.md` latest handoff/reference notes
- [x] Run doc hygiene verification
- [x] Commit the handoff refresh

## Review
- `docs/progress.md` now distinguishes the latest functional milestone commit from the latest handoff-sync commit, which is more stable for restart context after docs-only commits land.
- `AGENTS.md` now points at the latest restart-oriented handoff sync explicitly while keeping the latest functional terminal milestone chain intact.
- Verification for this docs-only sync will be `git diff --check`.
- Commit completed in this session: `docs(handoff): refresh latest progress anchors`.

# Session Plan (2026-03-18) - M8.5.16 Terminal Search Sort Controls

## Goal
- Continue post-`M8.5.15` by adding explicit terminal-history search sort controls (`relevance`, `newest`, `oldest`) while preserving RBAC, history compatibility, and the current timeline/detail boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and current terminal search slices
- [x] Write focused `M8.5.16` design doc
- [x] Write focused `M8.5.16` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing backend tests for search sort modes (service + route + OpenAPI)
- [x] Implement additive backend search sort contracts
- [x] Drive frontend RED for search sort query state
- [x] Implement frontend sort controls on `/terminals`
- [x] Run focused terminal regression suite
- [x] Run full backend/frontend verification plus diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added `sort` support to terminal history search end-to-end: `TerminalSessionService.search_history_by_group(...)` now accepts `relevance` / `newest` / `oldest`, the search route forwards the query parameter with default `relevance`, and OpenAPI now exposes the additive search-only contract.
- Added focused coverage in `tests/services/test_terminal_sessions.py`, `tests/app/routes/test_terminal_routes.py`, and `tests/app/routes/test_api_routes.py` for default ordering, explicit sort modes, pagination over the sorted result set, invalid sort rejection, and OpenAPI parameter exposure.
- Extended `web/src/api/client.ts`, `web/src/hooks/useApi.ts`, and `web/src/pages/Terminals.tsx` so `/terminals` exposes a search sort selector, includes sort in the request/query-key path, resets pagination/detail anchors when the active search ordering changes, and restores `relevance` on `Clear`.
- Verification executed: `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`614 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Feature commit completed in this session: `5761a3a` (`feat(terminal): add M8.5.16 search sort controls`).
- Handoff sync commit for this session: `docs(handoff): sync M8.5.16 search sort context`.

# Session Plan (2026-03-18) - M8.5.17 Terminal Relevance Ranking

## Goal
- Continue post-`M8.5.16` by refining default terminal-history `relevance` ordering so stronger textual matches outrank merely newer results, while preserving current search API, pagination semantics, and RBAC/history compatibility boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and current terminal search slices
- [x] Write focused `M8.5.17` design doc
- [x] Write focused `M8.5.17` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing backend service tests for relevance heuristic ordering
- [x] Implement additive backend relevance ranking heuristics
- [x] Run focused terminal regression suite
- [x] Run full backend/frontend verification plus diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added service-side TDD coverage in `tests/services/test_terminal_sessions.py` for concentrated-vs-sparse matches, first-match-position tie-breaking, weak recency behavior, and pagination over the globally ranked `relevance` result set.
- Refined `services/terminal_sessions.py` so `relevance` now sorts by `match_count`, `cluster_span`, `first_match_offset`, `match_density`, weak recency, and `session_id`, while preserving `newest` / `oldest`, response DTOs, snippets, deep links, `latest.json`, `/sessions/current/history`, and RBAC boundaries.
- RED verification ran: `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` -> `3 failed` in the new relevance-heuristic tests before implementation; GREEN rerun passed after the backend-only sort refinement.
- Verification executed: `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`618 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Feature commit completed in this session: `a40fdda` (`feat(terminal): refine M8.5.17 relevance ranking`).

# Session Plan (2026-03-18) - M8.5.18 Terminal Word-Boundary Relevance

## Goal
- Continue post-`M8.5.17` by refining default terminal-history `relevance` ordering so whole-word matches outrank substring-only matches, while preserving current search API, pagination semantics, and RBAC/history compatibility boundaries.

## Checklist
- [x] Re-read `AGENTS.md`, `docs/progress.md`, `docs/TODO.md`, and current terminal search slices
- [x] Write focused `M8.5.18` design doc
- [x] Write focused `M8.5.18` implementation plan doc
- [x] Add this session checklist before implementation
- [x] Add failing backend service tests for word-boundary ordering
- [x] Implement additive backend word-boundary relevance signals
- [x] Stabilize no-whole-word fallback ordering and regression coverage
- [x] Run focused terminal regression suite
- [x] Run full backend/frontend verification plus diff hygiene
- [x] Update `docs/progress.md`, `AGENTS.md`, and complete this review section
- [x] Commit milestone changes with a detailed message

## Review
- Added service-side TDD coverage in `tests/services/test_terminal_sessions.py` for whole-word-vs-substring ordering, first whole-word offset tie-break, no-whole-word fallback to `M8.5.17` signals, and pagination over globally ranked `relevance` results.
- Refined `services/terminal_sessions.py` so `relevance` now adds `whole_word_match_count` and `first_whole_word_offset` ahead of existing `M8.5.17` signals, while preserving `newest` / `oldest`, response DTOs, snippets, deep links, `latest.json`, `/sessions/current/history`, and RBAC boundaries.
- Addressed review findings by introducing a stable no-whole-word sentinel (`_NO_WHOLE_WORD_MATCH_OFFSET`) and strengthening fallback fixture design so transcript length cannot mask fallback-ordering regressions.
- Verification executed: `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`, `.venv/bin/pytest -o addopts='' -q` (`622 passed`), `.venv/bin/ruff check .`, `cd web && npm run lint`, `cd web && npm run build`, and `git diff --check`.
- Feature commits completed in this session: `244da16` (`feat(terminal): add M8.5.18 word-boundary relevance`) and `8a122d2` (`fix(terminal): stabilize M8.5.18 no-whole-word fallback ordering`).
