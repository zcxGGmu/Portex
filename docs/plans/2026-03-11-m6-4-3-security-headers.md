# M6.4.3 Security Headers Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M6.4.3` by adding a minimal HTTP security-header middleware to the FastAPI app and verifying it on normal API responses and CORS preflight responses.

**Architecture:** Add a small ASGI middleware in `app/middleware/security.py` that decorates outgoing HTTP responses with a fixed low-risk header set. Register it in `app/main.py` so it wraps the existing CORS middleware, and verify behavior through route-level and integration-level tests.

**Tech Stack:** Python 3.11+, FastAPI, Starlette, pytest

---

### Task 1: Lock the header contract with failing tests

**Files:**
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `tests/integration/test_api.py`
- Reference: `app/main.py`

**Step 1: Write the failing tests**

Add focused tests that prove:
- `GET /health` returns the expected security headers
- CORS preflight responses also include the same headers
- the real integration `GET /health` path includes the new headers

**Step 2: Run tests to verify they fail**

Run:
- `.venv/bin/pytest tests/app/routes/test_api_routes.py tests/integration/test_api.py -q`

Expected: FAIL because no security-header middleware exists yet.

### Task 2: Implement the minimal middleware

**Files:**
- Create: `app/middleware/security.py`
- Modify: `app/middleware/__init__.py`
- Modify: `app/main.py`

**Step 1: Write minimal implementation**

Add:
- `DEFAULT_SECURITY_HEADERS`
- `SecurityHeadersMiddleware`
- middleware registration in `app/main.py`

Keep behavior minimal:
- only affect HTTP responses
- do not modify WebSocket traffic
- do not overwrite route-specific values if a header is already present

**Step 2: Run tests to verify they pass**

Run:
- `.venv/bin/pytest tests/app/routes/test_api_routes.py tests/integration/test_api.py -q`

Expected: PASS

### Task 3: Run milestone verification and update handoff

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest tests/app/routes/test_api_routes.py tests/integration/test_api.py -q`
- `.venv/bin/python scripts/security_scan.py`
- `.venv/bin/python scripts/dependency_audit.py`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/pytest tests/ -v --cov`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

Expected: PASS

**Step 2: Update restart-oriented docs**

Record:
- `M6.4.3` completion summary
- exact verification evidence
- the boundary that CSP/HSTS are still out of scope
- the next starting point after `M6.4.3`

### Task 4: Commit the milestone

**Files:**
- Commit all approved `M6.4.3` changes

**Step 1: Commit**

Prepare a focused commit such as:
- `feat(security): complete M6.4.3 security headers`
