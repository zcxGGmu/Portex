# M8.5.50 Terminal Plain Exact-Tag Other-Leading Mixed-Whitespace Payload Demotion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a narrow backend-only `relevance` refinement so snapshots with clean single-space plain exact-tag hits prefer fewer other-leading mixed-whitespace payload plain exact-tag separators.

**Architecture:** Keep route/API/frontend contracts unchanged and only extend `TerminalSessionService` internal search-candidate metadata. Add one conditional other-leading mixed-whitespace payload count derived from existing other-leading payload predicates, inject it into the `relevance` tuple ahead of the existing `M8.5.49` other-leading offset key, and preserve all compatibility boundaries.

**Tech Stack:** FastAPI, Python dataclasses, pytest, Ruff, React 19, TypeScript, Vite

---

### Task 1: Add Failing Service Tests For Other-Leading Mixed-Whitespace Payload Tie-Break

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Reference: `services/terminal_sessions.py`
- Reference: `docs/plans/2026-03-22-m8-5-50-terminal-plain-exact-tag-other-leading-mixed-whitespace-payload-demotion-design.md`

**Step 1: Write failing tests**

Add focused tests that assert:

- when stronger signals tie, snapshots with fewer other-leading mixed-whitespace payload plain exact-tag separators rank ahead
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.49` behavior
- pagination still slices globally ordered results after the new tie-break

**Step 2: Run to confirm RED**

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -k "other_leading_mixed_whitespace_payload" -q
```

Expected:

- at least one new test fails before implementation

### Task 2: Implement Minimal Other-Leading Mixed-Whitespace Payload Metadata And Sort Key

**Files:**
- Modify: `services/terminal_sessions.py`
- Modify: `tests/services/test_terminal_sessions.py`

**Step 1: Extend internal candidate metadata**

Add one field to `_TerminalSessionHistorySearchCandidate`:

- `conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count`

**Step 2: Add other-leading mixed-whitespace payload helper logic**

Add helper(s):

- `_is_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match(...)`
- `_count_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_hits(...)`

Rules:

- start from existing other-leading payload predicate
- require second separator character to exist and be whitespace
- keep all current exclusions and compatibility boundaries

**Step 3: Wire `_build_search_candidate(...)`**

Compute conditional other-leading mixed-whitespace payload count:

- when `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use the count
- otherwise use `0`

**Step 4: Update `relevance` tuple only**

Insert:

- `item.conditional_line_start_plain_exact_tag_other_leading_mixed_whitespace_payload_match_count`

Placement:

- immediately after `-item.conditional_first_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_offset`
- before `-item.conditional_first_line_start_plain_exact_tag_other_leading_whitespace_payload_offset`

Keep:

- existing wrapper/marker ordering
- `newest`/`oldest` untouched

**Step 5: Run RED -> GREEN**

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -k "other_leading_mixed_whitespace_payload" -q
```

Expected:

- all new tests pass

**Step 6: Commit feature changes**

```bash
git add services/terminal_sessions.py tests/services/test_terminal_sessions.py docs/plans/2026-03-22-m8-5-50-terminal-plain-exact-tag-other-leading-mixed-whitespace-payload-demotion-design.md docs/plans/2026-03-22-m8-5-50-terminal-plain-exact-tag-other-leading-mixed-whitespace-payload-demotion.md
git commit -m "feat(terminal): add M8.5.50 other-leading mixed-whitespace payload demotion"
```

### Task 3: Run Focused Regression Verification

**Files:**
- Reference: `tests/app/routes/test_terminal_monitor_routes.py`
- Reference: `tests/app/routes/test_terminal_routes.py`
- Reference: `tests/app/routes/test_terminal_websocket_routes.py`
- Reference: `tests/app/routes/test_api_routes.py`

**Step 1: Run terminal focused baseline**

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- pass with no terminal route/API contract regressions

**Step 2: Run full backend regression**

```bash
.venv/bin/pytest -o addopts='' -q
```

Expected:

- full backend suite passes

**Step 3: Run lint/build hygiene**

```bash
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- all checks pass

### Task 4: Sync Restart/Handoff Docs

**Files:**
- Modify: `docs/progress.md`
- Optional: `AGENTS.md` (if snapshot pointers need refresh)

**Step 1: Update progress/handoff context**

Record:

- `M8.5.50` scope and commit IDs
- latest verification evidence
- immediate next small backend-only relevance refinement suggestion

**Step 2: Commit handoff docs**

```bash
git add docs/progress.md AGENTS.md
git commit -m "docs(handoff): sync M8.5.50 mixed-other payload context"
```
