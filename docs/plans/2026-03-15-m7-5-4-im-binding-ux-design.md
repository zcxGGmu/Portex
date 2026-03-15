# M7.5.4 IM Binding UX Design

## Goal

Complete `M7.5.4` by adding IM binding UX to the Web chat shell so workspace owners can bind/unbind raw IM endpoints to the active workspace without leaving chat.

## Scope

- add IM binding read/manage card in `ChatPanel`
- list IM endpoint binding statuses for active workspace
- support bind/unbind actions for each endpoint
- honor existing owner-only backend permission boundary
- keep current message/websocket execution contracts unchanged

## Out Of Scope

- no backend API changes
- no IM channel setup/configuration wizard
- no multi-workspace bulk binding actions
- no changes to room/workspace switch protocols from `M7.5.3`
- no terminal/onboarding/mobile work

## Current Gap

`M7.5.3` provides workspace/room switching in chat, but users still cannot manage IM endpoint bindings from chat. Binding APIs already exist (`/groups/{group_id}/bindings/im...`) and are owner-only.

## Options Considered

### Option A: Add a standalone `/bindings` page

Pros:

- isolated implementation

Cons:

- does not satisfy chat-surface parity intent
- adds navigation friction for frequent binding actions

Reject.

### Option B: Add IM binding card inside chat shell (recommended)

Pros:

- keeps binding operations near active workspace context
- reuses current group selection from `M7.5.3`
- minimal scope with existing APIs

Cons:

- adds one more operator card in chat side panel

Recommendation: choose this option.

### Option C: Implicit auto-bind only, no explicit UX

Pros:

- least UI work

Cons:

- does not satisfy `M7.5.4` requirement for binding UX

Reject.

## Recommended Design

### 1. Frontend API Surface

Add typed client methods/hooks:

- `GET /groups/{group_id}/bindings/im`
- `PUT /groups/{group_id}/bindings/im/{im_jid}`
- `DELETE /groups/{group_id}/bindings/im/{im_jid}`

Model returned binding status in frontend types for deterministic rendering.

### 2. Chat Shell Card

In right-side shell cards, add `IM Bindings` panel:

- show per-endpoint summary (`im_jid`, `channel`, `binding_state`, target/fallback)
- for owner:
  - `Bind Here` for endpoints not bound to current workspace
  - `Unbind` for endpoints bound to current workspace
- for non-owner:
  - show “owner only” note, no actions

### 3. Action Semantics

- bind action: call `PUT` and refetch binding list
- unbind action: call `DELETE` and refetch binding list
- keep local error/notice text in card
- disable actions while request is in flight or run is currently active

### 4. Permission Handling

Backend returns `403` for non-owner. Frontend should avoid noisy errors:

- non-owner path does not auto-query binding list
- show clear owner-only explanation

### 5. Preserve Existing Contracts

No changes to:

- chat websocket payloads
- attachment upload flow
- workspace/room context switch store model

## Verification Plan

- red evidence: reference new binding hook in `ChatPanel` before hook implementation and run `cd web && npm run build` expecting failure
- green:
  - `cd web && npm run lint`
  - `cd web && npm run build`
- regression:
  - `.venv/bin/pytest -o addopts='' -q`
  - `.venv/bin/ruff check .`
  - `git diff --check`

## Completion Signal

`M7.5.4` is complete when:

- chat shell includes functional IM binding card
- owner can bind/unbind endpoints for active workspace
- non-owner gets explicit owner-only UX
- verification passes and handoff advances to `M7.5.5`
