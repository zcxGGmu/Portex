# M8.5.25 Terminal Exact-Tag Marker Relevance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refine default terminal-history `relevance` ordering so wrapper exact-tag marker hits such as `[query]: text` and `[query] - text` outrank plain exact-tag wrapper hits such as `[query] text`, while preserving the existing API/UI/history compatibility boundaries.

**Architecture:** Keep the current terminal history search contract intact and only extend the backend `relevance` candidate metadata inside `TerminalSessionService`. Reuse the existing exact-tag wrapper signal and already-matched offsets to derive one additional exact-tag-marker signal family from the text immediately after the closing wrapper, then reuse the current search route, pagination, and frontend behavior as regression coverage rather than expanding the surface area.

**Tech Stack:** FastAPI, Python dataclasses, pytest, Ruff, React 19, TypeScript, Vite

---

### Task 1: Add Failing Service Tests For Exact-Tag Marker Ordering

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Reference: `services/terminal_sessions.py`
- Reference: `docs/plans/2026-03-20-m8-5-25-terminal-exact-tag-marker-relevance-design.md`

**Step 1: Write the failing test**

Add focused service tests that assert:

- exact-tag marker hits such as `[query]: text` outrank plain exact-tag wrapper hits such as `[query] text`
- when exact-tag marker counts tie, earlier `first_line_start_exact_tag_marker_offset` wins
- when neither snapshot has an exact-tag marker hit, ordering falls back to the existing `M8.5.24` raw-marker + exact-tag signals
- pagination still slices the fully ranked `relevance` result set after the new ordering is applied

Example target shape:

```python
page = await service.search_history_by_group("project-alpha", query="error", limit=10, offset=0)
assert [item.record.session_id for item in page.items] == [
    exact_tag_marker.session_id,
    plain_exact_tag.session_id,
]
```

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- FAIL because current `relevance` does not distinguish exact-tag marker hits from plain exact-tag wrapper hits

**Step 3: Commit the RED state only if you intentionally keep a separate checkpoint**

Normally skip committing the failing state. Keep the worktree dirty and move straight to the minimal implementation.

### Task 2: Implement Minimal Exact-Tag Marker Relevance Signals

**Files:**
- Modify: `services/terminal_sessions.py`
- Modify: `tests/services/test_terminal_sessions.py`

**Step 1: Add the smallest internal metadata needed**

Extend the internal search candidate metadata in `services/terminal_sessions.py` with:

- `line_start_exact_tag_marker_match_count`
- `first_line_start_exact_tag_marker_offset`

Use a local helper that evaluates already-matched offsets as exact-tag marker hits only when they already satisfy the current line-start exact-tag rule and the closing wrapper is immediately followed by either:

- `:` followed by end-of-output or whitespace
- strict ` -` followed by end-of-output or whitespace

Example target helper shape:

```python
@staticmethod
def _count_line_start_exact_tag_marker_hits(
    text: str,
    offsets: list[int],
    *,
    query_length: int,
) -> tuple[int, int]:
    marker_offsets = [
        offset
        for offset in offsets
        if TerminalSessionService._is_line_start_exact_tag_marker_match(
            text,
            offset,
            query_length=query_length,
        )
    ]
    if not marker_offsets:
        return 0, _NO_LINE_START_EXACT_TAG_MARKER_MATCH_OFFSET
    return len(marker_offsets), marker_offsets[0]
```

**Step 2: Update only the `relevance` sort branch**

Keep `newest` and `oldest` unchanged.

Update the `relevance` sort tuple to:

```python
(
    -item.match.match_count,
    -item.line_start_log_marker_match_count,
    -item.line_start_delimited_log_marker_match_count,
    -item.line_start_exact_tag_marker_match_count,
    -item.line_start_exact_tag_match_count,
    -item.line_start_punctuation_wrap_match_count,
    -item.line_start_whole_word_match_count,
    item.conditional_non_line_start_whole_word_match_count,
    -item.whole_word_match_count,
    item.first_line_start_log_marker_offset,
    item.first_line_start_delimited_log_marker_offset,
    item.first_line_start_exact_tag_marker_offset,
    item.first_line_start_exact_tag_offset,
    item.first_line_start_punctuation_wrap_offset,
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

- PASS for the new exact-tag-marker-focused service coverage

**Step 4: Commit**

```bash
git add tests/services/test_terminal_sessions.py services/terminal_sessions.py
git commit -m "feat(terminal): add M8.5.25 exact-tag marker relevance"
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
git commit -m "fix(terminal): stabilize M8.5.25 exact-tag marker regressions"
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

- `M8.5.25` scope and behavior
- latest verification evidence
- next suggested post-`M8.5.25` search-quality refinement

**Step 3: Commit**

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync M8.5.25 exact-tag marker relevance context"
```
