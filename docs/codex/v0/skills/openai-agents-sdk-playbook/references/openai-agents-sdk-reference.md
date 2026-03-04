# OpenAI Agents SDK Reference (Condensed)

## Core Objects
1. `Agent`: instructions, model, tools, handoffs, guardrails, output type.
2. `Runner`: `run`, `run_sync`, `run_streamed`.
3. `RunResult`: final output + items + guardrail results + helpers.
4. `RunContextWrapper[T]`: typed runtime context for tools and hooks.

## Streaming Event Categories
1. Raw model stream events.
2. Run item events (messages, tool outputs, etc.).
3. Agent update events (active agent switched).

## Tools
1. Function tools: Python functions exposed to model.
2. Agent-as-tool: expose specialist agent via `as_tool`.
3. Hosted tools: provider-managed tools when available.
4. MCP tools: integrate remote tool servers via stdio/SSE/streamable HTTP.

## Handoffs
1. Configure explicit downstream agents.
2. Add handoff input filters.
3. Use handoff callbacks for telemetry and policy checks.
4. Gate handoff enablement by runtime policy.

## Guardrails
1. Input guardrails run before model action.
2. Output guardrails run before final return.
3. Tripwire should transition run into blocked state.

## Sessions and Memory
1. Use SDK sessions for short-term memory and continuation.
2. For production multi-tenant systems, keep authoritative history in platform storage.

## Tracing
1. SDK tracing is built-in.
2. Keep it enabled by default.
3. Bridge trace identifiers to platform logs/metrics.

## Model Configuration
Typical controls include:
1. temperature, top_p
2. frequency/presence penalty
3. max tokens
4. tool choice and parallel tool calls
5. reasoning and verbosity-related controls

## References
1. https://openai-agents-sdk.doczh.com/
2. https://openai-agents-sdk.doczh.com/agents/
3. https://openai-agents-sdk.doczh.com/running_agents/
4. https://openai-agents-sdk.doczh.com/streaming/
5. https://openai-agents-sdk.doczh.com/tools/
6. https://openai-agents-sdk.doczh.com/mcp/
7. https://openai-agents-sdk.doczh.com/handoffs/
8. https://openai-agents-sdk.doczh.com/guardrails/
9. https://openai-agents-sdk.doczh.com/tracing/
