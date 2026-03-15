# M7.5.5 Terminal Panel Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M7.5.5` by finalizing the terminal-panel decision and explicitly documenting execution-mode plus permission boundaries before any terminal implementation.

**Architecture:** Docs-first decision milestone. Reuse current runtime/auth contracts as evidence, compare against HappyClaw terminal behavior, then freeze a conservative Portex decision: terminal panel deferred until dedicated backend and policy boundaries exist.

**Tech Stack:** Markdown docs, current FastAPI/React contracts, existing verification command set

---

### Task 1: Confirm Current Runtime And Permission Baseline

**Files (read):**
- `web/src/components/chat/ChatPanel.tsx`
- `app/routes/websocket.py`
- `services/execution_policy.py`
- `domain/permissions.py`
- HappyClaw reference slices around terminal lifecycle

**Step 1: Capture current Portex constraints**

- no terminal backend/session manager
- WebSocket route is text-run stream oriented
- no terminal-specific auth/ownership protocol
- execution mode controls exist, but no terminal enablement contract

**Step 2: Capture parity signal**

- HappyClaw terminal is explicitly bounded by execution mode and access control
- this confirms boundary-first sequencing is necessary before UI parity

### Task 2: Publish M7.5.5 Design Decision

**Files:**
- Create: `docs/plans/2026-03-15-m7-5-5-terminal-panel-decision-design.md`

**Step 1: Write decision doc**

- decide `defer terminal panel for now`
- define future execution-mode boundary
- define future permission boundary
- keep out-of-scope clear (no terminal API/UI implementation in this slice)

### Task 3: Refresh Handoff And Verification Evidence

**Files:**
- Modify: `docs/progress.md`

**Step 1: Update progress context**

- mark `M7.5.5` complete
- record docs delivered for terminal decision
- move next entrypoint to `M7.5.6`

**Step 2: Run verification**

```bash
cd web && npm run lint
cd web && npm run build
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
git diff --check
```

### Task 4: Commit Milestone

**Step 1: Commit**

```bash
git add docs/plans/2026-03-15-m7-5-5-terminal-panel-decision-design.md docs/plans/2026-03-15-m7-5-5-terminal-panel-decision.md docs/progress.md
git commit -m "docs(web): complete M7.5.5 terminal panel decision"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-5-5-terminal-panel-decision.md`. Given you asked to continue in this session, I’m executing it directly now.
