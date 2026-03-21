# M8.5.39 Terminal Plain Exact-Tag Single-Space Separator Preference Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a narrow backend-only `relevance` refinement so plain exact-tag hits with a single-space separator after the closing wrapper gain explicit quality preference within the existing non-marker exact-tag branch.

**Architecture:** Keep route/API/frontend contracts unchanged and only extend `TerminalSessionService` internal search-candidate metadata. Reuse the existing exact-tag and exact-tag-marker helpers, add one plain exact-tag separator-quality signal (plus earliest offset if needed), inject it into the current `relevance` tuple after the wrapper-specific plain chain, and preserve all other ranking families and compatibility boundaries.

**Tech Stack:** FastAPI, Python dataclasses, pytest, Ruff, React 19, TypeScript, Vite

---

### Task 1: Add Failing Service Tests For Plain Exact-Tag Single-Space Preference

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Reference: `services/terminal_sessions.py`
- Reference: `docs/plans/2026-03-21-m8-5-39-terminal-plain-exact-tag-single-space-separator-preference-design.md`

**Step 1: Write the failing tests**

Add focused tests that assert:

- when stronger signals are tied, single-space plain exact-tag hits outrank multi-space or tab-separated plain exact-tag hits
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.38` signals
- pagination still slices the globally ranked result set after the new preference

**Step 2: Run the service suite to confirm RED**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- at least one new test fails because current `relevance` does not include plain exact-tag single-space separator quality metadata

### Task 2: Implement Minimal Plain Exact-Tag Separator-Quality Metadata And Sort Keys

**Files:**
- Modify: `services/terminal_sessions.py`
- Modify: `tests/services/test_terminal_sessions.py`

**Step 1: Extend internal candidate metadata**

Add fields to `_TerminalSessionHistorySearchCandidate`:

- `line_start_plain_exact_tag_single_space_separator_match_count`
- `first_line_start_plain_exact_tag_single_space_separator_offset`

Add one sentinel constant:

- `_NO_LINE_START_PLAIN_EXACT_TAG_SINGLE_SPACE_SEPARATOR_MATCH_OFFSET`

**Step 2: Add separator-quality helper/count**

Implement:

- `_is_line_start_plain_exact_tag_single_space_separator_match(...)`
- `_count_line_start_plain_exact_tag_single_space_separator_hits(...)`

Rules:

- must satisfy existing line-start exact-tag conditions
- must not be exact-tag marker
- the character after the closing wrapper must be `" "`
- the next character must exist and must not be whitespace

**Step 3: Wire `_build_search_candidate(...)`**

Compute the new separator-quality count/offset tuple and populate candidate metadata.

**Step 4: Update `relevance` tuple only**

Insert the new keys in `sort="relevance"`:

- `-item.line_start_plain_exact_tag_single_space_separator_match_count` after the existing plain wrapper-specific count chain
- `item.first_line_start_plain_exact_tag_single_space_separator_offset` after the existing plain wrapper-specific offset chain

Keep:

- existing plain wrapper family count/offset placement
- `newest` and `oldest` untouched

**Step 5: Run RED -> GREEN**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -q
```

Expected:

- all service tests pass, including new plain exact-tag separator-quality focused tests

**Step 6: Commit feature changes**

```bash
git add services/terminal_sessions.py tests/services/test_terminal_sessions.py
git commit -m "feat(terminal): add M8.5.39 plain exact-tag single-space preference"
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

- `M8.5.39` scope and commit IDs
- latest verification evidence
- next post-`M8.5.39` backend-only refinement suggestion

**Step 3: Commit docs sync**

```bash
git add docs/progress.md AGENTS.md tasks/todo.md
git commit -m "docs(handoff): sync M8.5.39 plain exact-tag single-space context"
```
