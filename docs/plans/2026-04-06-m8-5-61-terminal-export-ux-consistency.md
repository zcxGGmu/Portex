# M8.5.61 Terminal Export UX Consistency Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the existing `/terminals` export and download actions read and behave consistently without changing any backend contract or terminal-history behavior.

**Architecture:** Keep the current distributed export surface in place, but refactor `web/src/pages/Terminals.tsx` so all export/download actions share one local browser-download helper and one consistent success/error handling pattern. Treat this as a frontend-only consistency pass; backend routes, schemas, and filenames stay unchanged.

**Tech Stack:** React 19, TypeScript, Vite, ESLint, FastAPI route regression via pytest

---

### Task 1: Record The Session Start And Lock The Scope

**Files:**
- Modify: `tasks/todo.md`
- Create: `docs/plans/2026-04-06-m8-5-61-terminal-export-ux-consistency-design.md`
- Create: `docs/plans/2026-04-06-m8-5-61-terminal-export-ux-consistency.md`
- Reference: `docs/progress.md`
- Reference: `web/src/pages/Terminals.tsx`

**Step 1: Add the new session checklist**

Add a new top section to `tasks/todo.md` for `M8.5.61` with unchecked implementation and verification items, plus checked items for re-reading restart docs and writing the design/plan docs.

**Step 2: Sanity-check the docs**

Run:

```bash
git diff --check
```

Expected:

- PASS with no whitespace issues in the new planning docs

**Step 3: Commit the planning docs**

Run:

```bash
git add tasks/todo.md docs/plans/2026-04-06-m8-5-61-terminal-export-ux-consistency-design.md docs/plans/2026-04-06-m8-5-61-terminal-export-ux-consistency.md
git commit -m "docs(plans): add M8.5.61 terminal export UX consistency plan"
```

Expected:

- PASS and the worktree is ready for implementation

### Task 2: Create A Small RED Signal For The Refactor

**Files:**
- Modify: `web/src/pages/Terminals.tsx`
- Reference: `web/src/api/client.ts`

**Step 1: Write the failing change**

Change one existing export handler in `web/src/pages/Terminals.tsx` to call a new shared helper before that helper exists yet.

Example shape:

```tsx
await runTerminalDownloadAction({
  actionKey: key,
  request: () => apiClient.downloadTerminalOverview(token),
  fileName: buildTerminalOverviewExportFileName(),
  successMessage: `Exported terminal overview for ${items.length.toLocaleString()} workspaces.`,
  failureMessage: 'Failed to export terminal overview.',
})
```

**Step 2: Run build to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the shared helper is referenced but not defined

**Step 3: Write minimal implementation**

Add one page-local helper that:

- clears stale action notice/error state
- sets `actionKey`
- awaits a blob request callback
- triggers the browser download with the provided filename
- sets success or fallback error copy
- always clears `actionKey` in `finally`

**Step 4: Run build to verify it passes**

Run:

```bash
cd web && npm run build
```

Expected:

- PASS

### Task 3: Move All Export And Download Actions Onto The Shared Pattern

**Files:**
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Write the failing refactor**

Switch the remaining export/download handlers to the shared helper and reorder one action group before the helper callsites are fully aligned.

Focus only on:

- overview export actions
- timeline export actions
- search export actions
- detail download actions

**Step 2: Run lint to verify the intermediate state is not clean yet**

Run:

```bash
cd web && npm run lint
```

Expected:

- FAIL or report issues until all callsites and local variables are aligned with the new helper usage

**Step 3: Write minimal implementation**

Complete the consistency pass:

- order overview buttons as `Overview` -> `Latest Histories` -> `History Archive`
- order timeline buttons as `Current Page` -> `Archive`
- order search buttons as `Search Page` -> `Search Archive`
- keep detail as `Download Output` -> `Download JSON`
- normalize success and fallback failure copy across all handlers
- do not change any filename builder or API client method

**Step 4: Run lint and build to verify it passes**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected:

- PASS

### Task 4: Run Regression Checks And Sync Restart Docs

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Optional: `AGENTS.md`
- Reference: `tests/app/routes/test_terminal_routes.py`
- Reference: `tests/app/routes/test_api_routes.py`

**Step 1: Run focused route regression**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS, proving the frontend-only cleanup did not require route-contract updates

**Step 2: Run final hygiene checks**

Run:

```bash
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- PASS

**Step 3: Update restart docs**

Refresh:

- `docs/progress.md` with the new `M8.5.61` scope and verification evidence
- `tasks/todo.md` review section with implementation notes
- `AGENTS.md` only if the terminal operator-surface summary should explicitly mention the UX consistency pass

**Step 4: Commit**

Run:

```bash
git add web/src/pages/Terminals.tsx docs/progress.md tasks/todo.md AGENTS.md
git commit -m "feat(web): add M8.5.61 terminal export UX consistency"
```

Expected:

- PASS with the completed milestone captured in git history
