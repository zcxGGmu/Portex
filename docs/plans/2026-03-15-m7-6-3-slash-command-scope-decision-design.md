# M7.6.3 Slash-Command Scope Decision Design

## Goal

Complete `M7.6.3` by deciding how much of HappyClaw's slash-command behavior should exist in Portex, and by freezing the current answer as: **do not add a generic slash-command subsystem to Portex parity scope**.

## Scope

- make an explicit `include/exclude` decision for HappyClaw-style slash-command parity
- document the rationale against Portex's current product shape
- define what narrow exception remains acceptable in the future
- move the next real parity entrypoint to `M7.6.4`

## Out Of Scope

- no IM command parser implementation
- no `/bind` `/unbind` `/new` `/clear` command support
- no Web slash command UX
- no richer IM artifact decision work (`M7.6.4`)
- no broader intentionally-unmatched inventory beyond this slice (`M7.6.5`)

## Current Gap

HappyClaw intercepts IM messages that start with `/` and routes them through a dedicated command layer. That layer is not a cosmetic extra; it changes workspace binding, session state, and chat response policy from inside IM.

Representative HappyClaw commands include:

- `/list`
- `/status`
- `/where`
- `/bind <target>`
- `/unbind`
- `/new <name>`
- `/recall`
- `/clear`
- `/require_mention`

Portex currently has none of this behavior. Messages beginning with `/` continue through the normal message/runtime flow.

## Options Considered

### Option A: Recreate HappyClaw-style generic slash-command parity

Pros:

- closes a visible behavior gap versus HappyClaw
- gives IM users a text-only management path

Cons:

- duplicates workflows Portex already exposes through Web/operator surfaces
- would reopen workspace binding, workspace creation, session reset, and response-policy decisions inside IM
- adds a new command-dispatch contract across all retained channels

Reject.

### Option B: Exclude generic slash-command parity, allow narrow future exceptions only when Web has no viable substitute (recommended)

Pros:

- matches Portex's product direction: Web-first management, IM as message ingress/egress
- avoids creating a second control plane inside chat text
- still leaves room for future channel-specific, necessity-driven commands if a real gap appears

Cons:

- Portex remains intentionally short of HappyClaw's IM command ergonomics

Recommendation: choose this option.

### Option C: Partially copy only a small slash-command subset now

Pros:

- appears to reduce parity gap quickly

Cons:

- hard to choose a subset without reopening product-boundary debates
- tends to create an unstable halfway command surface

Reject.

## Recommended Decision

`M7.6.3` decision: **Portex does not include HappyClaw-style generic slash-command parity in the current roadmap.**

Messages that begin with `/` continue to be treated as ordinary chat input unless a future milestone explicitly introduces a narrow, channel-specific command with no good Web/UI substitute.

## Rationale

### 1. Portex Already Has A Web Control Plane

Portex now exposes the important management surfaces in Web:

- workspace and slot management
- IM bindings
- settings/configuration
- operator/status views
- onboarding and mobile/PWA entry surfaces

Re-encoding those controls as IM slash commands would duplicate capability instead of closing a real product gap.

### 2. Slash Commands Would Reopen Several Settled Boundaries

A generic slash-command layer would need to decide, again:

- which commands are allowed per channel
- which commands mutate workspace bindings
- which commands mutate session state
- which commands depend on role and workspace access
- how unknown commands fall back to normal chat

That is a meaningful subsystem, not a tiny convenience wrapper.

### 3. QQ Is Already Out Of Scope

With `M7.6.1`, Portex explicitly excluded QQ from current parity scope. That removes one of the strongest reasons to preserve a text-only IM management plane, because the roadmap no longer includes the most command-heavy reference channel.

## Allowed Future Exception

Portex may still add a future IM command only if all of the following are true:

- it solves an IM-only workflow that cannot be handled reasonably in Web
- it is narrow and channel-specific
- it does not implicitly bootstrap a generic command framework
- it comes with explicit permission and routing rules

This preserves a pragmatic escape hatch without committing Portex to slash-command parity as a product goal.

## Downstream Impact

### 1. No Current Follow-Up Implementation Milestone

There is no immediate implementation successor for generic slash commands under the current decision.

### 2. `M7.6.4` Still Matters

Richer IM artifacts remain a separate decision for the channels Portex does keep:

- Feishu
- Telegram

That evaluation should happen independently of slash-command parity.

### 3. `M7.6.5` Should Record Slash Commands As Intentionally Unmatched

When Portex writes the broader intentionally-unmatched list, generic slash-command parity should be listed as:

- considered
- explicitly excluded
- excluded because Portex keeps management flows in Web rather than reintroducing them inside IM text commands

## Delivery Choice

This milestone is **decision + documentation only**:

- add design doc + implementation-plan doc
- update `docs/progress.md` to mark `M7.6.3` complete
- move next entrypoint to `M7.6.4`

## Verification Plan

- `cd web && npm run lint`
- `cd web && npm run build`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `git diff --check`

## Completion Signal

`M7.6.3` is complete when:

- slash-command scope is explicit (`generic parity excluded`)
- the narrow future exception rule is documented
- progress handoff moves from `M7.6.3` to `M7.6.4`
- verification commands pass
