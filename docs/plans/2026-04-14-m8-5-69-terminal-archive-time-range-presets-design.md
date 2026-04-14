# M8.5.69 Terminal Archive Time-Range Presets Design

## Goal

Add archive-only preset time-range shortcuts on `/terminals` so operators can apply recent-window archive filters with one click instead of manually entering both datetime bounds.

## Scope

- frontend-only change in `/terminals`
- add archive-only preset buttons in the top-level summary filter area:
  - `1h`
  - `6h`
  - `24h`
  - `7d`
  - `30d`
- reuse the existing local-datetime preset helper and local-datetime -> UTC ISO query conversion
- keep preset state local to the page
- clear archive preset highlight when archive datetime inputs are manually edited or reset
- keep `Export History Archive JSON` as the only action that consumes the top-level archive filters

## Out Of Scope

- no backend route changes
- no API client contract changes
- no new top-level archive filter parameters
- no changes to workspace-scoped timeline/search/detail/export/archive surfaces
- no persistence of archive preset state across reloads
- no new frontend test harness

## Context

`M8.5.62` introduced top-level archive owner/session/time filters, and `M8.5.67` / `M8.5.68` completed the current archive-only summary/reset/chip UX. That surface is now functionally complete enough that it should not grow more backend knobs without evidence.

There is still one frontend consistency gap: timeline/search already expose reusable `1h` / `6h` / `24h` / `7d` / `30d` shortcuts, but the top-level archive filter form still requires typing both datetime fields manually. Since the archive route already accepts the same time semantics, the smallest useful next step is to reuse the preset interaction pattern without changing backend behavior.

## Approaches Considered

### 1. Add archive-only preset buttons reusing the existing helper and button pattern (recommended)

Pros:

- closes a real usability gap with no backend work
- matches the existing terminal timeline/search mental model
- keeps archive semantics unchanged

Cons:

- introduces one more small piece of local page state

### 2. Add one-click "last 24 hours" only

Pros:

- even smaller UI delta

Cons:

- inconsistent with the existing preset family
- undershoots the already-established terminal filter pattern

### 3. Leave archive time filtering manual-only

Pros:

- zero code change

Cons:

- leaves the top-level archive flow less ergonomic than the existing workspace-scoped surfaces

## Recommended Approach

Use approach 1.

Add a second preset-state slice for archive-only filters, reuse the existing preset helper to populate `snapshotFromLocal` / `snapshotToLocal`, and render the same preset family ahead of the archive datetime inputs. Manual archive datetime edits, time-related chip clearing, and full archive reset should all clear the active preset highlight.

## Frontend Design

In `web/src/pages/Terminals.tsx`:

- add archive-only preset state separate from the existing timeline preset state
- render a `Preset Ranges` block in the archive summary filter area
- on preset click:
  - update `archiveFilters.snapshotFromLocal`
  - update `archiveFilters.snapshotToLocal`
  - set the archive active preset id
- on manual archive datetime input edits:
  - keep the new datetime value
  - clear the archive active preset id
- on `Clear Archive Filters`:
  - reset archive filters to defaults
  - clear the archive active preset id
- on per-chip clear:
  - keep current non-time chip behavior
  - if clearing `snapshotFromLocal` or `snapshotToLocal`, also clear the archive active preset id

## Error Handling

- preserve the current page-level `actionKey` / `actionError` / `actionNotice` model
- preset clicks should not trigger network requests
- preset clicks should not emit success/failure notices
- keep export/download wording unchanged

## Testing Strategy

Frontend RED signal:

- create a small build-breaking reference to a not-yet-defined archive preset state/value or handler

Frontend verification:

- `cd web && npm run lint`
- `cd web && npm run build`

Regression verification:

- `.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Risks And Mitigations

- Risk: archive preset state accidentally interferes with the existing timeline preset state.
  - Mitigation: keep separate state and separate update helpers for archive vs timeline filters.
- Risk: archive preset highlight becomes stale after manual datetime edits.
  - Mitigation: clear archive preset state whenever archive datetime inputs or time-related chip clears diverge from the preset.
- Risk: the new buttons imply changed backend semantics.
  - Mitigation: reuse the exact same local-datetime helper and query conversion already used by the existing archive time filters.

## Rollout

Frontend-only operator-surface improvement. No migration, no API changes, and no behavior change outside the top-level archive filter UX on `/terminals`.
