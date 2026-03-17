# M8.5.14 Terminal Time-Range Filters Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add inclusive `snapshot_from` / `snapshot_to` filters to terminal history timeline and search, and expose matching local minute-granularity controls on `/terminals`.

**Architecture:** Extend the shared terminal snapshot filtering path to support additive time bounds on `snapshot_at`, expose the same UTC wire-format params on timeline and search routes, then reuse the existing `/terminals` filter state with `datetime-local` inputs that convert browser-local values to UTC request params.

**Tech Stack:** Python, FastAPI, Pydantic, React, TypeScript, pytest, Ruff, npm lint/build

---

### Task 1: Add Failing Backend Time-Range Filter Tests

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `services/terminal_sessions.py`
- Reference: `app/routes/terminals.py`

**Step 1: Write the failing test**

Cover:

- timeline filtering by inclusive `snapshot_from`
- timeline/search filtering by inclusive `snapshot_to`
- bounded `snapshot_from + snapshot_to`
- invalid range (`snapshot_from > snapshot_to`) rejected
- route parameter pass-through for both timeline and search
- OpenAPI exposure of `snapshot_from` and `snapshot_to` on both routes

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because time-range filters are not implemented yet

**Step 3: Write minimal implementation**

Implement:

- additive `snapshot_from` / `snapshot_to` parameters in `TerminalSessionService`
- shared snapshot time filtering on `snapshot_at`
- invalid-range `ValueError`
- additive route query parameters on both timeline and search

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS on backend time-range coverage

**Step 5: Commit**

```bash
git add tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py services/terminal_sessions.py app/routes/terminals.py
git commit -m "feat(terminal): add M8.5.14 backend time-range filters"
```

### Task 2: Add Frontend Time-Range Filter Controls

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Write the failing frontend contract usage**

Reference the intended contract first:

- timeline and search request options include `snapshotFrom` and `snapshotTo`
- query keys include the two time-range values
- `/terminals` filter state includes local `from` / `to` strings
- filter changes reset stale search/detail state

**Step 2: Run test to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new frontend filter fields are not wired yet

**Step 3: Write minimal implementation**

Implement:

- additive request option types in `web/src/api/client.ts`
- additive query key/request params in `web/src/hooks/useApi.ts`
- `datetime-local` filter controls plus local-to-UTC conversion helpers in `web/src/pages/Terminals.tsx`
- state reset behavior on time-filter changes

**Step 4: Run test to verify it passes**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected:

- PASS for lint and build

**Step 5: Commit**

```bash
git add web/src/api/client.ts web/src/hooks/useApi.ts web/src/pages/Terminals.tsx
git commit -m "feat(web): add M8.5.14 time-range filter controls"
```

### Task 3: Verification And Handoff Sync

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Modify: `AGENTS.md`

**Step 1: Run focused terminal regression**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS for the terminal-focused suite

**Step 2: Run full repository verification**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- PASS on tests, lint/build, and diff hygiene

**Step 3: Update restart-oriented docs**

Record:

- `M8.5.14` scope, verification evidence, and the next post-`M8.5.14` refinement suggestion

**Step 4: Commit milestone**

Commit message:

```bash
git commit -m "feat(terminal): complete M8.5.14 time-range filters"
```
