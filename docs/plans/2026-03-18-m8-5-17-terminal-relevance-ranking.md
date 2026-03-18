# M8.5.17 Terminal Relevance Ranking Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refine the default `relevance` ordering for terminal history search so stronger textual matches outrank merely newer results, without changing the current search API, UI, or compatibility boundaries.

**Architecture:** Keep the current terminal history search contract intact and only replace the backend `relevance` ranking branch inside `TerminalSessionService`. Compute a deterministic ranking tuple from the already-available match offsets and transcript length, then reuse the existing search route, pagination, and frontend behavior as regression coverage rather than expanding the surface area.

**Tech Stack:** FastAPI, Python dataclasses, pytest, Ruff, React 19, TypeScript, Vite

---

### Task 1: Add Failing Service Tests For Relevance Heuristics

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Reference: `services/terminal_sessions.py`
- Reference: `tests/app/routes/test_terminal_routes.py`
- Reference: `tests/app/routes/test_api_routes.py`

**Step 1: Write the failing test**

Add focused service tests that assert:

- equal `match_count` results prefer smaller `cluster_span`
- when `cluster_span` is tied, earlier `first_match_offset` wins
- weak recency only decides near-ties, not clearly better textual matches
- pagination still slices the fully ranked `relevance` result set

Example target shape:

```python
page = await service.search_history_by_group("project-alpha", query="error", limit=10, offset=0)
assert [item.record.session_id for item in page.items] == [
    concentrated.session_id,
    earlier.session_id,
    newer_but_sparse.session_id,
]
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- FAIL because current `relevance` still uses `match_count`, then recency

**Step 3: Write minimal implementation**

Add the smallest backend-only relevance metadata and ranking logic needed to satisfy the new ordering.

Keep these unchanged:

- public search API
- route signatures
- snippet generation
- `newest` / `oldest` sort branches

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- PASS for the new relevance-focused service coverage

**Step 5: Commit**

```bash
git add tests/services/test_terminal_sessions.py services/terminal_sessions.py
git commit -m "feat(terminal): refine M8.5.17 relevance ranking"
```

### Task 2: Verify Search Contract Regressions Stay Green

**Files:**
- Reference: `tests/app/routes/test_terminal_monitor_routes.py`
- Reference: `tests/app/routes/test_terminal_routes.py`
- Reference: `tests/app/routes/test_terminal_websocket_routes.py`
- Reference: `tests/app/routes/test_api_routes.py`

**Step 1: Run focused terminal regression**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS with no search-route, OpenAPI, or terminal-surface regressions

**Step 2: Run frontend/lint/diff hygiene regression**

Run:

```bash
cd web && npm run lint
cd web && npm run build
.venv/bin/ruff check .
git diff --check
```

Expected:

- PASS with no frontend, lint, or diff-hygiene regressions even though this milestone is backend-only

**Step 3: Commit if follow-up fixes were required**

```bash
git add <any additional files touched while stabilizing regressions>
git commit -m "fix(terminal): stabilize M8.5.17 relevance ranking regressions"
```

Only commit this step if focused verification required extra code changes beyond Task 1.

### Task 3: Run Full Verification And Sync Restart Docs

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`
- Modify: `tasks/todo.md`

**Step 1: Run full backend verification**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
```

Expected:

- PASS on the full backend suite

**Step 2: Update handoff docs**

Record in `docs/progress.md`, `AGENTS.md`, and the active `tasks/todo.md` session section:

- `M8.5.17` scope and behavior
- latest verification evidence
- next suggested post-`M8.5.17` refinement

**Step 3: Commit**

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync M8.5.17 relevance ranking context"
```
