# M8.5.69 Terminal Archive Time-Range Presets Implementation Plan

**Goal:** Add archive-only preset time-range shortcuts on `/terminals` so operators can quickly apply recent-window archive filters without manually entering both datetime bounds.

**Architecture:** Keep the change frontend-only. Reuse the existing preset helper in `web/src/pages/Terminals.tsx`, add archive-specific preset state, render the standard preset family in the top-level archive filter area, and keep all backend routes, API-client contracts, and workspace-scoped history surfaces unchanged.

**Tech Stack:** React 19, TypeScript, Vite, ESLint

---

### Task 1: Record The New Session Scope

**Files:**
- Modify: `tasks/todo.md`
- Create: `docs/plans/2026-04-14-m8-5-69-terminal-archive-time-range-presets-design.md`
- Create: `docs/plans/2026-04-14-m8-5-69-terminal-archive-time-range-presets.md`
- Reference: `docs/progress.md`

**Step 1: Add the new session checklist**

Add a new top section in `tasks/todo.md` for `M8.5.69` with:

- checked items for restart-doc review, scope confirmation, UX-gap validation, and design/plan creation
- unchecked items for RED, implementation, verification, docs sync, and commit

**Step 2: Sanity-check the planning docs**

Run:

```bash
git diff --check
```

Expected:

- PASS with no whitespace issues

**Step 3: Commit the planning docs**

Run:

```bash
git add tasks/todo.md docs/plans/2026-04-14-m8-5-69-terminal-archive-time-range-presets-design.md docs/plans/2026-04-14-m8-5-69-terminal-archive-time-range-presets.md
git commit -m "docs(plans): add M8.5.69 terminal archive time-range presets plan"
```

Expected:

- PASS

### Task 2: Create A Small RED Signal

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Introduce a small failing reference**

Reference a not-yet-defined archive preset state or handler from the archive summary panel.

Example shape:

```tsx
className={archiveActivePresetId === preset.id ? '' : 'button--ghost'}
```

**Step 2: Run build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new archive preset state/handler is not implemented yet

### Task 3: Implement The Archive Preset Controls

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Write minimal frontend implementation**

Implement:

- archive-only preset range buttons
- archive-only active preset state
- archive filter update/reset behavior that clears preset state when archive datetime inputs stop matching the chosen preset

Keep unchanged:

- existing archive-only fields
- existing archive chips and summary text
- existing bulk `Clear Archive Filters` action semantics
- existing export handlers
- timeline/search/detail state
- backend contracts and API-client query wiring

**Step 2: Run lint and build to verify GREEN**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected:

- PASS

### Task 4: Run Regression Checks, Sync Restart Docs, And Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Optional: `AGENTS.md`

**Step 1: Run focused regression**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

**Step 2: Run hygiene checks**

Run:

```bash
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- PASS

**Step 3: Update restart-oriented docs**

Refresh:

- `docs/progress.md` with `M8.5.69` scope and verification evidence
- `tasks/todo.md` review section with exact preset UX notes
- `AGENTS.md` if the current terminal operator-surface summary should mention archive preset shortcuts

**Step 4: Commit**

Run:

```bash
git add web/src/pages/Terminals.tsx docs/progress.md tasks/todo.md AGENTS.md
git commit -m "feat(web): add M8.5.69 archive time-range presets"
```

Expected:

- PASS
