# M7.4.6 Settings And Configuration Surface Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a real settings/configuration API + UI surface for provider, channels, registration policy, appearance, and system settings, and enforce registration policy in `/auth/register`.

**Architecture:** Introduce one filesystem-backed `SettingsService` with user-scope and system-scope JSON files, expose `/settings` routes with role-aware permission boundaries, wire registration policy in auth registration flow, and expand existing `/settings` page into editable sections.

**Tech Stack:** FastAPI, Pydantic v2, React, TypeScript, Vite

---

### Task 1: Add Red Tests For Settings Service, Settings Routes, And Register Policy Wiring

**Files:**
- Create: `tests/services/test_settings_service.py`
- Create: `tests/app/routes/test_settings_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`

**Coverage:**
- default load and update persistence for provider/channels/registration/appearance/system
- user isolation for user-owned configs
- path/symlink safety and invalid user id rejection
- `/settings/*` authentication and permission boundaries
- register policy enforcement (`allow_registration`, `require_invite_code`)
- OpenAPI tag/path/schema assertions for settings routes

**Step 1: Write failing tests**
- add service tests and route tests first
- add openapi assertions for `settings` tag and settings paths

**Step 2: Run test to verify it fails**

Run:
```bash
.venv/bin/pytest tests/services/test_settings_service.py tests/app/routes/test_settings_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:
- fails because `SettingsService` and `/settings` routes do not exist yet

### Task 2: Implement Backend Settings Service And Routes

**Files:**
- Create: `services/settings.py`
- Create: `app/routes/settings.py`
- Modify: `domain/schemas.py`
- Modify: `app/openapi.py`
- Modify: `app/main.py`
- Modify: `app/routes/__init__.py`
- Modify: `app/routes/auth.py`

**Step 1: Implement `SettingsService`**
- file-backed JSON storage in `data/settings`
- user scope files: provider + channels
- global scope files: registration + appearance + system
- safety guards: safe user segment, root containment, symlink escape, max file size, atomic writes

**Step 2: Add DTOs and route contracts**
- add request/response models in `domain/schemas.py`
- add `settings` tag in OpenAPI metadata

**Step 3: Add `/settings` route family**
- `GET/PUT /settings/provider`
- `GET/PUT /settings/channels`
- `GET/PUT /settings/registration`
- `GET/PUT /settings/appearance`
- `GET/PUT /settings/system`

**Step 4: Wire registration policy in `/auth/register`**
- enforce `allow_registration`
- enforce `require_invite_code`
- preserve existing invite behavior

**Step 5: Run focused backend tests**

Run:
```bash
.venv/bin/pytest tests/services/test_settings_service.py tests/app/routes/test_settings_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:
- pass

### Task 3: Expand Frontend Settings Page

**Files:**
- Modify: `web/src/pages/Settings.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/index.css`

**Step 1: Add API types and clients for settings sections**
- add provider/channels/registration/appearance/system request/response types
- add client methods for all `/settings` endpoints

**Step 2: Add hooks for settings queries**
- add query hooks for each settings section

**Step 3: Expand `/settings` page UI**
- keep account summary
- add editable cards/forms for provider/channels
- add role-aware cards/forms for registration/appearance/system

**Step 4: Run frontend verification**

Run:
```bash
cd web && npm run lint
cd web && npm run build
```

Expected:
- both commands pass

### Task 4: Full Verification, Progress Update, And Commit

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run focused + regression + hygiene**

Run:
```bash
.venv/bin/pytest tests/services/test_settings_service.py tests/app/routes/test_settings_routes.py tests/app/routes/test_api_routes.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

**Step 2: Update handoff docs**
- record `M7.4.6` completion evidence
- move next entrypoint to `M7.4.7`

**Step 3: Commit**
- commit message should follow `type(scope): summary`
