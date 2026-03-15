# M7.5.2 Web Chat Attachments Design

## Goal

Complete `M7.5.2` by adding file upload and attachment UX inside the Web chat surface so users are no longer limited to text-only submission.

## Scope

- add attachment picker/removal UX in `ChatPanel`
- upload selected files to the active workspace before sending the message
- include uploaded workspace paths in the outgoing prompt payload
- show attachment upload state/error/notice in chat
- surface recent uploaded paths in the current chat shell

## Out Of Scope

- no backend protocol changes for websocket message payload
- no binary inline message transport over websocket
- no workspace switching (`M7.5.3`)
- no IM attachment parity (`M7.5.4+`)
- no terminal/onboarding/mobile work

## Current Gap

After `M7.5.1`, chat has workspace shell context but still submits plain text only. Users must leave chat and open `/files` to upload artifacts first.

## Options Considered

### Option A: Keep chat text-only and rely on `/files`

Pros:

- zero implementation work

Cons:

- directly violates `M7.5.2`
- interrupts the chat workflow

Reject.

### Option B: Frontend-only attachment UX using existing workspace file APIs

Pros:

- no backend contract risk
- leverages existing safe upload boundary (`/groups/{group_id}/files`)
- minimal incremental change on top of `M7.5.1`

Cons:

- websocket still carries text payload with attachment references, not binary blobs

Recommendation: choose this option.

### Option C: New websocket binary attachment protocol

Pros:

- more “native” chat transport

Cons:

- large scope expansion beyond `M7.5.2`
- requires backend protocol, storage, and security redesign

Reject.

## Recommended Design

### 1. Chat Attachment Queue In Composer

Add a composer subpanel:

- `Attach Files` action with multi-file picker
- selected file list with per-item remove
- clear-all selected attachments
- upload state text and error/notice messages

### 2. Upload First, Send Second

On `Send`:

1. validate message/attachments input
2. if attachments exist, upload them to workspace path `chat-attachments/`
3. build final outgoing prompt text by appending uploaded file paths
4. send the prompt through existing websocket text channel

No changes to current websocket payload schema.

### 3. Prompt Composition Contract

When attachments exist, send:

- user text (or fallback sentence if text is empty)
- appended section:
  - `Attached workspace files:`
  - bullet list of uploaded relative paths

This keeps runtime integration with existing text-only chain while giving the agent stable file references.

### 4. Role/State Guardrails

- attachments disabled while run is active
- attachments disabled during upload
- if websocket is not open, block send
- if current user lacks write-capable role in current frontend contract, block attachment upload

### 5. Shell Integration

Show recent uploaded paths in the `Resource Dock` card to provide immediate feedback and quick context.

## Verification Plan

- red evidence: run `cd web && npm run build` after introducing attachment call-sites before implementing client method
- green verification:
  - `cd web && npm run lint`
  - `cd web && npm run build`
- regression:
  - `.venv/bin/pytest -o addopts='' -q`
  - `.venv/bin/ruff check .`
  - `git diff --check`

## Completion Signal

`M7.5.2` is complete when:

- chat supports selecting/removing multiple attachments
- send flow uploads attachments and then sends one prompt with attachment path context
- user receives clear upload state/error feedback in chat
- verification commands pass and progress handoff moves to `M7.5.3`
