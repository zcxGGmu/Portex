# Terminal Relevance Offline Evaluation Baseline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a deterministic offline benchmark baseline for terminal-history `relevance` ranking using fixed fixture cases and explicit summary metrics.

**Architecture:** Keep production routes/services unchanged. Add a repo-local evaluation script that reuses `TerminalSessionService` in a script-local harness, driven by committed JSON fixture cases. The script prints per-case results plus aggregate metrics and returns non-zero when baseline expectations fail.

**Tech Stack:** Python 3.11, pytest, FastAPI service layer (`TerminalSessionService`)

---

### Task 1: Add Failing Tests For Offline Evaluation Script

**Files:**
- Create: `tests/scripts/test_evaluate_terminal_relevance.py`
- Create: `tests/fixtures/terminal_relevance_baseline.json`
- Reference: `services/terminal_sessions.py`

**Step 1: Write failing tests**

Add focused tests that assert:

- fixture loading + validation works for baseline JSON
- evaluation computes stable metrics (`case_count`, `pass_count`, `pass_rate`, `top1_accuracy`, `mrr`)
- script `main()` returns `0` when all cases pass and `1` when a case fails

**Step 2: Run to confirm RED**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- failures before script implementation

### Task 2: Implement Offline Evaluation Script

**Files:**
- Create: `scripts/evaluate_terminal_relevance.py`
- Modify: `tests/scripts/test_evaluate_terminal_relevance.py`
- Modify: `tests/fixtures/terminal_relevance_baseline.json` (if needed by RED feedback)

**Step 1: Add fixture parser and schema validation**

Implement strict fixture decoding with clear `ValueError` on malformed input.

**Step 2: Add evaluation harness using `TerminalSessionService`**

Implement deterministic case runner:

- create sessions for each entry output
- emit outputs via script-local fake bridge
- run `search_history_by_group`
- map returned session IDs back to fixture entry IDs

**Step 3: Add metrics and report formatters**

Implement:

- per-case pass/fail
- `case_count`, `pass_count`, `pass_rate`, `top1_accuracy`, `mrr`
- text and json output modes

**Step 4: Add script CLI + exit policy**

Implement CLI options:

- `--fixture` (default baseline fixture path)
- `--format` (`text` / `json`)

Exit code:

- `0` when all cases pass
- `1` on any failure/invalid fixture

**Step 5: Run RED -> GREEN**

```bash
.venv/bin/pytest tests/scripts/test_evaluate_terminal_relevance.py -q
```

Expected:

- all new tests pass

**Step 6: Commit feature changes**

```bash
git add scripts/evaluate_terminal_relevance.py tests/scripts/test_evaluate_terminal_relevance.py tests/fixtures/terminal_relevance_baseline.json docs/plans/2026-03-22-terminal-relevance-offline-evaluation-baseline-design.md docs/plans/2026-03-22-terminal-relevance-offline-evaluation-baseline.md
git commit -m "feat(terminal): add offline relevance evaluation baseline"
```

### Task 3: Run Verification Suite

**Files:**
- Reference: `tests/services/test_terminal_sessions.py`
- Reference: `tests/app/routes/test_terminal_monitor_routes.py`
- Reference: `tests/app/routes/test_terminal_routes.py`
- Reference: `tests/app/routes/test_terminal_websocket_routes.py`
- Reference: `tests/app/routes/test_api_routes.py`

**Step 1: Run new offline baseline script**

```bash
.venv/bin/python scripts/evaluate_terminal_relevance.py --format text
```

Expected:

- all committed baseline cases pass with summary metrics

**Step 2: Run terminal focused regression**

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- no regressions

**Step 3: Run full backend + hygiene**

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- all pass

### Task 4: Sync Restart/Handoff Docs

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`

**Step 1: Update progress and next-step guidance**

Record:

- new script + fixture + tests
- verification evidence
- next step recommendation (use baseline metrics before any new tie-break change)

**Step 2: Commit handoff docs**

```bash
git add docs/progress.md AGENTS.md
git commit -m "docs(handoff): sync offline relevance evaluation baseline context"
```
