# M7.6.4 Richer IM Artifacts Scope Decision Design

## Goal

Complete `M7.6.4` by deciding whether Portex needs HappyClaw-style richer IM artifacts parity, and by freezing the current answer as: **do not add provider-specific rich IM artifact parity to the current Portex roadmap**.

## Scope

- make an explicit `include/exclude` decision for richer IM artifact parity
- document the rationale against Portex's current retained channels and product direction
- define what narrow future exception remains acceptable
- move the next real parity entrypoint to `M7.6.5`

## Out Of Scope

- no Feishu rich-card implementation
- no Feishu reaction/typing reaction implementation
- no Telegram long-message chunking implementation
- no richer IM media/formatting redesign
- no broader intentionally-unmatched inventory beyond this slice (`M7.6.5`)

## Current Gap

HappyClaw's IM layers go beyond minimal inbound/outbound messaging. Representative richer artifact behaviors include:

- Feishu interactive card rendering
- Feishu reaction feedback and typing-state reactions
- Telegram long-message chunking beyond simple send
- provider-specific formatting/rendering behaviors that optimize for each channel

Portex currently remains intentionally narrow:

- Feishu sends the minimal message payload through `send_message()`
- Telegram sends a minimal HTML-converted text payload through `send_text_message()`
- earlier Portex milestones explicitly avoided cards, reactions, and long-message chunking

That makes `M7.6.4` a scope decision about whether Portex should stay on that minimal boundary.

## Options Considered

### Option A: Add richer IM artifact parity

Pros:

- narrows one visible product gap versus HappyClaw
- gives IM users a more platform-native reply experience

Cons:

- highly provider-specific work with low cross-channel reuse
- reopens formatting, lifecycle, and testing complexity for each retained channel
- shifts focus away from Portex's core runtime/workspace/operator product value

Reject.

### Option B: Exclude richer IM artifact parity, keep minimal provider adapters (recommended)

Pros:

- matches Portex's current architecture and milestone history
- keeps IM channels as bounded ingress/egress surfaces rather than product-specific experience stacks
- avoids a high-maintenance class of features with weak shared abstractions

Cons:

- Portex remains intentionally less polished than HappyClaw inside some IM channels

Recommendation: choose this option.

### Option C: Selectively copy one provider-specific enhancement now

Pros:

- looks like a small parity win

Cons:

- creates arbitrary, hard-to-defend scope asymmetry
- starts provider-specific UX work without a broader product decision

Reject.

## Recommended Decision

`M7.6.4` decision: **Portex does not include HappyClaw-style richer IM artifact parity in the current roadmap.**

The current Portex parity target remains:

- reliable message ingress/egress
- workspace/execution routing
- Web/operator surfaces as the primary management and observability plane

Provider-specific reply polish is not a current parity goal.

## Rationale

### 1. Provider-Specific Artifact Work Has Weak Reuse

Feishu cards/reactions and Telegram chunking are not instances of one shared feature. They are separate integrations with separate formatting rules, limits, delivery semantics, and failure paths.

That makes the maintenance cost high relative to the product value returned to Portex.

### 2. Portex Has Repeatedly Chosen The Minimal IM Boundary

Earlier Portex milestones already locked conservative boundaries:

- Feishu send path avoids rich card builders
- Telegram formatting stays intentionally narrow
- execution-plane work explicitly deferred provider-specific IM behaviors

`M7.6.4` should preserve those decisions instead of quietly undoing them.

### 3. Portex Is Web-First For Rich Interaction

Portex already puts its richer experience into:

- chat workspace shell
- files/memory/skills/MCP/settings pages
- monitor/usage/audit/operator surfaces
- onboarding and mobile/PWA shell

Given that product shape, duplicating polish into provider-specific IM artifacts is not the highest-value parity work.

## Allowed Future Exception

Portex may still add a future provider-specific IM enhancement only if all of the following are true:

- there is a concrete product need for a single retained channel
- the enhancement is narrow and isolated
- it does not imply a broader “full artifact parity” commitment
- its permission, fallback, and failure behavior are explicitly documented

This keeps a pragmatic escape hatch without treating cards/reactions/chunking as roadmap commitments.

## Downstream Impact

### 1. No Immediate Implementation Successor

There is no current follow-up implementation milestone for richer IM artifacts under this decision.

### 2. `M7.6.5` Now Becomes The Consolidation Step

After excluding QQ, generic slash commands, and richer IM artifacts, `M7.6.5` should consolidate those choices into one explicit “intentionally unmatched” record for future restarts.

## Delivery Choice

This milestone is **decision + documentation only**:

- add design doc + implementation-plan doc
- update `docs/progress.md` to mark `M7.6.4` complete
- move next entrypoint to `M7.6.5`

## Verification Plan

- `cd web && npm run lint`
- `cd web && npm run build`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Completion Signal

`M7.6.4` is complete when:

- richer IM artifact scope is explicit (`excluded`)
- the narrow future-exception rule is documented
- progress handoff moves from `M7.6.4` to `M7.6.5`
- verification commands pass
