# M7.4.3 Memory Management Surface Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add authenticated APIs and a dedicated `/memory` page for user-global memory and workspace markdown memory management on top of the current file-backed `MemoryService`.

**Architecture:** Extend `MemoryService` only enough to manage workspace markdown memory files under `data/memory/{group_folder}`, add a dedicated `/memory` route family for global memory plus workspace-scoped memory operations, and expose a standalone `/memory` web page with separate global-memory and workspace-memory editors.

**Tech Stack:** FastAPI, Pydantic v2, Python filesystem I/O, React, TypeScript, Vite

---

### Task 1: Add The Failing Backend Tests For Memory Service And Memory Routes

**Files:**
- Modify: `tests/services/test_memory_service.py`
- Create: `tests/app/routes/test_memory_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`

**Step 1: Write the failing tests**

Cover:

- listing workspace markdown memory files
- reading missing-but-valid workspace memory files as empty content
- writing workspace markdown memory files
- traversal, symlink, and extension guards
- `GET/PUT /memory/global`
- workspace memory route auth/access behavior
- OpenAPI route/schema coverage

**Step 2: Run the focused tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/services/test_memory_service.py tests/app/routes/test_memory_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: FAIL because the new memory service methods and memory routes do not exist yet.

**Step 3: Commit red tests only if useful for review**

```bash
git add tests/services/test_memory_service.py tests/app/routes/test_memory_routes.py tests/app/routes/test_api_routes.py
git commit -m "test(memory): add M7.4.3 coverage"
```

### Task 2: Implement Backend Memory APIs On Top Of `MemoryService`

**Files:**
- Modify: `services/memory.py`
- Create: `app/routes/memory.py`
- Modify: `app/main.py`
- Modify: `app/routes/__init__.py`
- Modify: `app/openapi.py`
- Modify: `domain/schemas.py`

**Step 1: Run the smallest failing backend subset**

Run:

```bash
.venv/bin/pytest tests/services/test_memory_service.py tests/app/routes/test_memory_routes.py -q
```

Expected: FAIL because service methods, DTOs, and routes are missing.

**Step 2: Write the minimal implementation**

Implement:

- workspace markdown memory list/read/write helpers in `MemoryService`
- safe path handling under `data/memory/{group_folder}`
- `/memory/global`
- `/memory/workspaces/{group_id}/files`
- `/memory/workspaces/{group_id}/file`
- `/memory/workspaces/{group_id}/search`
- OpenAPI docs and DTOs

Keep search path-only and keep workspace access based on existing workspace visibility.

**Step 3: Run focused backend tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/services/test_memory_service.py tests/app/routes/test_memory_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: PASS

**Step 4: Commit**

```bash
git add services/memory.py app/routes/memory.py app/main.py app/routes/__init__.py app/openapi.py domain/schemas.py tests/services/test_memory_service.py tests/app/routes/test_memory_routes.py tests/app/routes/test_api_routes.py
git commit -m "feat(memory): add memory management APIs"
```

### Task 3: Add The Frontend `/memory` Page And API Wiring

**Files:**
- Modify: `web/src/App.tsx`
- Modify: `web/src/components/layout/AppLayout.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Create: `web/src/pages/Memory.tsx`
- Modify: `web/src/index.css`

**Step 1: Run frontend verification to expose missing wiring**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected: FAIL once the new page references missing client methods, hooks, or types.

**Step 2: Write the minimal implementation**

Implement:

- memory API client methods
- query/mutation hooks for global and workspace memory
- `/memory` protected route
- nav entry
- page with global memory editor, workspace selector, workspace file list, search, `Today` shortcut, and note editor

Do not add markdown rendering or settings-page integration.

**Step 3: Run frontend verification again**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected: PASS

**Step 4: Commit**

```bash
git add web/src/App.tsx web/src/components/layout/AppLayout.tsx web/src/api/client.ts web/src/hooks/useApi.ts web/src/pages/Memory.tsx web/src/index.css
git commit -m "feat(web): add memory page"
```

### Task 4: Run Full Verification And Refresh Handoff

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run focused slice verification**

Run:

```bash
.venv/bin/pytest tests/services/test_memory_service.py tests/app/routes/test_memory_routes.py tests/app/routes/test_api_routes.py -q
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

- `M7.4.3` marked complete
- exact verification commands
- next entrypoint set to `M7.4.4`

**Step 5: Commit**

```bash
git add docs/progress.md
git commit -m "docs(progress): record M7.4.3 completion"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-4-3-memory-surface.md`. Given you asked to pause, I will stop here after saving and committing the planning docs.
