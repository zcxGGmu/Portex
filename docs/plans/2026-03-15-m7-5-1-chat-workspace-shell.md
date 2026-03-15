# M7.5.1 Chat Workspace Shell Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand the current `/chat` experience into a workspace shell that surfaces workspace context, resource entry points, and execution controls while preserving the existing text-only chat run chain.

**Architecture:** Keep the backend unchanged and implement this milestone entirely in the web layer. Extend the frontend API client/hooks for members and slots reads, then refactor `ChatPanel` into a responsive multi-zone shell that composes workspace snapshot cards, the existing message/timeline panels, and a dedicated execution-control area.

**Tech Stack:** React 19, TypeScript, TanStack Query, Zustand, Vite, FastAPI existing group endpoints

---

### Task 1: Add Frontend Data Contracts For Workspace Shell Reads

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`

**Step 1: Add failing call-sites in chat shell scaffolding**

- Start using new hooks in `ChatPanel` (`members` and `slots`) before methods exist to surface TypeScript failures.

**Step 2: Run frontend verification to confirm missing contracts fail**

Run:

```bash
cd web && npm run build
```

Expected: FAIL due to missing API client methods/types/hooks.

**Step 3: Implement minimal contracts**

- Add `GroupMemberSummary`, `GroupMemberListResponse`, `ConversationSlotSummary`, `ConversationSlotListResponse` types.
- Add API methods:
  - `getGroupMembers(token, groupId)`
  - `getGroupSlots(token, groupId)`
- Add query hooks:
  - `useGroupMembersQuery(groupId)`
  - `useGroupSlotsQuery(groupId)`

**Step 4: Re-run frontend verification**

Run:

```bash
cd web && npm run build
```

Expected: PASS for this slice.

### Task 2: Refactor ChatPanel Into Workspace Shell

**Files:**
- Modify: `web/src/components/chat/ChatPanel.tsx`
- Modify: `web/src/pages/Chat.tsx`
- Modify: `web/src/index.css`

**Step 1: Add shell structure using the new data hooks**

- Create workspace context cards:
  - workspace summary
  - slots snapshot
  - members snapshot
- Keep the existing message stream and thinking/tool panels in the center column.
- Add resource dock links and execution controls cards on the right.
- Keep message send/cancel protocol unchanged.

**Step 2: Run frontend lint/build**

Run:

```bash
cd web && npm run lint
cd web && npm run build
```

Expected: PASS with no TypeScript or lint regressions.

### Task 3: Full Regression And Handoff Update

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run feature-level and full regression verification**

Run:

```bash
cd web && npm run lint
cd web && npm run build
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
git diff --check
```

Expected: PASS.

**Step 2: Update progress/handoff state**

- Mark `M7.5.1` complete in `docs/progress.md`.
- Record verification evidence.
- Set next entrypoint to `M7.5.2`.

**Step 3: Commit milestone**

```bash
git add docs/plans/2026-03-15-m7-5-1-chat-workspace-shell-design.md docs/plans/2026-03-15-m7-5-1-chat-workspace-shell.md web/src/api/client.ts web/src/hooks/useApi.ts web/src/components/chat/ChatPanel.tsx web/src/pages/Chat.tsx web/src/index.css docs/progress.md
git commit -m "feat(web): complete M7.5.1 chat workspace shell"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-5-1-chat-workspace-shell.md`. Given你要求继续在本会话推进，我会直接按该计划执行。
