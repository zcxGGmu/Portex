# M7.5.4 IM Binding UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add IM binding UX in chat so owners can bind/unbind IM endpoints to the active workspace directly from the Web chat shell.

**Architecture:** Reuse existing backend group binding APIs and implement frontend-only integration. Add typed binding methods/hooks, then add one IM binding management card in `ChatPanel` that is context-aware (active workspace from `M7.5.3`) and permission-aware (owner-only operations).

**Tech Stack:** React 19, TypeScript, TanStack Query, existing `/groups/*/bindings/im` routes

---

### Task 1: Add Red-Stage Evidence For Binding API Hook Contract

**Files:**
- Modify: `web/src/components/chat/ChatPanel.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/hooks/useApi.ts`

**Step 1: Introduce binding hook usage in ChatPanel before it exists**

- reference `useGroupImBindingsQuery` in `ChatPanel`.

**Step 2: Run red-stage verification**

```bash
cd web && npm run build
```

Expected: FAIL because binding hook/method/types are missing.

**Step 3: Implement minimal binding API contracts**

- add binding response types
- add client methods for list/bind/unbind
- add binding query hook

### Task 2: Implement IM Binding Card In Chat Shell

**Files:**
- Modify: `web/src/components/chat/ChatPanel.tsx`
- Modify: `web/src/index.css`

**Step 1: Add owner-aware binding card**

- list endpoints
- show state/target metadata
- bind/unbind actions
- error/notice feedback

**Step 2: Keep context and runtime boundaries stable**

- active workspace follows existing `M7.5.3` selector
- no websocket payload/attachment flow change
- disable operations during in-flight action/run

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

- mark `M7.5.4` complete
- move next entrypoint to `M7.5.5`
- record red/green verification evidence

**Step 4: Commit**

```bash
git add docs/plans/2026-03-15-m7-5-4-im-binding-ux-design.md docs/plans/2026-03-15-m7-5-4-im-binding-ux.md docs/progress.md web/src/api/client.ts web/src/hooks/useApi.ts web/src/components/chat/ChatPanel.tsx web/src/index.css
git commit -m "feat(web): complete M7.5.4 im binding ux"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-5-4-im-binding-ux.md`. Given you asked to continue in this session, I’m executing it directly now.
