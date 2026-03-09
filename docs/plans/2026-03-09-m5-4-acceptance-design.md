# M5.4 Acceptance Design

## Goal

Complete `M5.4` by turning the finished `M5.1`–`M5.3` work into an explicit acceptance handoff: a verified checklist, evidence-backed validation results, and updated progress/TODO state that clearly marks `M5` complete and advances the project to `M6`.

## Scope

- Re-read `M5.1` through `M5.3` deliverables
- Build an acceptance matrix covering:
  - Feishu channel
  - Telegram channel
  - unified message conversion
  - minimal message routing
  - current IM integration evidence
- Run fresh verification commands
- Apply only minimal fixes if acceptance reveals small gaps
- Update `docs/progress.md`, `docs/TODO.md`, and `tasks/todo.md`

## Out of Scope

- Do not start `M6` implementation work
- Do not wire the minimal router into real send paths, API routes, or WebSocket flows
- Do not expand current in-memory / file-backed boundaries for users, tasks, logs, or memory
- Do not introduce retries, rate limiting, persistent delivery logs, or `group_folder` resolution

## Design Constraints

- Acceptance claims must be backed by fresh command output
- Existing deferred boundaries must remain visible rather than being silently “accepted away”
- The final handoff should be restart-friendly and concise

## Acceptance Options

### Option A: Pure documentation sign-off

- Use only previously recorded evidence

Pros:
- Fastest

Cons:
- Weakest confidence
- Conflicts with evidence-first workflow

### Option B: Fresh verification + minimal fixes

- Rebuild acceptance from current code and current test output
- Patch only small issues discovered during verification

Pros:
- Highest confidence without scope creep
- Produces trustworthy handoff evidence

Cons:
- Slightly slower than doc-only sign-off

### Option C: Expand into product-style IM end-to-end flows

- Add new API smoke tests, live webhook flows, or delivery behavior until acceptance feels broader

Pros:
- More surface coverage

Cons:
- Turns acceptance into feature work
- Conflicts with the current `M5` boundary

## Recommended Design

Choose **Option B**.

## Acceptance Matrix

### M5.1 Feishu Channel

Verify:
- tenant access token fetch
- webhook signature / decrypt helpers
- inbound event normalization
- outbound send contract

### M5.2 Telegram Channel

Verify:
- Bot API update polling
- inbound message normalization
- Markdown-to-HTML conversion
- current explicit non-support for send path

### M5.3 Unified Message and Routing

Verify:
- `UnifiedMessage` schema / timestamp normalization
- Feishu and Telegram to-unified conversion
- `MessageRouter` channel dispatch behavior
- unknown-channel error and downstream exception propagation

### Current IM Integration Evidence

Use the existing Feishu / Telegram / unified-message / router test suite as the integration evidence for this milestone; do not invent new runtime wiring while `app/routes/messages.py` and WebSocket message entrypoints remain intentionally unintegrated.

## Expected Deliverables

- `docs/progress.md` marks `M5.4` complete and `M6.1.1` as the next starting point
- `docs/TODO.md` reflects `M5.4` completion state and `M5` completion overall
- `tasks/todo.md` records the acceptance session checklist and evidence
- verification commands and outputs are refreshed
- acceptance exceptions remain explicitly documented as deferred risk notes
