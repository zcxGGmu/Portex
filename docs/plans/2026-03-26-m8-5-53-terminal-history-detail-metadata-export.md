# M8.5.53 Terminal History Detail Metadata Export Implementation Plan

**Goal:** Extend the existing terminal history detail download path so one snapshot can be exported either as raw text or as a JSON attachment containing the full detail payload.

**Architecture:** Keep `GET /terminals/{group_id}/sessions/history/{session_id}/download` as the single snapshot-download route, add a narrow `format=text|json` query parameter that defaults to `text`, and thread that option into the frontend download action layer without touching terminal history persistence or relevance logic.

**Tech Stack:** FastAPI, Pydantic v2, Starlette responses, React 19, TypeScript, Vite, pytest, Ruff, ESLint

---

### Task 1: Add Failing Backend Route And OpenAPI Coverage

**Files:**
- Modify: `tests/app/routes/test_terminal_routes.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Reference: `app/routes/terminals.py`

**Step 1: Write the failing tests**

Add focused coverage that proves:

- default download behavior still returns raw text output and `.log`
- `?format=json` returns:
  - `200`
  - `application/json`
  - JSON body containing the existing history detail payload
  - attachment filename ending with `.json`
- missing sessions still return `404` under `format=json`
- invalid format returns `422`
- OpenAPI exposes the `format` query parameter on the download route

**Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- FAIL because the route only supports raw text today

**Step 3: Write minimal implementation**

Implement the smallest backend delta:

- add a literal `format` query parameter with default `text`
- reuse the existing snapshot lookup and detail DTO conversion
- return either `PlainTextResponse` or `JSONResponse`
- generalize the filename helper so it can emit `.log` and `.json`

**Step 4: Run test to verify it passes**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

### Task 2: Add Frontend JSON Export Wiring

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/pages/Terminals.tsx`

**Step 1: Add the failing frontend wiring**

Reference a `json` download mode from the existing history detail panel before the client helper supports it.

**Step 2: Run build to verify it fails**

Run:

```bash
cd web && npm run build
```

Expected:

- FAIL because the client/helper signatures do not yet support the extra format option

**Step 3: Write minimal implementation**

Implement:

- `downloadTerminalHistoryDetail(token, groupId, sessionId, format?)`
- generalized filename helper with configurable extension
- one shared page-level download helper
- two detail actions:
  - `Download Output`
  - `Download JSON`

Keep unchanged:

- search/detail state transitions
- match navigation
- default raw download behavior

**Step 4: Run build to verify it passes**

Run:

```bash
cd web && npm run build
```

Expected:

- PASS

### Task 3: Run Focused Verification And Sync Restart Notes

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`
- Optional: `AGENTS.md`

**Step 1: Run focused verification**

Run:

```bash
.venv/bin/pytest tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q
```

Expected:

- PASS

**Step 2: Run hygiene and frontend verification**

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

- `docs/progress.md` with `M8.5.53` scope and evidence
- `tasks/todo.md` review section
- `AGENTS.md` if the terminal snapshot summary should mention the new export mode

**Step 4: Commit**

Use the standard split if the session lands both code and restart-doc updates:

```bash
git add app/routes/terminals.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py web/src/api/client.ts web/src/pages/Terminals.tsx docs/plans/2026-03-26-m8-5-53-terminal-history-detail-metadata-export-design.md docs/plans/2026-03-26-m8-5-53-terminal-history-detail-metadata-export.md
git commit -m "feat(terminal): add M8.5.53 history detail metadata export"
```

Then sync restart docs:

```bash
git add docs/progress.md tasks/todo.md AGENTS.md
git commit -m "docs(handoff): sync M8.5.53 history detail metadata export context"
```
