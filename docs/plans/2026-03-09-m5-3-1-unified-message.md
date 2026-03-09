# M5.3.1 Unified Message Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Introduce a minimal routeable `UnifiedMessage` DTO and conversion helpers for Feishu and Telegram message events.

**Architecture:** Add a small cross-channel schema in `domain/schemas.py`, then keep each channel-specific event contract intact while giving it a `to_unified_message()` adapter. Avoid service and route rewrites in this step; this milestone is about standardizing shape, not rewiring the whole message flow.

**Tech Stack:** Python 3.11, Pydantic v2, dataclasses, pytest

---

### Task 1: Write schema and channel-conversion tests first

**Files:**
- Add: `tests/domain/test_schemas.py`
- Modify: `tests/infra/im/test_feishu.py`
- Modify: `tests/infra/im/test_telegram.py`

**Step 1: Write the failing test**

Add tests for:

```python
def test_unified_message_accepts_optional_group_folder_and_normalizes_timestamp() -> None:
    ...

def test_feishu_message_event_converts_to_unified_message() -> None:
    ...

def test_feishu_non_text_event_converts_to_unified_message_with_empty_content() -> None:
    ...

def test_telegram_message_event_converts_to_unified_message() -> None:
    ...

def test_telegram_non_text_event_converts_to_unified_message_with_empty_content() -> None:
    ...
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest -o addopts='' tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`
Expected: FAIL because `UnifiedMessage` and the conversion helpers do not exist yet.

**Step 3: Write minimal implementation**

Implement:

```python
class UnifiedMessage(BaseModel):
    ...

def to_unified_message(self, group_folder: str | None = None) -> UnifiedMessage:
    ...
```

Also add the smallest timestamp extraction/fallback logic needed by the tests.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest -o addopts='' tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py domain/schemas.py infra/im/feishu.py infra/im/telegram.py
git commit -m "feat(messages): add unified message schema"
```

### Task 2: Refresh docs and run milestone verification

**Files:**
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
- Modify: `tasks/todo.md`

**Step 1: Update milestone status**

Record `M5.3.1` completion, verification evidence, and the next start point (`M5.3.2`).

**Step 2: Run focused and regression verification**

Run:

```bash
.venv/bin/pytest -o addopts='' tests/domain/test_schemas.py tests/infra/im/test_feishu.py tests/infra/im/test_telegram.py -q
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
```

Expected: all pass.

**Step 3: Mark session checklist and review notes**

Update `tasks/todo.md` with completion state, verification commands, and summary.

**Step 4: Commit**

```bash
git add docs/progress.md docs/TODO.md tasks/todo.md
git commit -m "docs(handoff): record M5.3.1 progress"
```
