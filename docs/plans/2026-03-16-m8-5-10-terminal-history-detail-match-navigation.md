# M8.5.10 Terminal History Detail Match Navigation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add local previous/next match navigation inside the `/terminals` history detail panel without changing any backend contracts.

**Architecture:** Keep all match-navigation logic in the frontend by deriving match offsets from the active search term and the loaded detail output. Reuse the existing detail panel and search state, then add active-match highlighting and scroll-into-view behavior.

**Tech Stack:** React, TypeScript, existing `/terminals` page state, pytest regression suite, Ruff, npm lint/build

---

### Task 1: Drive Frontend RED For Match Navigation

**Files:**
- Modify: `web/src/pages/Terminals.tsx`
- Reference: `web/src/api/client.ts`
- Reference: `web/src/hooks/useApi.ts`

**Step 1: Create the frontend RED condition**

Update `web/src/pages/Terminals.tsx` to reference the intended match-navigation state and rendering:

- derived match indexes from the current search term and detail output
- `Previous` / `Next` controls
- active match counter
- highlighted detail output segments

Do this before finishing the supporting render/state logic so the frontend build fails for the incomplete implementation.

**Step 2: Run the frontend build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new match-navigation logic is incomplete

**Step 3: Implement the minimal frontend logic**

Implement in `web/src/pages/Terminals.tsx`:

- local match-index derivation from `detailData.output` and the active search term
- `activeMatchIndex` state/reset rules
- segmented output rendering with base and active highlights
- `Previous` / `Next` actions and `Match N / M` display
- scroll-to-active-match behavior

Avoid backend changes. Only add CSS in `web/src/index.css` if the existing styles cannot support readable highlighting.

**Step 4: Re-run frontend checks to verify GREEN**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected:

- PASS for both lint and build

**Step 5: Commit**

```bash
git add web/src/pages/Terminals.tsx web/src/index.css
git commit -m "feat(web): add terminal detail match navigation"
```

### Task 2: Run Focused Regression And Full Verification

**Files:**
- No intentional production-file changes beyond Task 1 unless a regression fix is required

**Step 1: Run focused terminal regression**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS for the terminal-focused suite, proving the frontend-only change did not break backend contracts

**Step 2: Run full repo verification**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- PASS on backend tests, Ruff, frontend lint/build, and diff hygiene

**Step 3: Commit any required regression-only fix**

If verification exposed a real issue that required code changes, commit that fix separately with a narrow message. If no fix was needed, skip this step.

### Task 3: Sync Handoff Docs

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`
- Modify: `tasks/todo.md`

**Step 1: Update restart-oriented docs**

Record:

- `M8.5.10` scope and completion state
- fresh verification evidence
- immediate next step after local match navigation

Keep `docs/progress.md` concise and restart-oriented.

**Step 2: Commit handoff docs**

Run:

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync M8.5.10 terminal detail navigation context"
```
