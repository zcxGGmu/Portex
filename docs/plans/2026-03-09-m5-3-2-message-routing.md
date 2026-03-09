# M5.3.2 Message Routing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a minimal message router that dispatches `UnifiedMessage` instances to injected Feishu, Telegram, or Web handlers.

**Architecture:** Keep routing as a thin orchestration layer in `services/`, separate from channel client implementations and separate from persistence or API routes. The router only chooses the correct handler based on `message.channel` and leaves all delivery details to the injected downstream handler.

**Tech Stack:** Python 3.11, asyncio, pytest

---

### Task 1: Write message router tests first

**Files:**
- Add: `tests/services/test_message_router.py`
- Reference: `domain/schemas.py`

**Step 1: Write the failing test**

Add tests for:

```python
@pytest.mark.asyncio
async def test_route_message_dispatches_feishu_messages() -> None:
    ...

@pytest.mark.asyncio
async def test_route_message_dispatches_telegram_messages() -> None:
    ...

@pytest.mark.asyncio
async def test_route_message_dispatches_web_messages() -> None:
    ...

@pytest.mark.asyncio
async def test_route_message_raises_for_unknown_channel() -> None:
    ...

@pytest.mark.asyncio
async def test_route_message_propagates_handler_errors() -> None:
    ...
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest -o addopts='' tests/services/test_message_router.py -q`
Expected: FAIL because the router service does not exist yet.

**Step 3: Write minimal implementation**

Implement:

```python
class MessageRouterError(RuntimeError):
    ...

class MessageRouter:
    def __init__(...):
        ...

    async def route_message(self, message: UnifiedMessage) -> None:
        ...
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest -o addopts='' tests/services/test_message_router.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/services/test_message_router.py services/message_router.py
git commit -m "feat(messages): add message router"
```

### Task 2: Refresh docs and run milestone verification

**Files:**
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
- Modify: `tasks/todo.md`

**Step 1: Update milestone status**

Record `M5.3.2` completion, verification evidence, and the next start point (`M5.4`).

**Step 2: Run focused and regression verification**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/services/test_message_router.py tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
```

Expected: all pass.

**Step 3: Mark session checklist and review notes**

Update `tasks/todo.md` with completion state, verification commands, and summary.

**Step 4: Commit**

```bash
git add docs/progress.md docs/TODO.md tasks/todo.md
git commit -m "docs(handoff): record M5.3.2 progress"
```
