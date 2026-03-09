# M5.2.2 Telegram Message Handling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add minimal Telegram update normalization so the client can turn raw `message` updates into a stable event object without expanding into routing or reply behavior.

**Architecture:** Extend the existing Telegram polling client with a small pure parsing method and a single normalized dataclass, mirroring the current Feishu event-handling style. Keep support intentionally narrow: only top-level `message` updates are recognized, while unsupported update families return `None`.

**Tech Stack:** Python 3.11, `dataclasses`, `pytest`, `pytest-asyncio`

---

### Task 1: Write Telegram message-handling tests first

**Files:**
- Modify: `tests/infra/im/test_telegram.py`
- Reference: `tests/infra/im/test_feishu.py`

**Step 1: Write the failing test**

Add tests for:

```python
def test_handle_update_normalizes_text_message() -> None:
    ...

def test_handle_update_returns_none_for_unsupported_update_family() -> None:
    ...

def test_handle_update_keeps_ids_for_non_text_message() -> None:
    ...

def test_handle_update_raises_for_invalid_message_payload() -> None:
    ...
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest -o addopts='' tests/infra/im/test_telegram.py -q`
Expected: FAIL because `TelegramMessageEvent` and `handle_update()` do not exist yet.

**Step 3: Write minimal implementation**

Implement the smallest event dataclass and parser needed by the tests:

```python
@dataclass(slots=True)
class TelegramMessageEvent:
    ...

def handle_update(self, update: dict[str, object]) -> TelegramMessageEvent | None:
    ...
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest -o addopts='' tests/infra/im/test_telegram.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/infra/im/test_telegram.py infra/im/telegram.py
git commit -m "feat(im): add telegram message handling"
```

### Task 2: Refresh docs and run milestone verification

**Files:**
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
- Modify: `tasks/todo.md`

**Step 1: Update milestone status**

Record `M5.2.2` completion, verification evidence, and the next start point (`M5.2.3`).

**Step 2: Run focused and regression verification**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
```

Expected: all pass.

**Step 3: Mark session checklist and review notes**

Update `tasks/todo.md` with completion state, verification commands, and summary.

**Step 4: Commit**

```bash
git add docs/progress.md docs/TODO.md tasks/todo.md
git commit -m "docs(handoff): record M5.2.2 progress"
```
