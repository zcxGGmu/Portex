# M7.6.5 Intentionally Unmatched Surfaces Design

## Goal

Complete `M7.6.5` by explicitly recording which HappyClaw-specific surfaces remain intentionally unmatched in Portex, and by distinguishing those from items that are merely deferred rather than rejected.

## Scope

- consolidate prior `M7.6.x` decisions into one restart-friendly unmatched-surface record
- classify each candidate as:
  - intentionally unmatched
  - deferred / still reopenable
  - already matched enough for current Portex goals
- move the parity backlog to a stable “decision track complete” state

## Out Of Scope

- no new backend or frontend implementation
- no reopening of QQ, slash-command, or richer IM artifact decisions
- no new post-`M7.6` roadmap creation
- no attempt to force terminal panel into the intentionally-unmatched bucket if it is still only deferred

## Current Gap

By `M7.6.4`, Portex has already made several individual scope decisions:

- QQ is excluded from current parity scope
- generic slash-command parity is excluded
- richer IM artifact parity is excluded

But those decisions still live in separate milestone docs. Without one consolidated record, future restarts can misread excluded items as “unfinished parity work” instead of “consciously non-targeted surfaces.”

## Candidate Surfaces

The main HappyClaw-specific surfaces still requiring classification are:

- QQ channel support
- generic IM slash-command control plane
- provider-specific richer IM artifacts
- terminal panel

## Options Considered

### Option A: Treat every remaining HappyClaw gap as intentionally unmatched

Pros:

- simplest summary

Cons:

- technically inaccurate
- would incorrectly collapse “deferred” and “rejected” into the same bucket
- risks closing off terminal work that Portex has only postponed, not refused

Reject.

### Option B: Record only the surfaces already explicitly excluded, while keeping terminal panel as deferred (recommended)

Pros:

- matches the actual decision history
- gives future Codex sessions a clean, trustworthy handoff
- preserves space for terminal work to reopen if backend prerequisites are later met

Cons:

- requires slightly more nuanced wording than a flat “everything unmatched is excluded”

Recommendation: choose this option.

### Option C: Leave `M7.6.5` implicit and rely on earlier docs

Pros:

- no extra summarization work

Cons:

- defeats the purpose of `M7.6.5`
- keeps restart context fragmented across multiple docs

Reject.

## Recommended Decision

`M7.6.5` decision: the following HappyClaw-specific surfaces are **intentionally unmatched** in current Portex scope:

- QQ channel parity
- generic IM slash-command parity
- provider-specific richer IM artifact parity

The following surface is **deferred but not intentionally unmatched**:

- terminal panel

## Intentionally Unmatched List

### 1. QQ Channel Parity

Status: **intentionally unmatched**

Reason:

- high integration cost
- low leverage versus Portex's retained channels
- explicitly excluded in `M7.6.1`

### 2. Generic IM Slash-Command Control Plane

Status: **intentionally unmatched**

Reason:

- duplicates Web/operator management surfaces
- would create a second control plane inside message text
- explicitly excluded in `M7.6.3`

### 3. Provider-Specific Rich IM Artifacts

Status: **intentionally unmatched**

Reason:

- weak reuse across providers
- high maintenance relative to value
- explicitly excluded in `M7.6.4`

## Deferred But Reopenable

### Terminal Panel

Status: **deferred, not intentionally unmatched**

Reason:

- `M7.5.5` documented a boundary-first defer decision
- the current blocker is missing backend/session/policy prerequisites, not a product-scope rejection
- future work may reopen terminal implementation if those prerequisites become explicit milestones

This distinction matters: terminal is not in the same category as QQ or slash-command parity.

## What This Means For Future Work

### 1. These Excluded Surfaces Should Not Reappear As Implicit TODOs

Unless a future product decision explicitly reopens them, the following should stay out of active implementation planning:

- QQ support
- generic slash-command framework
- richer IM artifact parity

### 2. Future Reopens Must Be Explicit

If any excluded surface is reconsidered later, it should return through:

- a new design decision
- a new milestone
- explicit rationale for why the current exclusion no longer holds

### 3. Terminal Work Follows A Different Rule

Terminal work may still return through a future backend/policy milestone without contradicting `M7.6.5`, because it was deferred rather than rejected.

## Delivery Choice

This milestone is **decision + documentation only**:

- add design doc + implementation-plan doc
- update `docs/progress.md` to mark `M7.6.5` complete
- note that the current parity-decision track is exhausted

## Verification Plan

- `cd web && npm run lint`
- `cd web && npm run build`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Completion Signal

`M7.6.5` is complete when:

- the intentionally unmatched list is explicit
- terminal is clearly separated as deferred instead of rejected
- progress handoff reflects that the current `M7` parity decision track is complete
- verification commands pass
