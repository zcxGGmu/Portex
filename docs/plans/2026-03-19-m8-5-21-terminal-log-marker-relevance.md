# M8.5.21 Terminal Log-Marker Relevance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refine default terminal-history `relevance` ordering so line-start `query:` and strict `query -` marker results outrank plain line-start whole-word results without changing the current search API, UI, snippets, or compatibility boundaries.

**Architecture:** Keep the current terminal history search contract intact and only extend the backend `relevance` candidate metadata inside `TerminalSessionService`. Reuse the existing whole-word and line-start signals to derive two narrow marker-aware signals from already matched offsets, then reuse the existing search route, pagination, and frontend behavior as regression coverage rather than expanding the surface area.

**Tech Stack:** FastAPI, Python dataclasses, pytest, Ruff, React 19, TypeScript, Vite

---

### Task 1: Add Failing Service Tests For Log-Marker Ordering

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Reference: `services/terminal_sessions.py`
- Reference: `docs/plans/2026-03-19-m8-5-21-terminal-log-marker-relevance-design.md`

**Step 1: Write the failing test**

Add focused service tests that assert:

- line-start `query:` / strict `query -` results outrank plain line-start whole-word results when broader strength is otherwise similar
- when marker counts tie, earlier `first_line_start_log_marker_offset` wins
- when neither snapshot has a marker hit, ordering falls back to the existing `M8.5.20` relevance signals
- pagination still slices the fully ranked `relevance` result set after the new ordering is applied

Example target shape:

```python
page = await service.search_history_by_group("project-alpha", query="error", limit=10, offset=0)
assert [item.record.session_id for item in page.items] == [
    marker_style.session_id,
    plain_line_start.session_id,
]
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- FAIL because current `relevance` does not distinguish line-start marker-style hits from plain line-start hits

**Step 3: Commit the RED state only if you intentionally keep a separate checkpoint**

Normally skip committing the failing state. Keep the worktree dirty and move straight to the minimal implementation.

### Task 2: Implement Minimal Log-Marker Relevance Signals

**Files:**
- Modify: `services/terminal_sessions.py`
- Modify: `tests/services/test_terminal_sessions.py`

**Step 1: Add the smallest internal metadata needed**

Extend the internal search candidate metadata in `services/terminal_sessions.py` with:

- `line_start_log_marker_match_count`
- `first_line_start_log_marker_offset`

Use a local helper that evaluates already-matched offsets as marker hits only when they already satisfy the current line-start whole-word rule and are immediately followed by either `:` or strict ` -`.

Example target helper shape:

```python
@staticmethod
def _count_line_start_log_marker_hits(text: str, offsets: list[int], *, query_length: int) -> tuple[int, int]:
    marker_offsets = [
        offset
        for offset in offsets
        if TerminalSessionService._is_line_start_log_marker_match(text, offset, query_length=query_length)
    ]
    if not marker_offsets:
        return 0, _NO_LINE_START_LOG_MARKER_MATCH_OFFSET
    return len(marker_offsets), marker_offsets[0]
```

**Step 2: Update only the `relevance` sort branch**

Keep `newest` and `oldest` unchanged.

Update the `relevance` sort tuple to:

```python
(
    -item.match.match_count,
    -item.line_start_log_marker_match_count,
    -item.line_start_whole_word_match_count,
    item.conditional_non_line_start_whole_word_match_count,
    -item.whole_word_match_count,
    item.first_line_start_log_marker_offset,
    item.first_line_start_whole_word_offset,
    item.first_whole_word_offset,
    item.cluster_span,
    item.first_match_offset,
    -item.match_density,
    -item.match.snapshot_at.timestamp(),
    item.match.record.session_id,
)
```

**Step 3: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- PASS for the new marker-focused service coverage

**Step 4: Commit**

```bash
git add tests/services/test_terminal_sessions.py services/terminal_sessions.py
git commit -m "feat(terminal): add M8.5.21 log-marker relevance"
```

### Task 3: Verify Search Contract Regressions Stay Green

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
git commit -m "fix(terminal): stabilize M8.5.21 log-marker regressions"
```

Only commit this step if focused verification required extra code changes beyond Task 2.

### Task 4: Run Full Verification And Sync Restart Docs

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

- `M8.5.21` scope and behavior
- latest verification evidence
- next suggested post-`M8.5.21` search-quality refinement

**Step 3: Commit**

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync M8.5.21 log-marker relevance context"
```
