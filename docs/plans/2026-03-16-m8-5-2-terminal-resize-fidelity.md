# M8.5.2 Terminal Resize Fidelity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement real terminal resize propagation for container terminal sessions and align frontend resize emission with real panel size.

**Architecture:** Upgrade `DockerExecTerminalBridge` from pipe-only/no-op resize to PTY-backed resize via `TIOCSWINSZ`, keep service/route contracts unchanged, and make `TerminalPanel` emit dynamic resize updates.

**Tech Stack:** Python asyncio + FastAPI service layer, React + TypeScript, pytest, Ruff, ESLint, Vite

---

### Task 1: Add Bridge-Focused Failing Tests For TTY/Resize Behavior

**Files:**
- Add: `tests/services/test_terminal_bridge.py`

Steps:
1. Add test proving bridge start command requests interactive TTY (`docker exec -it ...`).
2. Add test proving `resize(cols, rows)` triggers PTY resize (`ioctl`) with correct dimensions.
3. Run `.venv/bin/pytest tests/services/test_terminal_bridge.py -q` and confirm red on current code.

### Task 2: Implement PTY-Backed Bridge Resize

**Files:**
- Modify: `services/terminal_bridge.py`

Steps:
1. Add PTY fd lifecycle state in `DockerExecTerminalBridge`.
2. Start docker exec with PTY slave fd and TTY flags.
3. Replace stream-forwarding with PTY output forwarding task.
4. Implement `resize(cols, rows)` using `TIOCSWINSZ` on PTY master fd.
5. Keep close path robust (fd cleanup + task cancellation + graceful container shutdown).
6. Re-run `.venv/bin/pytest tests/services/test_terminal_bridge.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_websocket_routes.py -q` and confirm green.

### Task 3: Improve Frontend Resize Emission

**Files:**
- Modify: `web/src/components/chat/TerminalPanel.tsx`

Steps:
1. Replace fixed `120x32` resize-on-ready with dynamic dims derived from transcript panel size.
2. Send resize on ready and on window resize while socket remains open.
3. Add basic throttling/dedupe so repeated identical dimensions are skipped.
4. Run `cd web && npm run lint` and `cd web && npm run build`.

### Task 4: Verification, Handoff, Commit

**Files:**
- Modify: `tasks/todo.md`
- Modify: `docs/progress.md`

Steps:
1. Run focused verification:
   - `.venv/bin/pytest tests/services/test_terminal_bridge.py tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_api_routes.py -q`
2. Run full verification:
   - `.venv/bin/pytest -o addopts='' -q`
   - `.venv/bin/ruff check .`
   - `cd web && npm run lint`
   - `cd web && npm run build`
   - `git diff --check`
3. Update restart-oriented entries in `docs/progress.md` and add review block in `tasks/todo.md`.
4. Commit with milestone-scoped message.
