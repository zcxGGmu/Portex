# M8.5.52 Terminal History Detail Download Implementation Plan

**Goal:** Add a raw terminal-history download route plus a `/terminals` detail-panel download action without changing existing terminal timeline/search/detail semantics.

**Architecture:** Reuse `TerminalSessionService.get_history_snapshot_by_group(...)` as the source of truth, expose one additive `download` route that returns `text/plain` with an attachment filename, then thread that through the frontend API client and detail panel using the existing blob-download pattern from the files page.

**Tech Stack:** FastAPI, Starlette responses, React 19, TypeScript, Vite, pytest, Ruff, ESLint

---

### Task 1: Add Failing Backend Route And OpenAPI Coverage

**Files:**
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `app/routes/terminals.py`

**Step 1: Write the failing tests**

Add focused tests that assert:

- `GET /terminals/{group_id}/sessions/history/{session_id}/download` returns:
  - `200`
  - `text/plain`
  - the raw output body
  - a `Content-Disposition` attachment filename
- missing sessions still return `404`
- OpenAPI exposes the new download path with terminal-history wording and `404`

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because the download route does not exist yet

**Step 3: Write minimal implementation**

Implement the smallest backend delta:

- add one helper that builds a safe filename from `group_id` and `session_id`
- add the new route in `app/routes/terminals.py`
- reuse current terminal-role, workspace-access, and snapshot-lookup logic

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS for the new route/OpenAPI coverage

### Task 2: Add Frontend Download Wiring

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Add the failing frontend wiring**

Reference a not-yet-implemented terminal-history download client helper from the detail panel so the frontend build fails first.

**Step 2: Run build to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the new API helper is not wired yet

**Step 3: Write minimal implementation**

Implement:

- `apiClient.downloadTerminalHistoryDetail(token, groupId, sessionId)`
- one `handleDownloadDetail()` action in `web/src/pages/Terminals.tsx`
- one `Download Output` button in the history detail panel
- browser download flow using `URL.createObjectURL(...)`

Keep unchanged:

- current search/detail selection state
- search match navigation
- timeline pagination
- terminal route contracts other than the additive download path

**Step 4: Run build to verify it passes**

Run:

```bash
cd web && npm run build
```

Expected:

- PASS for the frontend wiring

### Task 3: Run Focused Verification And Sync Restart Notes

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Optional: `AGENTS.md` if the restart snapshot should mention the new milestone explicitly

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

**Step 2: Run broader regression and hygiene checks**

Run:

```bash
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
git diff --check
```

Expected:

- PASS

**Step 3: Update restart-oriented docs**

Refresh:

- `docs/progress.md` with the new `M8.5.52` scope, evidence, and next step
- `tasks/todo.md` review checklist
- `AGENTS.md` only if the top-level milestone snapshot or restart hints need the new entry

**Step 4: Commit**

```bash
git add app/routes/terminals.py web/src/api/client.ts web/src/pages/Terminals.tsx tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py docs/progress.md tasks/todo.md docs/plans/2026-03-26-m8-5-52-terminal-history-detail-download-design.md docs/plans/2026-03-26-m8-5-52-terminal-history-detail-download.md AGENTS.md
git commit -m "feat(terminal): add M8.5.52 history detail download"
```
