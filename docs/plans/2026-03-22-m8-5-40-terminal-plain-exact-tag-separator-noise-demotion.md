# M8.5.40 Terminal Plain Exact-Tag Separator-Noise Demotion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a narrow backend-only `relevance` refinement so snapshots that already contain clean single-space plain exact-tag hits gain an explicit tie-break against earlier non-single-space plain exact-tag separator noise.

**Architecture:** Keep route/API/frontend contracts unchanged and only extend `TerminalSessionService` internal search-candidate metadata. Reuse the existing plain exact-tag helper results, derive one conditional earliest-noise offset from those already-computed families, inject it into the current `relevance` tuple immediately after the single-space preference, and preserve all other ranking families and compatibility boundaries.

**Tech Stack:** FastAPI, Python dataclasses, pytest, Ruff, React 19, TypeScript, Vite

---

### Task 1: Add Failing Service Tests For Conditional Earliest-Noise Tie-Break

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Reference: `services/terminal_sessions.py`
- Reference: `docs/plans/2026-03-22-m8-5-40-terminal-plain-exact-tag-separator-noise-demotion-design.md`

**Step 1: Write the failing tests**

Add focused tests that assert:

- when stronger signals are tied, snapshots whose first non-single-space plain exact-tag separator noise appears later outrank snapshots whose first noise appears earlier
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.39` signals
- pagination still slices the globally ranked result set after the new tie-break

**Step 2: Run the service suite to confirm RED**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- at least one new test fails because current `relevance` does not include the conditional earliest separator-noise offset metadata

### Task 2: Implement Minimal Conditional Earliest-Noise Metadata And Sort Key

**Files:**
- Modify: `services/terminal_sessions.py`
- Modify: `tests/services/test_terminal_sessions.py`

**Step 1: Extend internal candidate metadata**

Add one field to `_TerminalSessionHistorySearchCandidate`:

- `conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset`

Add one sentinel constant:

- `_NO_LINE_START_NON_SINGLE_SPACE_PLAIN_EXACT_TAG_SEPARATOR_MATCH_OFFSET`

**Step 2: Derive the earliest non-single-space noise offset**

Compute the earliest non-single-space plain exact-tag offset only from existing non-marker plain exact-tag helper families and the current single-space separator helper.

Rules:

- if `line_start_plain_exact_tag_single_space_separator_match_count > 0` and at least one non-single-space plain exact-tag hit exists, use the earliest such offset
- otherwise use the sentinel

Do not reuse marker-family counters or offsets.

**Step 3: Wire `_build_search_candidate(...)`**

Populate candidate metadata with the new conditional earliest-noise offset field.

**Step 4: Update `relevance` tuple only**

Insert the new key in `sort="relevance"`:

- `-item.conditional_first_line_start_non_single_space_plain_exact_tag_separator_offset` after `-item.line_start_plain_exact_tag_single_space_separator_match_count`

Keep:

- existing wrapper-family plain chain
- existing single-space separator preference placement
- `newest` and `oldest` untouched

**Step 5: Run RED -> GREEN**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- all service tests pass, including new separator-noise-focused tests

**Step 6: Commit feature changes**

```bash
git add services/terminal_sessions.py tests/services/test_terminal_sessions.py
git commit -m "feat(terminal): add M8.5.40 separator-noise demotion"
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

- `M8.5.40` scope and commit IDs
- latest verification evidence
- next post-`M8.5.40` backend-only refinement suggestion

**Step 3: Commit docs sync**

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync M8.5.40 separator-noise context"
```
