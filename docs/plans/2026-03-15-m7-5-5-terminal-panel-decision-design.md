# M7.5.5 Terminal Panel Decision Design

## Goal

Complete `M7.5.5` by making an explicit terminal-panel decision for Web chat parity, and by defining the execution-mode and permission boundaries before any terminal implementation.

## Scope

- make an explicit `yes/no` decision for terminal panel in current parity track
- define the minimum execution-mode boundary needed for any future terminal implementation
- define the minimum permission boundary needed for any future terminal implementation
- keep current chat send/cancel/WebSocket runtime contracts unchanged

## Out Of Scope

- no backend terminal session API in this milestone
- no frontend `xterm`/terminal UI implementation in this milestone
- no new WebSocket protocol for terminal I/O in this milestone
- no onboarding (`M7.5.6`) or mobile/PWA (`M7.5.7`) work

## Current Gap

After `M7.5.4`, `ChatPanel` already has workspace/room switching, attachments, IM bindings, and execution controls, but there is still no terminal panel.

Compared with HappyClaw, Portex currently lacks:

- dedicated terminal lifecycle service
- authenticated terminal session ownership model
- terminal-specific WebSocket message contract
- workspace-level execution-mode policy that can gate terminal access

## Options Considered

### Option A: Implement terminal panel immediately

Pros:

- closes one visible parity gap quickly

Cons:

- Portex has no terminal backend/session contract yet
- current `/ws/{group_folder}` is message-stream oriented, not terminal-session oriented
- execution mode and permission gates are not ready for safe interactive shell access

Reject.

### Option B: Defer terminal implementation and lock boundaries first (recommended)

Pros:

- satisfies `M7.5.5` requirement exactly
- avoids shipping an unsafe/incomplete interactive shell surface
- keeps `M7.5.6` onboarding work unblocked

Cons:

- terminal parity remains deferred for now

Recommendation: choose this option.

### Option C: Add a fake/read-only “terminal-like” panel

Pros:

- small frontend delta

Cons:

- does not provide real terminal capability
- may create false parity expectation

Reject.

## Recommended Decision

`M7.5.5` decision: **do not implement terminal panel in current milestone**.  
Portex keeps terminal panel deferred until backend execution/permission prerequisites are in place.

## Required Boundaries For Future Terminal Work

### 1. Execution-Mode Boundary

- terminal must only attach to an execution backend that can safely host an interactive session
- `openai_runtime` is non-terminal by definition
- `host_process` must be treated as terminal-disabled by default unless a separate hardened policy explicitly allows it
- terminal enablement must resolve from explicit workspace/runtime policy, not implicit frontend toggles

### 2. Permission Boundary

- terminal sessions must require authenticated user context
- user must pass workspace access check before terminal start/input/resize/stop
- terminal control should be restricted to elevated roles (`owner/admin`) unless a later policy explicitly expands it
- one active terminal owner per workspace/session boundary, with deterministic takeover/release semantics
- terminal actions should be auditable (at least start/stop/error)

### 3. Protocol Boundary

- terminal I/O should not be multiplexed onto current text-chat send/cancel protocol
- use a dedicated terminal channel or a clearly separated terminal message namespace
- terminal disconnect/reconnect semantics must not corrupt normal message streaming state

## M7.5.5 Delivery Choice

This milestone is **decision + boundary documentation only**:

- add design doc + implementation-plan doc
- update `docs/progress.md` to mark `M7.5.5` complete
- move next entrypoint to `M7.5.6`

## Verification Plan

- `cd web && npm run lint`
- `cd web && npm run build`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Completion Signal

`M7.5.5` is complete when:

- terminal panel decision is explicit (`defer for now`)
- execution-mode and permission boundaries are documented
- progress handoff moves from `M7.5.5` to `M7.5.6`
- verification commands pass
