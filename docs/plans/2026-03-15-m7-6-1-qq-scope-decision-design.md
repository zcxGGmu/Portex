# M7.6.1 QQ Scope Decision Design

## Goal

Complete `M7.6.1` by making an explicit decision that QQ is **not** part of the current Portex parity scope, and by documenting the downstream milestone implications of that choice.

## Scope

- make an explicit `include/exclude` decision for QQ parity
- document the rationale against the current Portex product direction and implementation state
- define what this decision means for `M7.6.2`
- move the next real parity entrypoint to `M7.6.3`

## Out Of Scope

- no QQ backend/client implementation
- no QQ settings/config APIs or UI
- no slash-command decision work (`M7.6.3`)
- no richer IM artifact decision work (`M7.6.4`)
- no broader “what remains intentionally unmatched” inventory beyond the QQ slice (`M7.6.5`)

## Current Gap

After `M7.5.7`, Portex has reached a stable `Web + Feishu + Telegram` baseline with execution, workspace, operator, onboarding, and mobile/PWA surfaces in place. The parity backlog still leaves one unresolved product-scope question before more channel/ecosystem work can proceed: whether HappyClaw’s QQ support is a true Portex parity target or only a reference feature.

HappyClaw’s QQ support is not a thin adapter. It includes:

- dedicated QQ Bot API v2 connection/runtime handling
- private chat and group `@Bot` semantics
- pairing/binding flows
- outbound reply handling
- image-message handling
- user-facing QQ configuration surfaces

That makes `M7.6.1` a real scope decision, not a naming cleanup.

## Options Considered

### Option A: Include QQ in Portex parity scope

Pros:

- narrows one visible ecosystem gap versus HappyClaw
- preserves the possibility of “all major reference channels” parity

Cons:

- adds a large new channel surface after Portex already has a stable three-surface baseline
- requires new auth, connection, routing, pairing, media, and settings work
- pulls time away from more reusable product decisions in `M7.6.3` ~ `M7.6.5`

Reject.

### Option B: Exclude QQ from current Portex parity scope (recommended)

Pros:

- keeps parity focused on the channels Portex already supports: Web, Feishu, Telegram
- avoids importing a high-maintenance channel with distinct product and operational semantics
- lets `M7.6` continue as ecosystem-boundary documentation instead of reopening a large integration program

Cons:

- Portex remains intentionally short of HappyClaw’s QQ feature set

Recommendation: choose this option.

### Option C: Leave QQ undecided

Pros:

- defers commitment

Cons:

- keeps `M7.6.2` blocked
- weakens the purpose of `M7.6.1`
- leaves future milestone planning ambiguous

Reject.

## Recommended Decision

`M7.6.1` decision: **QQ is intentionally excluded from the current Portex parity scope.**

Portex treats HappyClaw’s QQ channel as reference-only functionality, not a required parity target for the current roadmap.

## Rationale

### 1. Portex’s Stable Channel Baseline Is Already Sufficient

Portex now has a coherent baseline around:

- Web chat
- Feishu ingress/egress
- Telegram ingress/egress

These channels already exercise the shared message-routing, workspace-binding, execution, and operator-management surfaces that matter most to Portex’s architecture.

### 2. QQ Would Reopen A Large Integration Surface

To add QQ with real parity, Portex would need more than another adapter:

- QQ credential/config lifecycle
- QQ connection/runtime management
- pairing/binding workflows
- C2C and group `@Bot` handling
- outbound reply and image semantics
- new test coverage across all of the above

That is disproportionate to the current roadmap value.

### 3. Portex Is A Python + OpenAI Agents SDK Rewrite, Not A Promise To Clone Every HappyClaw Surface

The parity backlog exists to identify meaningful product gaps, not to force one-to-one duplication of every HappyClaw ecosystem feature. Excluding QQ here is consistent with `M7.6`’s purpose: make deliberate product-scope decisions about what remains reference-only.

## Downstream Impact

### 1. `M7.6.2` Becomes Not Applicable In The Current Roadmap

`M7.6.2` starts with “If QQ is in scope...”.  
Because `M7.6.1` excludes QQ, that milestone does not proceed unless a future product decision reopens QQ.

### 2. `M7.6.3` And `M7.6.4` Still Matter

Slash-command and richer IM-artifact decisions remain relevant for the channels Portex does keep:

- Feishu
- Telegram
- Web where applicable

Those decisions should now be evaluated without QQ as a hidden dependency.

### 3. `M7.6.5` Should Record QQ As An Intentional Non-Parity Surface

When Portex writes the broader intentionally-unmatched list, QQ should be listed as:

- considered
- explicitly excluded
- excluded because it is not a worthwhile parity target for the current Portex roadmap

## Delivery Choice

This milestone is **decision + documentation only**:

- add design doc + implementation-plan doc
- update `docs/progress.md` to mark `M7.6.1` complete
- move next entrypoint to `M7.6.3`
- note that `M7.6.2` is not applicable under the current decision

## Verification Plan

- `cd web && npm run lint`
- `cd web && npm run build`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Completion Signal

`M7.6.1` is complete when:

- QQ scope is explicit (`excluded`)
- the rationale and downstream effect on `M7.6.2` are documented
- progress handoff moves from `M7.6.1` to `M7.6.3`
- verification commands pass
