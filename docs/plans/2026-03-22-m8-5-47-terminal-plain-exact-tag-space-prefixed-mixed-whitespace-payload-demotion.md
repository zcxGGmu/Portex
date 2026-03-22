# M8.5.47 Terminal Plain Exact-Tag Space-Prefixed Mixed-Whitespace Payload Demotion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a narrow backend-only `relevance` refinement so snapshots with clean single-space plain exact-tag hits prefer fewer space-prefixed mixed-whitespace payload plain exact-tag separators.

**Architecture:** Keep route/API/frontend contracts unchanged and only extend `TerminalSessionService` internal search-candidate metadata. Add one conditional mixed-whitespace payload count derived from existing exact-tag helpers, inject it into the `relevance` tuple immediately after the `M8.5.46` multi-space-payload-offset key, and preserve all compatibility boundaries.

**Tech Stack:** FastAPI, Python dataclasses, pytest, Ruff, React 19, TypeScript, Vite

---

### Task 1: Add Failing Service Tests For Space-Prefixed Mixed-Whitespace Payload Tie-Break

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Reference: `services/terminal_sessions.py`
- Reference: `docs/plans/2026-03-22-m8-5-47-terminal-plain-exact-tag-space-prefixed-mixed-whitespace-payload-demotion-design.md`

**Step 1: Write failing tests**

Add focused tests that assert:

- when stronger signals tie, snapshots with fewer space-prefixed mixed-whitespace payload plain exact-tag separators rank ahead
- when no single-space plain exact-tag exists, ordering falls back to existing `M8.5.46` behavior
- pagination still slices globally ordered results after the new tie-break

**Step 2: Run to confirm RED**

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -k "mixed_whitespace_payload or no_single_space_plain_exact_tag" -q
```

Expected:

- at least one new test fails before implementation

### Task 2: Implement Minimal Space-Prefixed Mixed-Whitespace Payload Metadata And Sort Key

**Files:**
- Modify: `services/terminal_sessions.py`
- Modify: `tests/services/test_terminal_sessions.py`

**Step 1: Extend internal candidate metadata**

Add one field to `_TerminalSessionHistorySearchCandidate`:

- `conditional_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match_count`

**Step 2: Add mixed-whitespace payload helper logic**

Add helper(s):

- `_is_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match(...)`
- `_count_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_hits(...)`

Rules:

- only non-marker exact-tag hits are eligible
- exclude existing single-space, payloadless, tab-prefixed payload, and multi-space payload forms
- the first separator character after the closing wrapper must be ASCII space
- the second separator position must be whitespace but not ASCII space
- at least one non-whitespace payload character must appear before newline/end

**Step 3: Wire `_build_search_candidate(...)`**

Compute conditional mixed-whitespace payload count:

- when `line_start_plain_exact_tag_single_space_separator_match_count > 0`, use the count
- otherwise use `0`

**Step 4: Update `relevance` tuple only**

Insert:

- `item.conditional_line_start_plain_exact_tag_space_prefixed_mixed_whitespace_payload_match_count`

Placement:

- immediately after `-item.conditional_first_line_start_plain_exact_tag_multi_space_payload_offset`
- before `item.conditional_non_exact_tag_punctuation_wrap_match_count`

Keep:

- existing wrapper/marker ordering
- `newest`/`oldest` untouched

**Step 5: Run RED -> GREEN**

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py -k "mixed_whitespace_payload or no_single_space_plain_exact_tag" -q
```

Expected:

- all new tests pass

**Step 6: Commit feature changes**

```bash
git add services/terminal_sessions.py tests/services/test_terminal_sessions.py docs/plans/2026-03-22-m8-5-47-terminal-plain-exact-tag-space-prefixed-mixed-whitespace-payload-demotion-design.md docs/plans/2026-03-22-m8-5-47-terminal-plain-exact-tag-space-prefixed-mixed-whitespace-payload-demotion.md
git commit -m "feat(terminal): add M8.5.47 mixed whitespace payload demotion"
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

- `M8.5.47` scope and commit IDs
- latest verification evidence
- immediate next small backend-only relevance refinement suggestion

**Step 2: Commit handoff docs**

```bash
git add docs/progress.md AGENTS.md
git commit -m "docs(handoff): sync M8.5.47 mixed whitespace payload context"
```
