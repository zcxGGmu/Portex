# M5.1.3 Feishu Send Message Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M5.1.3` by adding a minimal async Feishu message send method using the official message endpoint.

**Architecture:** Keep the implementation inside `infra/im/feishu.py`. Reuse the existing async auth helper to acquire a tenant access token, then issue a single POST to the Feishu message endpoint with the smallest request contract that is easy to test and extend later.

**Tech Stack:** Python 3.11, `httpx`, `json`, `pytest`

---

### Task 1: Write failing Feishu send-message tests

**Files:**
- Modify: `tests/infra/im/test_feishu.py`

**Step 1: Add failing tests**

Cover:
- successful send builds the expected URL, headers, and JSON payload
- dict message content is JSON-serialized
- Feishu error code raises `FeishuClientError`

**Step 2: Run focused tests to verify RED**

Run:
- `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py -q`

Expected: FAIL because send-message is still a placeholder.

### Task 2: Implement minimal Feishu send-message support

**Files:**
- Modify: `infra/im/feishu.py`

**Step 1: Add request builder**

Validate the minimal `msg_type` / `content` contract and serialize dict message bodies.

**Step 2: Add async send method**

Fetch a tenant access token, call the Feishu message send endpoint, and return the response payload on success.

**Step 3: Re-run focused tests to verify GREEN**

Run:
- `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py -q`

Expected: PASS.

### Task 3: Regression verification, docs, and commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update docs**

Record:
- `M5.1.3` complete
- send-message request contract
- next starting point becomes `M5.2.1`

**Step 3: Commit**

Prepare a focused commit such as:
- `feat(im): complete M5.1.3 feishu send message`
