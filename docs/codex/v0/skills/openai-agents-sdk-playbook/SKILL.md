---
name: openai-agents-sdk-playbook
description: Use when building, migrating, or debugging Python agent systems with OpenAI Agents SDK, especially when designing Agent/Runner flows, streaming events, tools/MCP integrations, handoffs, guardrails, and tracing in production services.
---

# OpenAI Agents SDK Playbook

## Overview
Use this skill to design and implement production-grade Python services on top of OpenAI Agents SDK.
Prioritize a stable platform contract: SDK internals stay behind an adapter layer, while API/WS contracts remain stable for clients.

## Workflow

### Step 1: Define the run contract first
Define a platform-level run contract before coding:
1. Input envelope: `tenant_id`, `user_id`, `session_id`, `request_id`, `message`.
2. Output envelope: `final_output`, `status`, `error`, `usage`, `timestamps`.
3. Event envelope: `event_type`, `event_version`, `run_id`, `seq`, `payload`.

Reject direct coupling between frontend contracts and raw SDK event classes.

### Step 2: Choose Runner mode by interaction pattern
Choose one mode explicitly:
1. Use `Runner.run_streamed` for interactive chat and live UI.
2. Use `Runner.run` for async backend tasks and workers.
3. Use `Runner.run_sync` only for local scripts or tests.

Always define `max_turns`, timeout, cancellation path, and retry semantics.

### Step 3: Build AgentFactory instead of hardcoding agents
Construct agents dynamically per tenant/session:
1. Set `name`, `instructions`, `model`.
2. Attach approved `tools`.
3. Attach allowed `handoffs`.
4. Attach `input_guardrails` and `output_guardrails`.
5. Bind typed context via `RunContextWrapper`.

Never inline tenant-specific policy into random handlers.

### Step 4: Treat tools as governed runtime extensions
Register tools through a central registry:
1. Classify tools: function, hosted, MCP.
2. Validate params before invocation.
3. Enforce permission and quota checks.
4. Emit audit logs for each invocation.

Prefer small, side-effect-bounded tools over broad shell wrappers.

### Step 5: Add handoff policy controls
When using multi-agent flows:
1. Explicitly whitelist reachable target agents.
2. Define `input_filter` for handoff payload minimization.
3. Add `on_handoff` telemetry hooks.
4. Add runtime enable switches per tenant/role.

Start with manager pattern before decentralized agent routing.

### Step 6: Enforce guardrails at input and output boundaries
Implement guardrails as platform policy layers:
1. Input guardrail: prompt injection, privilege escalation, unsafe intent.
2. Output guardrail: PII leakage, policy violation, over-broad disclosure.
3. Treat tripwire triggers as terminal run states with audit events.

Do not rely on prompt wording alone for safety guarantees.

### Step 7: Normalize streaming and tracing
Map SDK stream events into stable platform events:
1. Token deltas.
2. Tool lifecycle.
3. Agent switch events.
4. Completion/failure/cancellation.

Preserve SDK tracing, then bridge trace IDs into your observability stack.

## Implementation Checklist
Use this checklist before merging:
1. Contract tests exist for run/event schemas.
2. AgentFactory is the only agent construction path.
3. Tool calls enforce authz and are auditable.
4. Guardrail hits are persisted and queryable.
5. Streaming reconnect behavior is tested.
6. Timeout/cancel/retry behavior is deterministic.
7. SDK version is pinned and changelog impact reviewed.

## References
Load these files as needed:
1. `references/openai-agents-sdk-reference.md`: condensed SDK feature map.
2. `references/portex-integration-patterns.md`: concrete Portex integration patterns.
