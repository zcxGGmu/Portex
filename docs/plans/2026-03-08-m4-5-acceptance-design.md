# M4.5 Acceptance Design

## Goal

Complete `M4.5` by turning the finished `M4.1`–`M4.4` work into an explicit acceptance handoff: a verified checklist, evidence-backed validation results, and updated progress/TODO state that clearly marks `M4` complete and advances the project to `M5`.

## Scope

- Re-read `M4.1` through `M4.4` deliverables
- Build an acceptance matrix covering:
  - user system
  - RBAC / group member management
  - task system
  - memory system
  - multi-user isolation evidence
- Run fresh verification commands
- Apply only minimal fixes if acceptance reveals small gaps
- Update `docs/progress.md` and `docs/TODO.md`

## Out of Scope

- Do not start `M5` implementation work
- Do not add new product features unrelated to acceptance gaps
- Do not expand the current in-memory boundaries for users, tasks, logs, or memory

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

### Option C: Full product-style end-to-end expansion

- Add new smoke tests / APIs / workflows until acceptance feels “complete”

Pros:
- Broader confidence

Cons:
- Turns acceptance into new feature work

## Recommended Design

Choose **Option B**.

## Acceptance Matrix

### M4.1 User System

Verify:
- register / login / me flow
- admin user listing / update
- invite code create / list / consume

### M4.2 RBAC

Verify:
- permission templates
- permission dependency behavior
- group member management

### M4.3 Tasks

Verify:
- scheduler
- task CRUD
- task run logs

### M4.4 Memory

Verify:
- user-global `AGENTS.md`
- daily memory
- memory search
- runner memory tools

### Multi-user isolation evidence

Use existing group/user/task/memory boundaries and container mount tests as acceptance evidence; do not invent new isolation layers in this milestone.

## Expected Deliverables

- `docs/progress.md` marks `M4` complete and `M5` as the next starting point
- `docs/TODO.md` reflects `M4.5` completion state
- verification commands and outputs are refreshed
- any acceptance exceptions remain explicitly documented as deferred risk notes
