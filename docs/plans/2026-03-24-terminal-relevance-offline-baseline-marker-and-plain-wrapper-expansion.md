# Terminal Relevance Offline Baseline Marker And Plain Wrapper Expansion Implementation Plan

**Goal:** Expand offline terminal relevance coverage from 16 to 20 deterministic cases so the landed marker-family and plain-wrapper-family pagination behaviors are included in the offline benchmark.

**Architecture:** Keep production ranking logic unchanged. Reuse the existing benchmark harness and only extend fixture data, fixture-aware script tests, and restart-oriented progress notes.

**Tech Stack:** Python 3.11, pytest, JSON fixtures, `TerminalSessionService` benchmark harness

---

### Task 1: Add RED Expectations For 20 Cases

**Files:**
- Modify: `tests/scripts/test_evaluate_terminal_relevance.py`
- Reference: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Update fixture expectations**

- change case-count assertions from `16` to `20`
- assert the new marker/plain-wrapper case IDs are present

**Step 2: Run focused script tests to confirm RED**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- failure because the committed fixture still has 16 cases

### Task 2: Expand The Fixture

**Files:**
- Modify: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Add exact-tag colon-marker pagination coverage**

- add a deterministic case derived from the landed colon-marker pagination test

**Step 2: Add square-bracket dash-marker pagination coverage**

- add a deterministic case derived from the landed square-bracket dash-marker pagination test

**Step 3: Add square-bracket exact-tag pagination coverage**

- add a deterministic case derived from the landed square-bracket exact-tag pagination test

**Step 4: Add paren plain-wrapper pagination coverage**

- add a deterministic case derived from the landed paren plain-wrapper pagination test

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

- `case_count=20`, `pass_count=20`, `pass_rate=1.000`, `top1_accuracy=1.000`, `mrr=1.000`

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

**Step 1: Record the expanded marker/plain-wrapper coverage**

- update baseline case count and metrics
- note the newly covered marker/plain-wrapper pagination paths
- keep next-step guidance as “use baseline evidence before any new tie-break”

**Step 2: Commit planning, feature, and handoff updates**

```bash
git add docs/plans/2026-03-24-terminal-relevance-offline-baseline-marker-and-plain-wrapper-expansion-design.md docs/plans/2026-03-24-terminal-relevance-offline-baseline-marker-and-plain-wrapper-expansion.md
git commit -m "docs(plans): add offline relevance marker and plain wrapper expansion plan"

git add tests/scripts/test_evaluate_terminal_relevance.py tests/fixtures/terminal_relevance_baseline.json docs/progress.md tasks/todo.md
git commit -m "feat(terminal): expand offline relevance marker and plain wrapper fixtures"

git add docs/progress.md tasks/todo.md
git commit -m "docs(handoff): sync offline relevance marker and plain wrapper context"
```
