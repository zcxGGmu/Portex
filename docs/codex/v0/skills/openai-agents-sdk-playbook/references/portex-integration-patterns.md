# Portex Integration Patterns for OpenAI Agents SDK

## Pattern 1: Adapter Boundary

Use a dedicated adapter layer:
1. `AgentFactory`: build configured agents.
2. `RunnerExecutor`: own run/streamed invocation.
3. `EventMapper`: convert SDK events into Portex WS events.
4. `ResultMapper`: normalize final output and errors.

Benefit: SDK upgrades do not force frontend protocol changes.

## Pattern 2: Policy-Driven Tooling

Attach tools through policy resolution:
1. Resolve tool allowlist by tenant + role + workspace.
2. Build agent with resolved tool set.
3. Validate every tool call server-side.
4. Record tool invocation audit rows.

Benefit: model cannot bypass platform permissions.

## Pattern 3: Guardrails as Runtime Controls

Implement two guardrail layers:
1. Input guardrails for unsafe/unauthorized requests.
2. Output guardrails for data leakage and policy violations.

When tripwire is triggered:
1. End run with blocked status.
2. Emit `run.guardrail.hit` event.
3. Persist audit record and optional security alert.

## Pattern 4: Streaming UX

Use event classes that UI can render consistently:
1. `run.token.delta`
2. `run.tool.started`
3. `run.tool.completed`
4. `run.agent.switched`
5. `run.completed`
6. `run.failed`

Benefit: deterministic rendering and easier replay.

## Pattern 5: Multi-Agent Rollout

Roll out handoffs incrementally:
1. Start with a manager agent only.
2. Add one specialist agent as handoff target.
3. Enforce handoff whitelist and input filters.
4. Expand routing once telemetry quality is acceptable.

Benefit: controlled complexity growth and easier debugging.
