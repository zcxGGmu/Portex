# M4.4.3 Memory Search Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M4.4.3` by adding a minimal file-content search API to the existing memory service.

**Architecture:** Keep memory search file-backed and service-only. Search only markdown files inside a specific group folder, match case-insensitively on file contents, and return deterministic path strings. Do not expand into APIs, snippets, indexing, or runner integration.

**Tech Stack:** Python 3.11, pathlib, asyncio, pytest

---

### Task 1: Write failing memory-search tests

**Files:**
- Modify: `tests/services/test_memory_service.py`

**Step 1: Add failing tests**

Cover:
- `search_memory()` returns matched markdown files in the target group
- matching is case-insensitive
- blank query returns empty list
- other groups are excluded
- user-global `AGENTS.md` is excluded

**Step 2: Run focused tests to verify RED**

Run:
- `.venv/bin/pytest -o addopts='' tests/services/test_memory_service.py -q`

Expected: FAIL because memory search does not exist yet.

### Task 2: Implement minimal memory search

**Files:**
- Modify: `services/memory.py`

**Step 1: Add search helper**

Implement a helper for the group memory directory and recursive markdown file discovery.

**Step 2: Add search method**

Implement `search_memory(group_folder, query)` to:
- return `[]` for blank queries
- search only the target group directory
- match case-insensitively on file contents
- return sorted path strings

**Step 3: Re-run focused tests to verify GREEN**

Run:
- `.venv/bin/pytest -o addopts='' tests/services/test_memory_service.py -q`

Expected: PASS.

### Task 3: Regression verification, docs, and commit

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest -o addopts='' tests/services/test_memory_service.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update docs**

Record:
- `M4.4.3` complete
- search contract and exclusions
- current starting point advances to `M4.4.4`

**Step 3: Commit**

Prepare a focused commit such as:
- `feat(memory): complete M4.4.3 memory search`
