# M5.2.1 Telegram Client Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the Telegram placeholder with a minimal async Bot API client that can fetch updates safely and is covered by focused tests.

**Architecture:** Follow the existing Feishu client shape: a small dataclass with injected `httpx` transport and explicit domain error mapping. Keep `M5.2.1` limited to HTTP client construction plus `getUpdates`; defer update normalization and markdown formatting to later TODO items.

**Tech Stack:** Python 3.11, `httpx`, `pytest`, `pytest-asyncio`

---

### Task 1: Write Telegram client tests first

**Files:**
- Create: `tests/infra/im/test_telegram.py`
- Reference: `tests/infra/im/test_feishu.py`

**Step 1: Write the failing test**

Add tests for:

```python
@pytest.mark.asyncio
async def test_get_updates_returns_result_and_uses_expected_request_shape() -> None:
    ...

@pytest.mark.asyncio
async def test_get_updates_forwards_allowed_updates() -> None:
    ...

@pytest.mark.asyncio
async def test_get_updates_raises_for_telegram_error_payload() -> None:
    ...

@pytest.mark.asyncio
async def test_get_updates_raises_for_missing_result_list() -> None:
    ...
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest -o addopts='' tests/infra/im/test_telegram.py -q`
Expected: FAIL because the current placeholder client does not expose the async API or error handling yet.

**Step 3: Write minimal implementation**

Implement the smallest `TelegramClient` contract needed by the tests:

```python
class TelegramClientError(RuntimeError):
    ...

@dataclass(slots=True)
class TelegramClient:
    bot_token: str
    base_url: str = "https://api.telegram.org"
    http_client: httpx.AsyncClient | object | None = None

    async def get_updates(...):
        ...
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest -o addopts='' tests/infra/im/test_telegram.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/infra/im/test_telegram.py infra/im/telegram.py
git commit -m "feat(im): add telegram client skeleton"
```

### Task 2: Update handoff docs and verify regression

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Update milestone status**

Record `M5.2.1` completion, latest test evidence, and the next start point (`M5.2.2`).

**Step 2: Run focused and regression verification**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
```

Expected: all pass.

**Step 3: Mark session checklist and review notes**

Update `tasks/todo.md` with completion status, verification commands, and summary.

**Step 4: Commit**

```bash
git add docs/progress.md tasks/todo.md
git commit -m "docs(handoff): record M5.2.1 progress"
```
