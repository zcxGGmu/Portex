# Terminal Relevance Offline Baseline Convergence Audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Audit the current 81-case offline terminal relevance baseline against landed `M8.5.17` through `M8.5.51` service semantics and either record convergence or patch only the minimum missing offline evidence.

**Architecture:** Keep production ranking logic unchanged. Reuse `tests/services/test_terminal_sessions.py` as the semantic source of truth, compare those semantics against the JSON fixture and script assertions, and then either document convergence or add the smallest missing fixture/test cases before syncing restart docs.

**Tech Stack:** Python 3.11, pytest, JSON fixtures, Markdown planning docs, terminal relevance harness

---

### Task 1: Audit Service-Test Coverage Against The 81-Case Fixture

**Files:**
- Reference: `tests/services/test_terminal_sessions.py`
- Reference: `tests/fixtures/terminal_relevance_baseline.json`
- Reference: `tests/scripts/test_evaluate_terminal_relevance.py`

**Step 1: Enumerate the current relevance branches**

Run:

```bash
rg -n "test_terminal_session_service_relevance_" tests/services/test_terminal_sessions.py
```

Expected:

- all landed `M8.5.17` through `M8.5.51` relevance tests are visible for comparison

**Step 2: Enumerate the current offline case IDs**

Run:

```bash
rg -n '"id": "' tests/fixtures/terminal_relevance_baseline.json
```

Expected:

- the current 81-case fixture IDs are visible for mapping

**Step 3: Decide whether any non-duplicate semantic gap remains**

- compare each uncovered-looking service test to the existing fixture by ordering semantics, not by transcript identity
- pay special attention to the `M8.5.50` and `M8.5.51` count, offset, pagination, and fallback branches
- write down one conclusion only:
  - `no remaining non-duplicate gap`
  - or `real uncovered gap exists`

### Task 2: Patch The Offline Baseline Only If The Audit Finds A Real Gap

**Files:**
- Modify: `tests/scripts/test_evaluate_terminal_relevance.py`
- Modify: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Add RED expectations only for the confirmed missing case IDs**

- increase the expected case count only by the number of real missing cases
- assert the new case IDs explicitly

**Step 2: Run focused script tests to confirm RED**

Run:

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- failure because the fixture is still missing the newly asserted cases

**Step 3: Add the minimum missing fixture cases**

- add only the confirmed non-duplicate case or cases
- keep `scripts/evaluate_terminal_relevance.py` unchanged unless the audit proves the harness itself is insufficient

**Step 4: Re-run focused script tests to confirm GREEN**

Run:

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- all tests pass

### Task 3: Validate The Convergence Conclusion

**Files:**
- Reference: `scripts/evaluate_terminal_relevance.py`
- Reference: `tests/services/test_terminal_sessions.py`
- Reference: `tests/app/routes/test_terminal_monitor_routes.py`
- Reference: `tests/app/routes/test_terminal_routes.py`
- Reference: `tests/app/routes/test_terminal_websocket_routes.py`
- Reference: `tests/app/routes/test_api_routes.py`

**Step 1: Re-run the offline benchmark summary**

Run:

```bash
.venv/bin/python scripts/evaluate_terminal_relevance.py --format text
```

Expected:

- if the audit is docs-only: `case_count=81`, `pass_count=81`, `pass_rate/top1_accuracy/mrr = 1.000`
- if a real gap was patched: the new case count passes at `1.000`

**Step 2: Re-run the script tests**

Run:

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- all tests pass

**Step 3: If fixture/test content changed, run the terminal-focused regression suite**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- no regressions

**Step 4: Run diff hygiene**

Run:

```bash
git diff --check
```

Expected:

- no diff hygiene errors

### Task 4: Sync Restart Notes And Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`
- Modify: `tasks/todo.md`

**Step 1: Record the audit result**

- if no gap remains, document that baseline expansion should pause until a real semantic gap, metric regression, or operator-reported ranking failure appears
- if a gap was fixed, document the exact newly covered semantics and the new case count

**Step 2: Commit planning docs**

Run:

```bash
git add docs/plans/2026-03-26-terminal-relevance-offline-baseline-convergence-audit-design.md docs/plans/2026-03-26-terminal-relevance-offline-baseline-convergence-audit.md tasks/todo.md
git commit -m "docs(plans): add offline relevance convergence audit plan"
```

Expected:

- planning docs are committed before any fixture or handoff changes

**Step 3: Commit optional fixture/test changes only if Task 2 ran**

Run:

```bash
git add tests/scripts/test_evaluate_terminal_relevance.py tests/fixtures/terminal_relevance_baseline.json
git commit -m "feat(terminal): expand offline relevance convergence coverage"
```

Expected:

- skip this commit entirely when the audit concludes no new case is needed

**Step 4: Commit handoff sync**

Run:

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync offline relevance convergence audit context"
```

Expected:

- restart docs reflect the new convergence decision and next-step trigger conditions
