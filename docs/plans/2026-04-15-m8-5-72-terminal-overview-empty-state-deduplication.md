# M8.5.72 Terminal Overview Empty-State Deduplication Implementation Plan

**Goal:** Remove duplicate empty-state messaging from the `/terminals` overview so operators see one clear empty-state message when no canonical workspaces exist.

**Architecture:** Keep the change frontend-only. Patch the overview empty-state branch in `web/src/pages/Terminals.tsx`, retain the existing in-table empty-state row, and leave all backend routes, API-client contracts, and terminal-history surfaces unchanged.

**Tech Stack:** React 19, TypeScript, Vite, ESLint

---

### Task 1: Record The New Session Scope

**Files:**
- Modify: `tasks/todo.md`
- Create: `docs/plans/2026-04-15-m8-5-72-terminal-overview-empty-state-deduplication-design.md`
- Create: `docs/plans/2026-04-15-m8-5-72-terminal-overview-empty-state-deduplication.md`
- Reference: `docs/progress.md`

**Step 1: Add the new session checklist**

Add a new top section in `tasks/todo.md` for `M8.5.72` with:

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
git add tasks/todo.md docs/plans/2026-04-15-m8-5-72-terminal-overview-empty-state-deduplication-design.md docs/plans/2026-04-15-m8-5-72-terminal-overview-empty-state-deduplication.md
git commit -m "docs(plans): add M8.5.72 terminal overview empty-state dedupe plan"
```

Expected:

- PASS

### Task 2: Create A Small RED Signal

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Introduce a small failing reference**

Reference a not-yet-defined helper/value in the overview empty-state branch.

Example shape:

```tsx
{items.length === 0 ? renderOverviewEmptyStateHint() : null}
```

**Step 2: Run build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new helper/value is not implemented yet

### Task 3: Implement The Overview Empty-State Deduplication

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Write minimal frontend implementation**

Implement:

- remove the redundant standalone overview empty-state paragraph
- keep the existing in-table empty-state row intact

Keep unchanged:

- overview table headers, rows, and actions
- archive/timeline/search/detail behavior
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

- `docs/progress.md` with `M8.5.72` scope and verification evidence
- `tasks/todo.md` review section with the exact empty-state deduplication
- `AGENTS.md` if the current terminal baseline summary should mention the cleanup

**Step 4: Commit**

Run:

```bash
git add web/src/pages/Terminals.tsx docs/progress.md tasks/todo.md AGENTS.md
git commit -m "fix(web): dedupe M8.5.72 overview empty state"
```

Expected:

- PASS
