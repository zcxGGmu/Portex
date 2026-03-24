# Terminal Relevance Offline Baseline Realistic Edge Expansion Implementation Plan

**Goal:** Expand offline terminal relevance coverage from 8 to 12 deterministic cases so mid-chain ranking behavior is represented before any post-`M8.5.51` tie-break work is considered.

**Architecture:** Keep production ranking logic unchanged. Reuse the existing benchmark harness and only extend fixture data, fixture-aware script tests, and restart-oriented progress notes.

**Tech Stack:** Python 3.11, pytest, JSON fixtures, `TerminalSessionService` benchmark harness

---

### Task 1: Add RED Expectations For The Expanded Baseline

**Files:**
- Modify: `tests/scripts/test_evaluate_terminal_relevance.py`
- Reference: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Update fixture expectations**

- change case-count assertions from `8` to `12`
- assert the expanded case IDs include the new realistic-edge scenarios

**Step 2: Run focused script tests to confirm RED**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- failure because the committed fixture still has 8 cases

### Task 2: Expand The Offline Fixture

**Files:**
- Modify: `tests/fixtures/terminal_relevance_baseline.json`

**Step 1: Add wrapper-marker family ladder coverage**

- add `(error): ...`, `{error}: ...`, `<error>: ...`, and a lower-rank plain exact-tag comparator

**Step 2: Add single-space separator quality coverage**

- add clean single-space output
- add later non-single-space noise
- add earlier non-single-space noise

**Step 3: Add exact-tag punctuation-noise cleanliness coverage**

- add clean exact-tag output versus tighter-wrapper punctuation noise

**Step 4: Add `M8.5.49` pagination coverage**

- add later/earlier `other-leading whitespace payload` samples plus a lower-rank comparator
- keep explicit `limit`/`offset` slicing in the fixture

**Step 5: Re-run focused script tests to confirm GREEN**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- all tests pass

### Task 3: Validate The Expanded Baseline

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

- `case_count=12`, `pass_count=12`, `pass_rate=1.000`, `top1_accuracy=1.000`, `mrr=1.000`

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

**Step 1: Record the expanded baseline context**

- update the current baseline case count and metrics
- note the newly covered realistic-edge paths
- keep the next-step guidance as “use baseline evidence before any new tie-break”

**Step 2: Commit the completed task**

```bash
git add tests/scripts/test_evaluate_terminal_relevance.py tests/fixtures/terminal_relevance_baseline.json docs/plans/2026-03-24-terminal-relevance-offline-baseline-realistic-edge-expansion-design.md docs/plans/2026-03-24-terminal-relevance-offline-baseline-realistic-edge-expansion.md docs/progress.md tasks/todo.md
git commit -m "feat(terminal): expand offline relevance realistic edge fixtures"
```
