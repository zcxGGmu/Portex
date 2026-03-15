# M7.5.3 Workspace/Room Switching UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add richer room/workspace switching UX in Web chat so users can explicitly choose workspace and room instead of relying on implicit default targeting.

**Architecture:** Keep backend untouched and implement switching entirely in frontend state/orchestration. Refactor chat store to support context snapshots keyed by workspace+room, then update `ChatPanel` to drive websocket target and message composer behavior from selected workspace/slot.

**Tech Stack:** React 19, TypeScript, Zustand, existing group/slot APIs, existing websocket route

---

### Task 1: Add Red-Stage Evidence For Context-Switch Store Contract

**Files:**
- Modify: `web/src/components/chat/ChatPanel.tsx`
- Modify: `web/src/stores/chat.ts`

**Step 1: Use a non-existent chat store context-switch method in ChatPanel**

- wire a `switchContext()` call from workspace/slot selection flow before store implementation exists.

**Step 2: Run red-stage verification**

```bash
cd web && npm run build
```

Expected: FAIL with missing store method/type errors.

**Step 3: Implement minimal context-switch store contract**

- add per-context snapshot map
- add `switchContext(contextId)` method
- preserve and restore current draft/messages/events/run state across context switches

### Task 2: Implement Workspace + Room Switching UI

**Files:**
- Modify: `web/src/components/chat/ChatPanel.tsx`
- Modify: `web/src/index.css`

**Step 1: Add workspace switching controls**

- searchable workspace selector in `Workspace Snapshot`
- selected workspace drives websocket target

**Step 2: Add room/slot switching controls**

- clickable slot list with active state
- selected slot participates in context key

**Step 3: Keep attachments/send/cancel flow stable**

- preserve `M7.5.2` attachment UX
- include room marker in prompt when non-main room is selected

### Task 3: Verify, Handoff, And Commit

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run frontend verification**

```bash
cd web && npm run lint
cd web && npm run build
```

**Step 2: Run full regression/hygiene**

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
git diff --check
```

**Step 3: Update handoff**

- mark `M7.5.3` complete
- set next entrypoint to `M7.5.4`
- record red/green and regression evidence

**Step 4: Commit**

```bash
git add docs/plans/2026-03-15-m7-5-3-workspace-switching-design.md docs/plans/2026-03-15-m7-5-3-workspace-switching.md docs/progress.md web/src/stores/chat.ts web/src/components/chat/ChatPanel.tsx web/src/index.css
git commit -m "feat(web): complete M7.5.3 workspace switching ux"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-5-3-workspace-switching.md`. Given you asked to keep going in this session, I’m executing it directly now.
