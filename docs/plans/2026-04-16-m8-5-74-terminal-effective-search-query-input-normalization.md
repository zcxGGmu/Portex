# M8.5.74 Terminal Effective Search Query Input Normalization Implementation Plan

**Goal:** Normalize the `/terminals` search input to the same trimmed effective query value that the page already uses for search requests, query summary copy, detail highlighting, and export actions.

**Architecture:** Keep the change frontend-only. Patch the submit path in `web/src/pages/Terminals.tsx`, align the controlled input with the existing trimmed effective query, and leave backend routes, services, OpenAPI, and search contracts unchanged.

**Tech Stack:** React 19, TypeScript, Vite, ESLint

---

### Task 1: Record The New Session Scope

**Files:**
- Modify: `tasks/todo.md`
- Create: `docs/plans/2026-04-16-m8-5-74-terminal-effective-search-query-input-normalization-design.md`
- Create: `docs/plans/2026-04-16-m8-5-74-terminal-effective-search-query-input-normalization.md`
- Reference: `docs/progress.md`

**Step 1: Add the new session checklist**

Add a new top section in `tasks/todo.md` for `M8.5.74` with:

- checked items for restart-doc review, scope confirmation, consistency-gap validation, and design/plan creation
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
git add tasks/todo.md docs/plans/2026-04-16-m8-5-74-terminal-effective-search-query-input-normalization-design.md docs/plans/2026-04-16-m8-5-74-terminal-effective-search-query-input-normalization.md
git commit -m "docs(plans): add M8.5.74 terminal search-input normalization plan"
```

Expected:

- PASS

### Task 2: Create A Small RED Signal

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Introduce a small failing reference**

Reference a not-yet-defined helper/value in the search submit path.

Example shape:

```tsx
const effectiveSearchQuery = normalizeSubmittedSearchQuery(searchInput)
```

**Step 2: Run build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new helper/value is not implemented yet

### Task 3: Implement Effective Search Input Normalization

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Write minimal frontend implementation**

Implement:

- one small submit-time normalization step for the search input
- visible input alignment with the same trimmed query already used by the page
- empty-query submit clearing of pending first-match targeting

Keep unchanged:

- backend contracts and API-client query signatures
- search request semantics, ranking, pagination, exports, and highlighting
- archive/timeline/detail scope and action notices

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

- `docs/progress.md` with `M8.5.74` scope and verification evidence
- `tasks/todo.md` review section with the exact search-input normalization
- `AGENTS.md` if the current terminal baseline summary should mention the new frontend consistency fix

**Step 4: Commit**

Run:

```bash
git add web/src/pages/Terminals.tsx docs/progress.md tasks/todo.md AGENTS.md
git commit -m "fix(web): normalize M8.5.74 terminal search input"
```

Expected:

- PASS
