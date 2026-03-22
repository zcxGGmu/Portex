# Terminal Relevance Offline Baseline Expansion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand offline terminal relevance fixture coverage from 4 to 8 deterministic cases to better gate future post-`M8.5.51` ranking refinements.

**Architecture:** Reuse the existing benchmark harness and parser unchanged. Only extend fixture data and test expectations so evaluation metrics are computed over a broader case set, including ranking-ladder and pagination slice scenarios.

**Tech Stack:** Python 3.11, pytest, JSON fixtures, `TerminalSessionService` benchmark harness

---

### Task 1: Add RED Assertions For Expanded Baseline Size

**Files:**
- Modify: `tests/scripts/test_evaluate_terminal_relevance.py`
- Reference: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Update expectations to expanded case count**

Set fixture and report assertions to `8` cases.

**Step 2: Run focused script tests to confirm RED**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- failure because fixture still has 4 cases

### Task 2: Expand Offline Fixture Cases

**Files:**
- Modify: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Add deterministic ranking-ladder case**

Add a case covering:

- raw marker
- wrapper marker
- plain exact-tag

with explicit expected order.

**Step 2: Add pagination slice cases**

Add `limit`/`offset` cases for:

- `M8.5.50` mixed-other count path
- `M8.5.51` mixed-other offset path
- no-single-space fallback path

Each case keeps full `expected_order` and uses pagination slice for pass/fail.

**Step 3: Run focused script tests to confirm GREEN**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- all tests pass

### Task 3: Validate Baseline Metrics And Regressions

**Files:**
- Reference: `scripts/evaluate_terminal_relevance.py`
- Reference: `tests/services/test_terminal_sessions.py`
- Reference: `tests/app/routes/test_terminal_monitor_routes.py`
- Reference: `tests/app/routes/test_terminal_routes.py`
- Reference: `tests/app/routes/test_terminal_websocket_routes.py`
- Reference: `tests/app/routes/test_api_routes.py`

**Step 1: Run offline baseline script**

```bash
.venv/bin/python scripts/evaluate_terminal_relevance.py --format text
```

Expected:

- `case_count=8`, `pass_count=8`, `pass_rate=1.000`, `top1_accuracy=1.000`, `mrr=1.000`

**Step 2: Run terminal-focused regression**

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- no regressions

**Step 3: Run full backend and hygiene checks**

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- all checks pass

### Task 4: Sync Restart/Handoff Docs

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`

**Step 1: Record expanded baseline context**

Update:

- current baseline case count and metrics
- newly covered ranking/pagination paths
- immediate next-step guidance (evaluate metrics before any new tie-break)

**Step 2: Commit docs sync**

```bash
git add docs/progress.md AGENTS.md
git commit -m "docs(handoff): sync offline relevance baseline expansion context"
```
