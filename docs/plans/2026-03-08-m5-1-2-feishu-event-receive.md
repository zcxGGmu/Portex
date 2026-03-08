# M5.1.2 Feishu Event Receive Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M5.1.2` by adding a minimal Feishu callback event parser that returns a normalized message event structure for `im.message.receive_v1`.

**Architecture:** Keep this inside `infra/im/feishu.py`. Reuse the auth/signature/decryption foundation from `M5.1.1`, add a small dataclass for normalized message events, and expose a single event-handling method that accepts plaintext or encrypted payloads but stops short of route wiring or message-pipeline integration.

**Tech Stack:** Python 3.11, dataclasses, json, pytest

---

### Task 1: Write failing Feishu event tests

**Files:**
- Modify: `tests/infra/im/test_feishu.py`

**Step 1: Add failing tests**

Cover:
- plaintext message event normalization
- encrypted message event normalization
- unsupported event returns `None`
- malformed/non-text message content leaves `text=None`

**Step 2: Run focused tests to verify RED**

Run:
- `.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py -q`

Expected: FAIL because event parsing does not exist yet.

### Task 2: Implement minimal Feishu event parsing

**Files:**
- Modify: `infra/im/feishu.py`

**Step 1: Add normalized event dataclass**

Add `FeishuMessageEvent`.

**Step 2: Add event handler**

Implement `handle_webhook_event(payload)` with support for encrypted and plaintext payloads.

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
- `M5.1.2` complete
- normalized Feishu event parsing is ready
- next starting point becomes `M5.1.3`

**Step 3: Commit**

Prepare a focused commit such as:
- `feat(im): complete M5.1.2 feishu event receive`
