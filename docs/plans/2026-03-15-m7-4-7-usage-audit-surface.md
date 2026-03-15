# M7.4.7 Usage And Audit Operator Surface Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add minimal operator-facing usage and audit pages/APIs on top of current persisted message data, and explicitly defer heavier parity items (token-cost analytics and auth-event audit).

**Architecture:** Introduce one DB-backed read service for usage/audit aggregation, expose `GET /usage/stats` and `GET /audit/messages` routes with owner/admin gate, and wire two operator web pages (`/usage`, `/audit`) using new API clients/hooks.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic v2, React, TypeScript, Vite

---

### Task 1: Add Red Tests For Usage/Audit Service, Routes, And OpenAPI Contracts

**Files:**
- Create: `tests/services/test_usage_audit_service.py`
- Create: `tests/app/routes/test_usage_audit_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`

**Coverage:**
- usage aggregation from message rows + attachments metadata
- malformed attachments JSON tolerance
- audit list sorting/filtering/limit clamp behavior
- `/usage/stats` and `/audit/messages` authentication and role gate (`owner/admin` only)
- OpenAPI `usage`/`audit` tags + route schema visibility

**Step 1: Write failing tests first**

**Step 2: Run focused tests to confirm RED**

Run:
```bash
.venv/bin/pytest tests/services/test_usage_audit_service.py tests/app/routes/test_usage_audit_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:
- fails before implementation exists

### Task 2: Implement Backend Usage/Audit Service And Routes

**Files:**
- Create: `services/usage_audit.py`
- Create: `app/routes/usage.py`
- Create: `app/routes/audit.py`
- Modify: `domain/schemas.py`
- Modify: `app/openapi.py`
- Modify: `app/main.py`
- Modify: `app/routes/__init__.py`

**Step 1: Implement read service**
- read `messages` rows from DB
- parse attachments metadata safely
- aggregate usage summary/daily/channel payloads
- provide recent audit message list with optional group filter

**Step 2: Add DTO contracts**
- usage summary/daily/channel response models
- audit message list response models

**Step 3: Add routes and role gates**
- `GET /usage/stats`
- `GET /audit/messages`
- owner/admin allowed, member gets `403`

**Step 4: Run focused backend tests**

Run:
```bash
.venv/bin/pytest tests/services/test_usage_audit_service.py tests/app/routes/test_usage_audit_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:
- pass

### Task 3: Add `/usage` And `/audit` Web Pages

**Files:**
- Create: `web/src/pages/Usage.tsx`
- Create: `web/src/pages/Audit.tsx`
- Modify: `web/src/App.tsx`
- Modify: `web/src/components/layout/AppLayout.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`
- Modify: `web/src/index.css`

**Step 1: Add API types + client methods for usage/audit**

**Step 2: Add hooks for usage/audit queries**

**Step 3: Build operator-only UI pages**
- usage period switcher + summary cards + tables
- audit filter + feed table
- forbidden/unavailable/loading states aligned with monitor page

**Step 4: Run frontend verification**

Run:
```bash
cd web && npm run lint
cd web && npm run build
```

Expected:
- pass

### Task 4: Full Verification, Handoff Sync, And Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`

**Step 1: Run focused + regression + hygiene**

Run:
```bash
.venv/bin/pytest tests/services/test_usage_audit_service.py tests/app/routes/test_usage_audit_routes.py tests/app/routes/test_api_routes.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

**Step 2: Update restart handoff**
- record `M7.4.7` completion evidence
- move next entrypoint forward

**Step 3: Commit phase completion immediately**
- commit format: `type(scope): summary`
