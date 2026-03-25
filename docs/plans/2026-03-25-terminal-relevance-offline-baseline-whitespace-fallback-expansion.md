# Terminal Relevance Offline Baseline Whitespace Fallback Expansion Implementation Plan

**Goal:** Expand offline terminal relevance coverage from 66 to 70 deterministic cases so the remaining whitespace-family no-single-space fallback branches are included in the offline benchmark.

**Architecture:** Keep production ranking logic unchanged. Reuse the existing benchmark harness and only extend fixture data, fixture-aware script tests, and restart-oriented progress notes.

**Tech Stack:** Python 3.11, pytest, JSON fixtures, `TerminalSessionService` benchmark harness

---

### Task 1: Add RED Expectations For 70 Cases

**Files:**
- Modify: `tests/scripts/test_evaluate_terminal_relevance.py`
- Reference: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Update fixture expectations**

- change case-count assertions from `66` to `70`
- assert the four new whitespace fallback case IDs are present

**Step 2: Run focused script tests to confirm RED**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- failure because the committed fixture still has 66 cases

### Task 2: Expand The Fixture

**Files:**
- Modify: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Add tab-prefixed payload fallback coverage**

- add a deterministic case derived from the landed `M8.5.44` service test

**Step 2: Add multi-space payload fallback coverage**

- add a deterministic case derived from the landed `M8.5.46` service test

**Step 3: Add space-prefixed mixed-whitespace payload fallback coverage**

- add a deterministic case derived from the landed `M8.5.48` service test

**Step 4: Add other-leading whitespace payload fallback coverage**

- add a deterministic case derived from the landed `M8.5.49` service test

**Step 5: Re-run focused script tests to confirm GREEN**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- all tests pass

### Task 3: Validate Expanded Baseline And Regressions

**Files:**
- Reference: `scripts/evaluate_terminal_relevance.py`
- Reference: `tests/services/test_terminal_sessions.py`
- Reference: `tests/app/routes/test_terminal_monitor_routes.py`
- Reference: `tests/app/routes/test_terminal_routes.py`
- Reference: `tests/app/routes/test_terminal_websocket_routes.py`
- Reference: `tests/app/routes/test_api_routes.py`

**Step 1: Run the offline baseline script**

```bash
.venv/bin/python scripts/evaluate_terminal_relevance.py --format text
```

Expected:

- `case_count=70`, `pass_count=70`, `pass_rate=1.000`, `top1_accuracy=1.000`, `mrr=1.000`

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

### Task 4: Sync Restart Notes And Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`
- Modify: `tasks/todo.md`

**Step 1: Record the whitespace fallback coverage**

- update baseline case count and metrics
- note the newly covered `M8.5.44` / `M8.5.46` / `M8.5.48` / `M8.5.49` fallback paths
- clarify that the pagination gaps are already exhausted and this batch targets fallback evidence instead

**Step 2: Commit planning, feature, and handoff updates**

```bash
git add docs/plans/2026-03-25-terminal-relevance-offline-baseline-whitespace-fallback-expansion-design.md docs/plans/2026-03-25-terminal-relevance-offline-baseline-whitespace-fallback-expansion.md tasks/todo.md
git commit -m "docs(plans): add offline relevance whitespace fallback plan"

git add tests/scripts/test_evaluate_terminal_relevance.py tests/fixtures/terminal_relevance_baseline.json
git commit -m "feat(terminal): expand offline relevance whitespace fallback fixtures"

git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync offline relevance whitespace fallback context"
```
