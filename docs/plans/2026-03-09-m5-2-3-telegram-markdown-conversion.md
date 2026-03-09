# M5.2.3 Telegram Markdown Conversion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a minimal Markdown-to-Telegram-HTML formatter that safely handles the most common code-oriented output patterns without expanding into sending or routing behavior.

**Architecture:** Extend `TelegramClient` with a small pure helper that escapes Telegram HTML first and then applies a narrow set of formatting transforms. Keep support intentionally constrained to fenced code blocks, inline code, bold, and italic, leaving unsupported syntax untouched.

**Tech Stack:** Python 3.11, `re`, `html`, `pytest`

---

### Task 1: Write Telegram markdown conversion tests first

**Files:**
- Modify: `tests/infra/im/test_telegram.py`
- Reference: `infra/im/telegram.py`

**Step 1: Write the failing test**

Add tests for:

```python
def test_markdown_to_html_escapes_plain_text_html_characters() -> None:
    ...

def test_markdown_to_html_converts_basic_inline_formatting() -> None:
    ...

def test_markdown_to_html_converts_fenced_code_blocks_without_reformatting_inner_markdown() -> None:
    ...

def test_markdown_to_html_keeps_incomplete_markers_as_plain_text() -> None:
    ...

def test_markdown_to_html_leaves_unsupported_markdown_syntax_unchanged() -> None:
    ...
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest -o addopts='' tests/infra/im/test_telegram.py -q`
Expected: FAIL because `markdown_to_html()` does not exist yet.

**Step 3: Write minimal implementation**

Implement the smallest helper needed by the tests:

```python
def markdown_to_html(self, text: str) -> str:
    ...
```

Use a placeholder-based approach so fenced code blocks are escaped safely and not reformatted by the later inline regexes.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest -o addopts='' tests/infra/im/test_telegram.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/infra/im/test_telegram.py infra/im/telegram.py
git commit -m "feat(im): add telegram markdown conversion"
```

### Task 2: Refresh docs and run milestone verification

**Files:**
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
- Modify: `tasks/todo.md`

**Step 1: Update milestone status**

Record `M5.2.3` completion, verification evidence, and the next start point (`M5.3.1`).

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
git commit -m "docs(handoff): record M5.2.3 progress"
```
