# M8.5.15 Terminal Preset Time Ranges Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `1h` / `6h` / `24h` / `7d` / `30d` preset time-range controls to `/terminals` so operators can apply common history windows with one click while preserving the current `snapshot_from` / `snapshot_to` API contract.

**Architecture:** Keep the change frontend-only. Extend the existing `/terminals` filter state with a derived active-preset key, add small deterministic time helpers inside the page module, and have preset clicks write directly into the existing `snapshotFromLocal` / `snapshotToLocal` values so timeline and search continue to share one request path. Preserve current backend routes, terminal-history persistence, and RBAC behavior unchanged.

**Tech Stack:** React 19, TypeScript, Vite, ESLint, existing terminal history API/hooks

---

### Task 1: Add the Failing Preset-Range Frontend Contract

**Files:**
- Modify: `web/src/pages/Terminals.tsx`
- Reference: `web/src/api/client.ts`
- Reference: `web/src/hooks/useApi.ts`

**Step 1: Write the failing contract**

In `web/src/pages/Terminals.tsx`, introduce the intended preset UI/data-shape references before implementation:

- a fixed preset list for `1h`, `6h`, `24h`, `7d`, `30d`
- a new active preset state value
- render a preset button row in the history filter area
- wire button clicks to a not-yet-implemented preset apply helper

Example target shape:

```tsx
const TERMINAL_TIME_RANGE_PRESETS = [
  { key: '1h', label: '1h', minutes: 60 },
  { key: '6h', label: '6h', minutes: 360 },
]

const [activePreset, setActivePreset] = useState<TerminalTimePreset | null>(null)

<button onClick={() => applyTimePreset('24h')} type="button">
  24h
</button>
```

The file should now reference helpers/types that do not exist yet so the build fails for the right reason.

**Step 2: Run test to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because preset helpers/state wiring are referenced but not fully implemented yet

**Step 3: Write minimal implementation**

Implement the missing pieces in `web/src/pages/Terminals.tsx`:

- preset key/type definitions
- deterministic helper(s) to format browser-local `datetime-local` strings
- helper to derive `from` / `to` local values from a preset and a `Date`
- active preset detection based on current `snapshotFromLocal` / `snapshotToLocal`
- preset row UI with selected styling
- preset click handler that:
  - overwrites `snapshotFromLocal` / `snapshotToLocal`
  - resets `timelineOffset`
  - resets `searchOffset`
  - clears `pendingSearchPageMove`
  - clears `detailSessionId`
  - clears `pendingMatchTarget`
- manual `Snapshot From` / `Snapshot To` edits clear the active preset when the values no longer exactly match a preset-derived range

Keep these unchanged:

- `useTerminalHistoryTimelineQuery(...)`
- `useTerminalHistorySearchQuery(...)`
- backend request parameter names
- workspace-switch reset behavior
- `Clear` search button semantics

**Step 4: Run test to verify it passes**

Run:

```bash
cd web && npm run build
```

Expected:

- PASS with the preset UI compiling cleanly against the current terminal history API/hooks

**Step 5: Commit**

```bash
git add web/src/pages/Terminals.tsx
git commit -m "feat(web): add M8.5.15 terminal preset time ranges"
```

### Task 2: Verify Lint And Terminal Regression Compatibility

**Files:**
- Verify only: `web/src/pages/Terminals.tsx`
- Verify only: `web/src/api/client.ts`
- Verify only: `web/src/hooks/useApi.ts`

**Step 1: Run frontend verification**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected:

- PASS on lint and build

**Step 2: Run focused terminal regression**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS to confirm the frontend-only preset change did not regress current terminal route contracts or overview behavior

**Step 3: Run hygiene verification**

Run:

```bash
.venv/bin/ruff check .
git diff --check
```

Expected:

- PASS with no formatting or lint regressions

### Task 3: Sync Restart-Oriented Docs

**Files:**
- Modify: `docs/progress.md`

**Step 1: Update progress context**

Record:

- `M8.5.15` scope as frontend-only preset time ranges
- verification evidence (`pytest`, `ruff`, `npm run lint`, `npm run build`, `git diff --check`)
- the next suggested post-`M8.5.15` refinement entry

Update these sections:

- current phase / latest completed milestone bullets
- recent completion summary
- `下一位 Codex 直接执行`
- one-line restart summary

**Step 2: Commit handoff sync**

Run:

```bash
git add docs/progress.md
git commit -m "docs(handoff): sync M8.5.15 preset time-range context"
```

### Task 4: Optional Final Milestone Squash Commit

**Files:**
- Verify only: working tree

**Step 1: Check whether milestone commits are already cleanly split**

If the feature commit and handoff commit already exist and are clean, do nothing.

**Step 2: Do not amend by default**

Per repo rules, do not rewrite or amend commits unless explicitly requested.
