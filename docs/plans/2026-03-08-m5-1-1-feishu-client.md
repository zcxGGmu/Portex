# M5.1.1 Feishu Client Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M5.1.1` by replacing the Feishu placeholder client with a minimal async client that can fetch a tenant access token and provide signature/decryption primitives for future event handling.

**Architecture:** Keep the implementation inside `infra/im/feishu.py`. Add async auth over `httpx`, pure helpers for signature verification and event decryption, and focused tests that prove the cryptographic contract without requiring live network calls.

**Tech Stack:** Python 3.11, `httpx`, `hashlib`, `base64`, `cryptography`, `pytest`

---

### Task 1: Write failing Feishu client tests

**Files:**
- Create: `tests/infra/im/test_feishu.py`

**Step 1: Add failing tests**

Cover:
- token retrieval success
- token retrieval failure on non-zero Feishu code
- valid and invalid signature verification
- decrypt round-trip for a generated encrypted payload
- decrypt failure when no `encrypt_key` is configured

**Step 2: Run focused tests to verify RED**

Run:
- `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py -q`

Expected: FAIL because the Feishu client is still a placeholder.

### Task 2: Implement minimal Feishu client foundation

**Files:**
- Modify: `infra/im/feishu.py`

**Step 1: Add async auth**

Implement `get_access_token()` using the Feishu tenant access token endpoint with injectable `httpx.AsyncClient`.

**Step 2: Add signature verification**

Implement `verify_signature()` with the configured verification token.

**Step 3: Add decrypt helper**

Implement `decrypt_event()` using AES-CBC and the Feishu length-prefixed payload format.

**Step 4: Re-run focused tests to verify GREEN**

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
- `M5.1.1` complete
- auth/signature/decryption foundation is ready
- next starting point becomes `M5.1.2`

**Step 3: Commit**

Prepare a focused commit such as:
- `feat(im): complete M5.1.1 feishu client skeleton`
