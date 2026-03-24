# Terminal Relevance Offline Baseline Brace And Angle Pairwise Expansion Implementation Plan

**Goal:** Expand offline terminal relevance coverage from 36 to 40 deterministic cases so the remaining brace/angle direct pairwise and branch-specific fallback/offset behaviors are included in the offline benchmark.

**Architecture:** Keep production ranking logic unchanged. Reuse the existing benchmark harness and only extend fixture data, fixture-aware script tests, and restart-oriented progress notes.

**Tech Stack:** Python 3.11, pytest, JSON fixtures, `TerminalSessionService` benchmark harness

---

### Task 1: Add RED Expectations For 40 Cases

**Files:**
- Modify: `tests/scripts/test_evaluate_terminal_relevance.py`
- Reference: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Update fixture expectations**

- change case-count assertions from `36` to `40`
- assert the new brace/angle pairwise case IDs are present

**Step 2: Run focused script tests to confirm RED**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- failure because the committed fixture still has 36 cases

### Task 2: Expand The Fixture

**Files:**
- Modify: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Add brace-wrapper direct pairwise coverage**

- add a deterministic case derived from the landed brace-vs-angle wrapper marker test

**Step 2: Add brace plain exact-tag direct pairwise coverage**

- add a deterministic case derived from the landed brace-vs-angle plain exact-tag test

**Step 3: Add no-brace-plain fallback coverage**

- add a deterministic case derived from the landed fallback-to-`M8.5.35` test

**Step 4: Add angle-plain offset tie-break coverage**

- add a deterministic case derived from the landed `M8.5.37` offset tie-break test

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

- `case_count=40`, `pass_count=40`, `pass_rate=1.000`, `top1_accuracy=1.000`, `mrr=1.000`

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
- Modify: `tasks/todo.md`

**Step 1: Record the expanded brace/angle pairwise coverage**

- update baseline case count and metrics
- note the newly covered pairwise and fallback paths
- keep next-step guidance as “use baseline evidence before any new tie-break”

**Step 2: Commit planning, feature, and handoff updates**

```bash
git add docs/plans/2026-03-24-terminal-relevance-offline-baseline-brace-and-angle-pairwise-expansion-design.md docs/plans/2026-03-24-terminal-relevance-offline-baseline-brace-and-angle-pairwise-expansion.md
git commit -m "docs(plans): add offline relevance brace and angle pairwise expansion plan"

git add tests/scripts/test_evaluate_terminal_relevance.py tests/fixtures/terminal_relevance_baseline.json docs/progress.md tasks/todo.md
git commit -m "feat(terminal): expand offline relevance brace and angle pairwise fixtures"

git add docs/progress.md tasks/todo.md
git commit -m "docs(handoff): sync offline relevance brace and angle pairwise context"
```
