# M7.5.2 Web Chat Attachments Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add file upload and attachment UX in Web chat so message submission is no longer text-only.

**Architecture:** Keep backend APIs unchanged and implement chat attachments as a frontend orchestration on top of existing workspace file upload routes. `ChatPanel` uploads selected files to `chat-attachments/` in the active workspace, then sends one websocket text prompt that includes uploaded file-path references.

**Tech Stack:** React 19, TypeScript, existing `apiClient`, Zustand chat store, existing websocket transport

---

### Task 1: Add Red-Stage Evidence For Attachment Client Wiring

**Files:**
- Modify: `web/src/components/chat/ChatPanel.tsx`
- Modify: `web/src/api/client.ts`

**Step 1: Introduce attachment call-sites in chat**

- Add attachment-send flow in `ChatPanel` that calls a not-yet-implemented chat upload client method.

**Step 2: Run red-stage verification**

Run:

```bash
cd web && npm run build
```

Expected: FAIL with missing `apiClient.uploadChatAttachments` (or equivalent missing contract) error.

**Step 3: Implement minimal upload client method**

- Add `apiClient.uploadChatAttachments(token, groupId, files)` using existing `/groups/{group_id}/files` upload route with fixed path `chat-attachments`.

### Task 2: Implement Attachment UX In ChatPanel

**Files:**
- Modify: `web/src/components/chat/ChatPanel.tsx`
- Modify: `web/src/index.css`

**Step 1: Build attachment UI and state**

- add file picker
- add selected attachment list + remove/clear actions
- add uploading/error/notice status text

**Step 2: Implement send orchestration**

- upload selected files first
- compose final prompt text with uploaded path bullets
- append user-visible attachment section in chat timeline
- keep existing websocket send/cancel payload contracts unchanged

**Step 3: Integrate with shell cards**

- show recent uploaded file paths in `Resource Dock`.

### Task 3: Verify, Handoff, And Commit

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run frontend verification**

```bash
cd web && npm run lint
cd web && npm run build
```

**Step 2: Run regression and hygiene**

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
git diff --check
```

**Step 3: Update handoff**

- mark `M7.5.2` complete
- move next entrypoint to `M7.5.3`
- record red/green evidence and verification commands

**Step 4: Commit**

```bash
git add docs/plans/2026-03-15-m7-5-2-chat-attachments-design.md docs/plans/2026-03-15-m7-5-2-chat-attachments.md docs/progress.md web/src/api/client.ts web/src/components/chat/ChatPanel.tsx web/src/index.css
git commit -m "feat(web): complete M7.5.2 chat attachments"
```

Plan complete and saved to `docs/plans/2026-03-15-m7-5-2-chat-attachments.md`. Given you chose to continue in this session, I’m executing it directly now.
