# M8.5.68 Terminal Archive Filter Chips UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add archive-only active-filter chips on `/terminals` so operators can see which top-level archive filters are active and clear them individually without manually scanning the whole filter form.

**Architecture:** Keep the change frontend-only. Derive a small chip list from the existing archive-only filter state in `web/src/pages/Terminals.tsx`, render the chips in the summary area, and wire each chip to reset only its own field. Leave all backend routes, API client contracts, and workspace-scoped history surfaces unchanged.

**Tech Stack:** React 19, TypeScript, Vite, ESLint

---

### Task 1: Record The New Session Scope

**Files:**
- Modify: `tasks/todo.md`
- Create: `docs/plans/2026-04-12-m8-5-68-terminal-archive-filter-chips-ux-design.md`
- Create: `docs/plans/2026-04-12-m8-5-68-terminal-archive-filter-chips-ux.md`
- Reference: `docs/progress.md`

**Step 1: Add the new session checklist**

Add a new top section in `tasks/todo.md` for `M8.5.68` with:

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
git add tasks/todo.md docs/plans/2026-04-12-m8-5-68-terminal-archive-filter-chips-ux-design.md docs/plans/2026-04-12-m8-5-68-terminal-archive-filter-chips-ux.md
git commit -m "docs(plans): add M8.5.68 terminal archive filter chips UX plan"
```

Expected:

- PASS

### Task 2: Create A Small RED Signal

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Introduce a small failing reference**

Reference a not-yet-defined archive chip list or renderer from the summary panel.

Example shape:

```tsx
{archiveFilterChips.map((chip) => (
  <span key={chip.key}>{chip.label}</span>
))}
```

**Step 2: Run build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new helper/value is not implemented yet

### Task 3: Implement The Archive Filter Chips

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Write minimal frontend implementation**

Implement:

- archive-only active-filter chip derivation
- readable chip labels/values
- per-chip clear actions that reset only one archive field at a time

Keep unchanged:

- existing archive-only fields
- existing archive summary text
- existing bulk `Clear Archive Filters` action
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

- `docs/progress.md` with `M8.5.68` scope and verification evidence
- `tasks/todo.md` review section with exact UX notes
- `AGENTS.md` if the current terminal operator-surface summary should mention archive filter chips UX

**Step 4: Commit**

Run:

```bash
git add web/src/pages/Terminals.tsx docs/progress.md tasks/todo.md AGENTS.md
git commit -m "feat(web): add M8.5.68 archive filter chips UX"
```

Expected:

- PASS
