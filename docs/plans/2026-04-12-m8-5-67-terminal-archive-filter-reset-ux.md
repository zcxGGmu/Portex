# M8.5.67 Terminal Archive Filter Reset UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a small archive-only reset UX on `/terminals` so operators can quickly tell when the top-level archive export is filtered and can clear all archive filters in one action.

**Architecture:** Keep the change frontend-only. Derive a small active-filter summary from the existing archive-only filter state in `web/src/pages/Terminals.tsx`, add one reset action that restores `DEFAULT_ARCHIVE_FILTERS`, and leave all backend routes, API client contracts, and workspace-scoped history surfaces unchanged.

**Tech Stack:** React 19, TypeScript, Vite, ESLint

---

### Task 1: Record The New Session Scope

**Files:**
- Modify: `tasks/todo.md`
- Create: `docs/plans/2026-04-12-m8-5-67-terminal-archive-filter-reset-ux-design.md`
- Create: `docs/plans/2026-04-12-m8-5-67-terminal-archive-filter-reset-ux.md`
- Reference: `docs/progress.md`

**Step 1: Add the new session checklist**

Add a new top section in `tasks/todo.md` for `M8.5.67` with:

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
git add tasks/todo.md docs/plans/2026-04-12-m8-5-67-terminal-archive-filter-reset-ux-design.md docs/plans/2026-04-12-m8-5-67-terminal-archive-filter-reset-ux.md
git commit -m "docs(plans): add M8.5.67 terminal archive filter reset UX plan"
```

Expected:

- PASS

### Task 2: Create A Small RED Signal

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Introduce a small failing reference**

Reference a not-yet-defined archive reset helper or active-filter summary value from the summary panel.

Example shape:

```tsx
<p className="muted" style={{ marginTop: 0 }}>
  {archiveFilterSummary}
</p>
```

**Step 2: Run build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new helper/value is not implemented yet

### Task 3: Implement The Archive Reset UX

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Write minimal frontend implementation**

Implement:

- archive-only active-filter detection
- short archive-filter summary text
- `Clear Archive Filters` action that resets `archiveFilters` to `DEFAULT_ARCHIVE_FILTERS`
- disabled state when no archive filters are active or another action is running

Keep unchanged:

- existing archive-only fields
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

- `docs/progress.md` with `M8.5.67` scope and verification evidence
- `tasks/todo.md` review section with exact UX notes
- `AGENTS.md` if the current terminal operator-surface summary should mention archive filter reset UX

**Step 4: Commit**

Run:

```bash
git add web/src/pages/Terminals.tsx docs/progress.md tasks/todo.md AGENTS.md
git commit -m "feat(web): add M8.5.67 archive filter reset UX"
```

Expected:

- PASS
