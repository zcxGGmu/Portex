# M8.5.8 Terminal History Filters/Detail Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add server-side terminal-history timeline filters plus per-session history detail, while keeping `latest.json` and `/sessions/current/history` compatibility unchanged.

**Architecture:** Extend the existing merged terminal-history read model in `TerminalSessionService` so timeline list and detail lookup share the same dedupe logic. Expose the new filter/detail surface through additive FastAPI route/schema changes, then upgrade `/terminals` with in-page filter controls and a lazy detail panel.

**Tech Stack:** Python, FastAPI, Pydantic, React, TypeScript, pytest, Ruff, npm build/lint

---

### Task 1: Write Failing Service Tests For Timeline Filters And Detail

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Reference: `services/terminal_sessions.py`

**Step 1: Write the failing tests**

Add focused tests for:

- filtered timeline by `status`
- filtered timeline by `owner_user_id`
- filtered timeline by `session_id_prefix`
- filtered pagination after applying filters
- detail lookup from archived snapshot
- detail lookup from `latest.json`
- detail lookup from in-memory active snapshot
- detail lookup missing session raises `TerminalSessionNotFoundError`

**Step 2: Run the focused service tests to verify RED**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- FAIL on the new tests because filter/detail APIs or fields are missing

**Step 3: Write the minimal service implementation**

Implement in `services/terminal_sessions.py`:

- additive filter parameters on `list_history_timeline_by_group(...)`
- shared merged snapshot helper if needed
- `get_history_snapshot_by_group(group_folder, session_id)`
- additive summary/detail data objects needed by the service layer

**Step 4: Re-run the focused service tests to verify GREEN**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- PASS on the newly added service coverage

**Step 5: Commit**

```bash
git add tests/services/test_terminal_sessions.py services/terminal_sessions.py
git commit -m "feat(terminal): add history filters and detail service model"
```

### Task 2: Write Failing Route And OpenAPI Tests For Filter/Detail Surface

**Files:**
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `app/routes/terminals.py`
- Reference: `domain/schemas.py`

**Step 1: Write the failing route/OpenAPI tests**

Add tests for:

- timeline route passes `status`, `owner_user_id`, and `session_id_prefix`
- detail route success response
- detail route `404` mapping when session history is missing
- OpenAPI path for `GET /terminals/{group_id}/sessions/history/{session_id}`
- OpenAPI parameter/schema coverage for timeline filters and detail response

**Step 2: Run the route/OpenAPI tests to verify RED**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because route parameters, path, or schemas do not exist yet

**Step 3: Write the minimal route/schema implementation**

Implement in `domain/schemas.py` and `app/routes/terminals.py`:

- additive `snapshot_at` on timeline summary response
- `TerminalSessionHistoryDetailResponse`
- timeline filter query params
- detail route mapping to the new service method

**Step 4: Re-run the route/OpenAPI tests to verify GREEN**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS on the new route and schema coverage

**Step 5: Commit**

```bash
git add tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py domain/schemas.py app/routes/terminals.py
git commit -m "feat(api): add terminal history filters and detail routes"
```

### Task 3: Upgrade `/terminals` With Filter Controls And In-Page Detail

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/pages/Terminals.tsx`
- Reference: `web/src/index.css`

**Step 1: Create the frontend RED condition**

Update `web/src/pages/Terminals.tsx` to reference the intended new API shape:

- timeline filters in component state
- `snapshot_at` field on timeline items
- detail query state and detail rendering

Do this before adding the matching client/hook support so the frontend build fails for the missing contract.

**Step 2: Run the frontend build to verify RED**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new API client types/helpers/hooks are not implemented yet

**Step 3: Write the minimal frontend implementation**

Implement:

- timeline filter options in `web/src/api/client.ts`
- detail response type and fetch helper in `web/src/api/client.ts`
- timeline/detail hooks in `web/src/hooks/useApi.ts`
- filter controls, `snapshot_at` column, and lazy detail panel in `web/src/pages/Terminals.tsx`
- only add CSS in `web/src/index.css` if the page becomes unreadable without it

**Step 4: Re-run the frontend checks to verify GREEN**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected:

- PASS for both lint and build

**Step 5: Commit**

```bash
git add web/src/api/client.ts web/src/hooks/useApi.ts web/src/pages/Terminals.tsx web/src/index.css
git commit -m "feat(web): add terminal history filters and detail panel"
```

### Task 4: Full Verification, Handoff Docs, And Final Milestone Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`
- Modify: `tasks/todo.md`

**Step 1: Run focused terminal regression**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS for the terminal-focused regression suite

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

- PASS on tests, lint, build, and diff hygiene

**Step 3: Update restart-oriented docs**

Record:

- `M8.5.8` scope and completion state
- fresh verification evidence
- immediate next step after filters/detail

Keep `docs/progress.md` concise and restart-oriented.

**Step 4: Commit the milestone**

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync M8.5.8 terminal history filters/detail context"
```
