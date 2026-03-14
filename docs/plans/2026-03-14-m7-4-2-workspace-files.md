# M7.4.2 Workspace File Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add safe workspace file-management APIs and a minimal `/files` web page for browsing, uploading, downloading, previewing, editing, and deleting workspace files.

**Architecture:** Introduce one dedicated workspace-file service rooted at `data/groups/{workspace_folder}`, expose workspace-scoped file routes under `/groups/{group_id}`, and add a standalone `/files` page that reuses the existing `/groups` workspace list instead of coupling file management into the current chat shell.

**Tech Stack:** FastAPI, Pydantic v2, Python filesystem I/O, React, TypeScript, Vite

---

### Task 1: Add The Failing Backend Tests For Safe Workspace File Operations

**Files:**
- Create: `tests/services/test_workspace_files.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `tests/app/routes/test_message_routes.py`
- Create: `tests/app/routes/test_file_routes.py`

**Step 1: Write the failing tests**

Cover:

- list files under one workspace root
- reject path traversal and symlink escape
- reject deleting the workspace root
- upload file to a workspace-relative path
- read/write text file content with size/type guards
- preview and download route behavior
- route auth and permission differences between read and write operations
- OpenAPI route/schema coverage

**Step 2: Run the focused tests to verify they fail**

Run:

```bash
.venv/bin/pytest tests/services/test_workspace_files.py tests/app/routes/test_file_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: FAIL because there is no workspace file service or file route family yet.

**Step 3: Commit the red tests only if useful for review**

```bash
git add tests/services/test_workspace_files.py tests/app/routes/test_file_routes.py tests/app/routes/test_api_routes.py
git commit -m "test(files): add M7.4.2 backend coverage"
```

### Task 2: Implement The Backend File Service And Routes

**Files:**
- Create: `services/workspace_files.py`
- Create: `app/routes/files.py`
- Modify: `app/main.py`
- Modify: `app/routes/__init__.py`
- Modify: `app/openapi.py`
- Modify: `domain/schemas.py`

**Step 1: Run the smallest failing backend subset**

Run:

```bash
.venv/bin/pytest tests/services/test_workspace_files.py tests/app/routes/test_file_routes.py -q
```

Expected: FAIL because the service, DTOs, and routes do not exist.

**Step 2: Write the minimal implementation**

Implement:

- safe workspace root resolution
- directory listing
- upload target resolution and file-size guard
- download/preview/content/delete operations
- text extension allowlist and size limits
- read/write permission enforcement via existing workspace access model
- file routes under `/groups/{group_id}`

Keep the first version conservative and avoid rename/create-directory.

**Step 3: Run focused backend tests to verify they pass**

Run:

```bash
.venv/bin/pytest tests/services/test_workspace_files.py tests/app/routes/test_file_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: PASS

**Step 4: Commit**

```bash
git add services/workspace_files.py app/routes/files.py app/main.py app/routes/__init__.py app/openapi.py domain/schemas.py tests/services/test_workspace_files.py tests/app/routes/test_file_routes.py tests/app/routes/test_api_routes.py
git commit -m "feat(files): add workspace file APIs"
```

### Task 3: Add The Frontend Files Page And API Wiring

**Files:**
- Modify: `web/src/App.tsx`
- Modify: `web/src/components/layout/AppLayout.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Create: `web/src/pages/Files.tsx`
- Modify: `web/src/index.css`

**Step 1: Run frontend verification to expose missing wiring**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected: FAIL once the new page references missing client types/hooks or route wiring.

**Step 2: Write the minimal implementation**

Implement:

- typed file-management API client methods
- file list/content queries and upload/delete/save mutations
- `/files` protected route
- app navigation entry
- simple files page with workspace selector, current path navigation, upload, preview, text edit, and delete

Keep the layout intentionally simple and standalone.

**Step 3: Run frontend verification again**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected: PASS

**Step 4: Commit**

```bash
git add web/src/App.tsx web/src/components/layout/AppLayout.tsx web/src/api/client.ts web/src/hooks/useApi.ts web/src/pages/Files.tsx web/src/index.css
git commit -m "feat(web): add files page"
```

### Task 4: Run Full Verification And Refresh Handoff

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run focused slice verification**

Run:

```bash
.venv/bin/pytest tests/services/test_workspace_files.py tests/app/routes/test_file_routes.py tests/app/routes/test_api_routes.py -q
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

- `M7.4.2` marked complete
- exact verification commands
- next entrypoint set to `M7.4.3`

**Step 5: Commit**

```bash
git add docs/progress.md
git commit -m "docs(progress): record M7.4.2 completion"
```

Plan complete and saved to `docs/plans/2026-03-14-m7-4-2-workspace-files.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Given you asked to continue in this session, I’ll take option 1 unless you want to switch.
