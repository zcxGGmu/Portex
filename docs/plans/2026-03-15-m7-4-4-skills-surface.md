# M7.4.4 Skills Management Surface Implementation Plan

**Goal:** Add minimal skills-management APIs and a dedicated `/skills` page backed by `data/skills/{user_id}`.

**Architecture:** Implement a safe filesystem-backed `SkillsService`, expose authenticated `/skills` CRUD/state routes, wire DTO/OpenAPI updates, and add a standalone frontend page with list + editor + state controls.

**Tech Stack:** FastAPI, Pydantic v2, React, TypeScript, Vite

---

### Task 1: Add Red Tests For Skills Service And Skills Routes

**Files:**
- Create: `tests/services/test_skills_service.py`
- Create: `tests/app/routes/test_skills_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`

**Coverage:**
- list/detail/upsert/delete user skill files
- enable/disable state toggling (`SKILL.md` <-> `SKILL.md.disabled`)
- authentication required on all `/skills` routes
- cross-user isolation
- traversal/symlink guards mapped to `400`
- OpenAPI tag/path/schema assertions

**Red test command:**

```bash
.venv/bin/pytest tests/services/test_skills_service.py tests/app/routes/test_skills_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: fail before implementation.

### Task 2: Implement Backend Skills APIs

**Files:**
- Replace: `services/skills.py`
- Create: `app/routes/skills.py`
- Modify: `domain/schemas.py`
- Modify: `app/openapi.py`
- Modify: `app/main.py`
- Modify: `app/routes/__init__.py`

**Implementation:**
- filesystem-safe `SkillsService` with user-local root
- API dependency wiring and error mapping
- `/skills` route family
- `skills` OpenAPI tag + DTOs

**Focused verification:**

```bash
.venv/bin/pytest tests/services/test_skills_service.py tests/app/routes/test_skills_routes.py tests/app/routes/test_api_routes.py -q
```

Expected: pass.

### Task 3: Implement Frontend `/skills` Page

**Files:**
- Create: `web/src/pages/Skills.tsx`
- Modify: `web/src/App.tsx`
- Modify: `web/src/components/layout/AppLayout.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/index.css`

**Implementation:**
- skills API client methods + TS types
- query hooks for list/detail
- page for create/edit/toggle/delete
- route and nav wiring

**Frontend verification:**

```bash
cd web && npm run lint
cd web && npm run build
```

Expected: pass.

### Task 4: Full Verification And Handoff Update

**Verification:**

```bash
.venv/bin/pytest tests/services/test_skills_service.py tests/app/routes/test_skills_routes.py tests/app/routes/test_api_routes.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

**Docs:**
- update `docs/progress.md` with `M7.4.4` completion evidence and next entrypoint `M7.4.5`

