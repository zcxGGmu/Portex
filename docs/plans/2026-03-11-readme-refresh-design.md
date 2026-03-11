# README Refresh Design

## Goal

Refresh the public project entrypoint so `README.md` explains what Portex is, why it exists, and what it currently supports, while staying truthful to the current codebase. Add a Chinese counterpart README without exposing internal milestone numbering.

## Context

- The current `README.md` is accurate, but it reads like an internal milestone handoff.
- The public README currently exposes `M...` task IDs that are only useful inside the repo workflow.
- The current README has no visual explanation of the architecture or the active runtime flow.
- The user requested:
  - a Portex naming explanation: `Portal + Codex`
  - removal of internal `Mxxx` task IDs from the public README
  - architecture and workflow diagrams
  - a Chinese counterpart README, with English remaining primary

## Constraints

- Public docs must be honest about the current implementation boundary.
- Diagrams must reflect the current code, not aspirational architecture.
- `README.md` remains English-first.
- The Chinese README should stay close to the English structure to reduce drift.
- Internal workflow docs can still be linked, but should not dominate the public narrative.

## Options Considered

### Option A: Full layered README refresh plus bilingual counterpart

- Rewrite `README.md` as a product-facing entrypoint.
- Add `README.zh-CN.md` as a near-parity Chinese mirror.
- Add Mermaid diagrams directly in the README.

Pros:

- Best first impression for new readers
- Satisfies all user requirements in one pass
- Keeps English and Chinese docs aligned

Cons:

- Larger doc edit surface
- Requires careful wording to avoid overstating readiness

### Option B: Minimal patch on the current README

- Keep the current README mostly intact.
- Remove `M...` references and add a short naming section plus one diagram.

Pros:

- Smallest diff
- Lowest maintenance cost

Cons:

- The README would still read like internal handoff material
- Weakest response to the user's request for a more attractive README

### Option C: Keep README short and push detail into separate docs

- Turn the README into a short landing page.
- Move diagrams and deeper explanations into separate architecture docs.

Pros:

- Clean top-level README
- Easy to maintain over time

Cons:

- Fails the user's explicit request to improve the README itself
- Adds an extra click for the most important project context

## Decision

Choose Option A.

`README.md` will become a layered public entrypoint, and `README.zh-CN.md` will mirror the same information architecture in Chinese.

## Approved Structure

### `README.md`

1. Language switch to the Chinese README
2. Project pitch and naming story: `Portex = Portal + Codex`
3. `Why Portex`
4. `What Works Today`
5. `What's Next`
6. `Architecture`
   - system architecture diagram
   - web run/stream/cancel workflow diagram
   - IM normalization/routing boundary diagram
7. `Quick Start`
8. `Developer Workflow`
9. `Repository Map`
10. `Current Boundaries`
11. `Documentation`

### `README.zh-CN.md`

- Mirror the English README structure closely
- Keep English/Chinese language switch links at the top
- Use the same Mermaid topology so the diagrams do not drift semantically

## Diagram Scope

### System architecture

Show the current repo-level relationship between:

- React web app
- FastAPI app
- service layer
- OpenAI Agents runtime
- SQLite / file-backed memory
- Feishu / Telegram integration modules
- separate agent-runner slice

### Web chat workflow

Show the current truthful runtime path:

- browser chat UI
- WebSocket endpoint
- `trigger_agent_execution()`
- `OpenAIAgentsRuntime`
- OpenAI Agents SDK streaming
- event stream back to the browser
- cancel path

### IM routing boundary

Show only the currently implemented normalization boundary:

- Feishu payload -> `FeishuMessageEvent`
- Telegram update -> `TelegramMessageEvent`
- both -> `UnifiedMessage`
- `MessageRouter` dispatch boundary

This diagram must not imply that `/messages` is already a real end-to-end delivery chain.

## Content Rules

- Do not mention `M0`, `M6.5.3`, or any other internal task numbering in public-facing sections.
- Replace internal status framing with a public support matrix:
  - currently supported
  - next planned capabilities
- Keep current caveats, but compress them into clearer grouped boundaries.
- Keep deployment/API links available without making internal handoff docs the main call to action.

## Verification Plan

- `rg -n "M[0-9]" README.md README.zh-CN.md` should return no matches
- `git diff --check` should pass
- Repository regression commands should still pass after the doc change:
  - `.venv/bin/pytest -o addopts='' -q`
  - `.venv/bin/ruff check .`
  - `cd web && npm run lint`
  - `cd web && npm run build`
