# Terminal Relevance Offline Baseline Additive Fallback And Early Pagination Expansion Implementation Plan

**Goal:** Expand offline terminal relevance coverage from 48 to 52 deterministic cases so one remaining additive fallback and the next uncovered early pagination branches are included in the offline benchmark.

**Architecture:** Keep production ranking logic unchanged. Reuse the existing benchmark harness and only extend fixture data, fixture-aware script tests, and restart-oriented progress notes.

**Tech Stack:** Python 3.11, pytest, JSON fixtures, `TerminalSessionService` benchmark harness

---

### Task 1: Add RED Expectations For 52 Cases

**Files:**
- Modify: `tests/scripts/test_evaluate_terminal_relevance.py`
- Reference: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Update fixture expectations**

- change case-count assertions from `48` to `52`
- assert the four new fallback / pagination case IDs are present

**Step 2: Run focused script tests to confirm RED**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- failure because the committed fixture still has 48 cases

### Task 2: Expand The Fixture

**Files:**
- Modify: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Add no-exact-tag-wrapper fallback coverage**

- add a deterministic case derived from the landed `M8.5.22` fallback test

**Step 2: Add whole-word pagination coverage**

- add a deterministic paginated case derived from the landed `M8.5.18` word-boundary pagination test

**Step 3: Add line-boundary pagination coverage**

- add a deterministic paginated case derived from the landed `M8.5.19` line-boundary pagination test

**Step 4: Add line-start-quality pagination coverage**

- add a deterministic paginated case derived from the landed `M8.5.20` line-start-quality pagination test

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

- `case_count=52`, `pass_count=52`, `pass_rate=1.000`, `top1_accuracy=1.000`, `mrr=1.000`

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

**Step 1: Record the expanded fallback and pagination coverage**

- update baseline case count and metrics
- note the newly covered `M8.5.22` fallback and early pagination paths
- keep next-step guidance as “use baseline evidence before any new tie-break”

**Step 2: Commit planning, feature, and handoff updates**

```bash
git add docs/plans/2026-03-25-terminal-relevance-offline-baseline-additive-fallback-and-early-pagination-expansion-design.md docs/plans/2026-03-25-terminal-relevance-offline-baseline-additive-fallback-and-early-pagination-expansion.md tasks/todo.md
git commit -m "docs(plans): add offline relevance additive fallback and early pagination plan"

git add tests/scripts/test_evaluate_terminal_relevance.py tests/fixtures/terminal_relevance_baseline.json
git commit -m "feat(terminal): expand offline relevance additive fallback and early pagination fixtures"

git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync offline relevance additive fallback and early pagination context"
```
