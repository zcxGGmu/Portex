# M7.4.1 Monitor And Status Surface Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a minimal read-only operator monitor surface with one aggregated monitor API and one protected `/monitor` page for queue state, recent runs, and backend/runtime health.

**Architecture:** Extend `ExecutionCoordinator` with explicit read-side helpers for queue and recent-run summaries, add a dedicated `monitor` HTTP route that aggregates coordinator state plus best-effort backend health, and add a simple polling `/monitor` web page wired into the existing app layout for operator roles only.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy-backed route dependencies, React, TypeScript, Vite

---

### Task 1: Add The Failing Backend Tests For Coordinator Monitor Reads And `/monitor`

**Files:**
- Modify: `tests/services/test_execution_coordinator.py`
- Create: `tests/app/routes/test_monitor_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`

**Step 1: Write the failing tests**

Add coverage for:

- queue snapshot summaries by workspace
- recent run summary ordering and limit
- `GET /monitor` authentication and role gating
- idle monitor payload shape
- backend-health partial failure tolerance
- OpenAPI route/tag/schema presence

**Step 2: Run the focused tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_monitor_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: FAIL because there is no monitor route and the coordinator has no monitor read helpers.

**Step 3: Commit red tests only if the session flow wants them isolated**

```bash
git add tests/services/test_execution_coordinator.py tests/app/routes/test_monitor_routes.py tests/app/routes/test_api_routes.py
git commit -m "test(monitor): add M7.4.1 backend coverage"
```

### Task 2: Implement Backend Monitor Aggregation

**Files:**
- Modify: `services/execution_coordinator.py`
- Create: `app/routes/monitor.py`
- Modify: `app/main.py`
- Modify: `app/routes/__init__.py`
- Modify: `app/openapi.py`
- Modify: `domain/schemas.py`
- Modify: `services/execution_runtime.py`

**Step 1: Run the smallest failing backend subset**

Run:

```bash
.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_monitor_routes.py -q
```

Expected: FAIL on missing coordinator helpers, schemas, and route wiring.

**Step 2: Write the minimal implementation**

Implement:

- coordinator queue snapshot helper
- coordinator recent-run listing helper
- monitor response DTOs
- best-effort backend health probe wiring
- `GET /monitor`
- monitor router registration and OpenAPI tag

Keep the route read-only and tolerant of backend probe failures.

**Step 3: Run focused backend tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_monitor_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: PASS

**Step 4: Commit**

```bash
git add services/execution_coordinator.py app/routes/monitor.py app/main.py app/routes/__init__.py app/openapi.py domain/schemas.py services/execution_runtime.py tests/services/test_execution_coordinator.py tests/app/routes/test_monitor_routes.py tests/app/routes/test_api_routes.py
git commit -m "feat(monitor): add monitor aggregation API"
```

### Task 3: Add The Frontend Monitor Page And Route Wiring

**Files:**
- Modify: `web/src/App.tsx`
- Modify: `web/src/components/layout/AppLayout.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Create: `web/src/pages/Monitor.tsx`

**Step 1: Add the failing frontend-facing wiring**

Write the minimum frontend code changes needed so:

- `/monitor` becomes a protected route
- the nav shows `Monitor` for `owner/admin`
- the page polls `GET /monitor`
- forbidden and error states are explicit

If the repo has no frontend unit-test harness for this slice, rely on lint/build verification after implementation instead of creating a new test framework now.

**Step 2: Run frontend verification to expose wiring errors**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected: FAIL until the new page, types, and hooks are wired correctly.

**Step 3: Write the minimal implementation**

Implement:

- typed monitor response client call
- query hook with 5-second polling
- `/monitor` page using existing `AppLayout`
- nav visibility based on current user role

Keep the UI intentionally plain and operator-focused.

**Step 4: Run frontend verification again**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected: PASS

**Step 5: Commit**

```bash
git add web/src/App.tsx web/src/components/layout/AppLayout.tsx web/src/api/client.ts web/src/hooks/useApi.ts web/src/pages/Monitor.tsx
git commit -m "feat(web): add monitor page"
```

### Task 4: Run Full Verification And Refresh Handoff

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run focused full-slice verification**

Run:

```bash
.venv/bin/pytest tests/services/test_execution_coordinator.py tests/app/routes/test_monitor_routes.py tests/app/routes/test_api_routes.py -q
cd web && npm run lint
cd web && npm run build
```

Expected: PASS

**Step 2: Run broader backend regression**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
```

Expected: PASS

**Step 3: Run repo hygiene**

Run:

```bash
.venv/bin/ruff check .
git diff --check
```

Expected: PASS

**Step 4: Update restart docs**

Refresh `docs/progress.md` with:

- `M7.4.1` marked complete
- exact verification commands
- next entrypoint set to `M7.4.2`

**Step 5: Commit**

```bash
git add docs/progress.md
git commit -m "docs(progress): record M7.4.1 completion"
```

Plan complete and saved to `docs/plans/2026-03-14-m7-4-1-monitor-surface.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Given you asked to continue in this session, I’ll take option 1 unless you want to switch.
