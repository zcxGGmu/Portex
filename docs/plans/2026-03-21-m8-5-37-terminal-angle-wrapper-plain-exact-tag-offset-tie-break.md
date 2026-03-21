# M8.5.37 Terminal Angle-Wrapper Plain Exact-Tag Offset Tie-Break Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a narrow backend-only `relevance` refinement so angle-wrapper plain exact-tag quality (`<query> text`) has explicit earliest-offset tie-break behavior within the existing non-marker exact-tag branch.

**Architecture:** Keep route/API/frontend contracts unchanged and only extend `TerminalSessionService` internal search-candidate metadata. Reuse the existing angle plain exact-tag detection helper, add one first-offset field for that branch, inject it into the current `relevance` tuple near the paren/brace plain-wrapper offsets, and preserve all other ranking families and compatibility boundaries.

**Tech Stack:** FastAPI, Python dataclasses, pytest, Ruff, React 19, TypeScript, Vite

---

### Task 1: Add Failing Service Tests For Angle Plain Exact-Tag Offset Tie-Break

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Reference: `services/terminal_sessions.py`
- Reference: `docs/plans/2026-03-21-m8-5-37-terminal-angle-wrapper-plain-exact-tag-offset-tie-break-design.md`

**Step 1: Write the failing tests**

Add focused tests that assert:

- when stronger signals are tied, earlier angle-wrapper plain exact-tag offset wins
- when no angle-wrapper plain exact-tag exists, ordering falls back to existing `M8.5.36` signals
- pagination still slices the globally ranked result set after the new tie-break

**Step 2: Run the service suite to confirm RED**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- at least one new test fails because current `relevance` does not include angle plain exact-tag specific offset tie-break metadata

### Task 2: Implement Minimal Angle Plain Exact-Tag Offset Metadata And Sort Key

**Files:**
- Modify: `services/terminal_sessions.py`
- Modify: `tests/services/test_terminal_sessions.py`

**Step 1: Extend internal candidate metadata**

Add one field to `_TerminalSessionHistorySearchCandidate`:

- `first_line_start_angle_wrapper_plain_exact_tag_offset`

Add one sentinel constant:

- `_NO_LINE_START_ANGLE_WRAPPER_PLAIN_EXACT_TAG_MATCH_OFFSET`

**Step 2: Update angle plain count helper**

Change `_count_line_start_angle_wrapper_plain_exact_tag_hits(...)` to return:

- count
- first offset

Rules:

- must satisfy existing line-start exact-tag conditions
- must not be exact-tag marker
- wrapper pair must be `<>`

Keep `_is_line_start_angle_wrapper_plain_exact_tag_match(...)` unchanged.

**Step 3: Wire `_build_search_candidate(...)`**

Compute the new angle plain count/offset tuple and populate candidate metadata.

**Step 4: Update `relevance` tuple only**

Insert the new key in `sort="relevance"`:

- `item.first_line_start_angle_wrapper_plain_exact_tag_offset` after brace plain offset

Keep:

- existing `item.line_start_angle_wrapper_plain_exact_tag_match_count` ascending placement
- `newest` and `oldest` untouched

**Step 5: Run RED -> GREEN**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- all service tests pass, including new angle plain focused tests

**Step 6: Commit feature changes**

```bash
git add services/terminal_sessions.py tests/services/test_terminal_sessions.py
git commit -m "feat(terminal): add M8.5.37 angle plain exact-tag offset tie-break"
```

### Task 3: Run Focused Regression Verification

**Files:**
- Reference: `tests/app/routes/test_terminal_monitor_routes.py`
- Reference: `tests/app/routes/test_terminal_routes.py`
- Reference: `tests/app/routes/test_terminal_websocket_routes.py`
- Reference: `tests/app/routes/test_api_routes.py`

**Step 1: Run terminal-focused regression suite**

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- pass with no terminal-route contract regressions

**Step 2: Run lint/build hygiene checks**

```bash
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- all checks pass

### Task 4: Run Full Verification And Sync Handoff Docs

**Files:**
- Modify: `docs/progress.md`
- Modify: `AGENTS.md`
- Modify: `tasks/todo.md`

**Step 1: Run full backend verification**

```bash
.venv/bin/pytest -o addopts='' -q
```

Expected:

- full backend suite passes

**Step 2: Update restart/handoff docs**

Record:

- `M8.5.37` scope and commit IDs
- latest verification evidence
- next post-`M8.5.37` backend-only refinement suggestion

**Step 3: Commit docs sync**

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync M8.5.37 angle plain exact-tag offset context"
```
