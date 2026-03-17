# M8.5.12 Terminal Snippet-to-Offset Deep Link Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add snippet-level deep links so operators can jump from a search snippet directly to the matching output location in terminal history detail.

**Architecture:** Add additive snippet position metadata (`match_index`, `match_offset`, `text`) in backend search results, keep compatibility `snippets`, then wire `/terminals` to open detail at the targeted match using offset-first fallback logic.

**Tech Stack:** Python, FastAPI, Pydantic, React, TypeScript, pytest, Ruff, npm lint/build

---

### Task 1: Add Failing Backend Contract Tests

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `services/terminal_sessions.py`
- Reference: `app/routes/terminals.py`
- Reference: `domain/schemas.py`

**Step 1: Write failing tests**

Cover:

- search result exposes snippet position metadata (`match_index`, `match_offset`, `text`)
- compatibility `snippets` remains available
- route response includes `snippet_matches`
- OpenAPI schema documents new snippet response model

**Step 2: Run RED verification**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because new snippet-position contracts are not implemented yet

**Step 3: Implement minimal backend support**

Implement:

- snippet metadata dataclass + builder in `TerminalSessionService`
- additive schemas in `domain/schemas.py`
- route mapping in `app/routes/terminals.py`

**Step 4: Re-run GREEN verification**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS for the updated backend contracts

### Task 2: Implement `/terminals` Snippet Deep Link UX

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Add frontend type usage for new field**

- extend terminal search match type with `snippet_matches`

**Step 2: Implement deep-link behavior**

- render snippets as clickable controls
- clicking snippet sets detail session + pending exact target
- resolve exact target by offset, then fallback index, then clamp
- keep existing previous/next session/match navigation unchanged

**Step 3: Run frontend verification**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected:

- PASS with updated search/detail UI logic

### Task 3: Full Verification And Handoff

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Modify: `AGENTS.md`

**Step 1: Run focused terminal regression**

Run:

```bash
.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_monitor_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS for terminal-focused suite

**Step 2: Run full repository verification**

Run:

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- PASS for full regression/lint/build/hygiene

**Step 3: Update restart-oriented docs**

Record:

- `M8.5.12` scope, verification evidence, and next-step suggestion

**Step 4: Commit milestone**

Commit message:

```bash
git commit -m "feat(terminal): complete M8.5.12 snippet offset deep links"
```
