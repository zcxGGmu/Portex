# M4.4.4 Memory MCP Tool Wrapping Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M4.4.4` by replacing the runner's placeholder memory tools with direct file-backed append/search tools for the mounted group memory directory.

**Architecture:** Keep the implementation fully inside the runner package. Read and write the mounted `/workspace/memory` directory directly, expose minimal `function_tool` wrappers, and avoid adding any new main-service APIs or container networking assumptions.

**Tech Stack:** Python 3.11, pathlib, datetime, OpenAI Agents SDK `function_tool`, pytest

---

### Task 1: Write failing runner memory tool tests

**Files:**
- Create: `tests/container/agent_runner/test_memory_tools.py`

**Step 1: Add failing tests**

Cover:
- append creates today's markdown file
- append preserves order across multiple writes
- search returns relative markdown paths
- search is case-insensitive
- blank search returns empty list
- `build_default_tools()` includes the memory tool wrappers

**Step 2: Run focused tests to verify RED**

Run:
- `.venv/bin/pytest -o addopts='' tests/container/agent_runner/test_memory_tools.py -q`

Expected: FAIL because the memory tools are still placeholders and are not registered.

### Task 2: Implement minimal runner memory tools

**Files:**
- Modify: `container/agent-runner/src/tools/memory.py`
- Modify: `container/agent-runner/src/tools/__init__.py`

**Step 1: Replace placeholder memory store**

Implement:
- mounted memory directory constant
- date-based append helper
- recursive markdown search helper

**Step 2: Expose tool wrappers**

Add:
- `memory_append`
- `memory_search`

and include them in `build_default_tools()`.

**Step 3: Re-run focused tests to verify GREEN**

Run:
- `.venv/bin/pytest -o addopts='' tests/container/agent_runner/test_memory_tools.py -q`

Expected: PASS.

### Task 3: Regression verification, docs, and commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest -o addopts='' tests/container/agent_runner/test_memory_tools.py tests/container/agent_runner -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update docs**

Record:
- `M4.4.4` complete
- runner tools now operate on mounted group memory
- current starting point advances to `M4.5`

**Step 3: Commit**

Prepare a focused commit such as:
- `feat(memory): complete M4.4.4 runner memory tools`
