# M8.5.4 Terminal History Persistence Fallback Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make terminal history reads survive process restart by persisting latest bounded history snapshots to disk.

**Architecture:** Add disk persistence helpers inside `TerminalSessionService`, persist snapshots on output/state transitions, and fall back to disk when in-memory session snapshot is unavailable.

**Tech Stack:** Python/FastAPI service layer, pytest, Ruff

---

### Task 1: Add Failing Persistence Tests

**Files:**
- Modify: `tests/services/test_terminal_sessions.py`

Steps:
1. Add test for restart-like fallback: create history in one service instance, then read in a fresh instance from persisted snapshot.
2. Keep existing not-found behavior test for missing snapshot.
3. Run `.venv/bin/pytest tests/services/test_terminal_sessions.py -q` and confirm red.

### Task 2: Implement History Persistence + Fallback

**Files:**
- Modify: `services/terminal_sessions.py`

Steps:
1. Add persistence-root config and safe path resolution.
2. Implement atomic snapshot write + snapshot read helpers.
3. Persist snapshot on output updates and terminal-state transitions.
4. Update `get_history_by_group()` to fall back to persisted snapshot.
5. Re-run `.venv/bin/pytest tests/services/test_terminal_sessions.py tests/app/routes/test_terminal_routes.py tests/app/routes/test_terminal_websocket_routes.py tests/app/routes/test_api_routes.py -q`.

### Task 3: Verify, Handoff, Commit

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

Steps:
1. Run full verification:
   - `.venv/bin/pytest -o addopts='' -q`
   - `.venv/bin/ruff check .`
   - `cd web && npm run lint`
   - `cd web && npm run build`
   - `git diff --check`
2. Update handoff/progress entries for `M8.5.4`.
3. Commit milestone and finalize checklist review.
