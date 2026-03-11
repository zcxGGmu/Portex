# M7.1 Main Runtime Chain Parity Design

## Goal

Define the smallest honest design that turns Portex from “DTOs + placeholder routes + direct WebSocket runtime” into a real inbound-message -> agent-run -> outbound-reply chain for the currently supported channels.

## Scope

- close the current `/messages` placeholder boundary with a real dispatch path
- keep the existing `OpenAIAgentsRuntime` as the execution engine for this phase
- wire Feishu and Telegram inbound message normalization into the same dispatch path
- add outbound reply delivery for Feishu and Telegram
- persist enough message/run metadata to correlate one inbound message, one run, and one outbound response
- add focused service tests plus at least one integration slice for the end-to-end chain

## Out Of Scope

- do not implement the full HappyClaw-style execution plane or queue lifecycle; that remains `M7.2`
- do not finalize the long-term workspace/group topology; that remains `M7.3`
- do not add QQ support; that remains `M7.6`
- do not add file panel, terminal, monitor page, skills page, MCP server page, or other operator surfaces; those remain `M7.4` and `M7.5`
- do not replace the current browser WebSocket happy path
- do not introduce production-grade retry, dead-lettering, rate limiting, or delivery guarantees

## Current State

Portex already has:

- `FeishuMessageEvent` / `TelegramMessageEvent` -> `UnifiedMessage` conversion
- a thin `MessageRouter`
- a direct WebSocket runtime trigger path built around `trigger_agent_execution()`
- minimal message persistence via `services/message_service.py`

Portex does not yet have:

- a real inbound dispatch service
- a source-of-truth target resolver for IM messages
- a way to collect final runtime output for non-WebSocket channels
- Telegram outbound reply delivery
- any app-level Feishu or Telegram ingestion endpoint

## Options Considered

### Option A: Expand `/messages` only and keep IM clients unmounted

- Make `POST /messages` real
- Keep Feishu/Telegram limited to parser/client tests

Pros:

- smallest possible code change

Cons:

- does not actually close the IM runtime gap
- still leaves Feishu and Telegram outside the real execution system

Reject.

### Option B: Add a thin dispatch service plus minimal channel ingestion adapters

- Introduce one orchestration service that accepts `UnifiedMessage`
- Add minimal Feishu and Telegram app-level ingestion entrypoints
- Reuse current runtime and current WebSocket-adjacent trigger path by swapping the broadcaster implementation

Pros:

- closes the main runtime chain without dragging in `M7.2`
- keeps the architecture testable
- preserves the current runtime stack and current channel client work

Cons:

- still uses a temporary target-resolution model until `M7.3`
- still does not solve queue/workspace lifecycle parity

Recommendation: choose this option.

### Option C: Wait for `M7.2` and `M7.3`, then do a “full parity” runtime rewrite

Pros:

- one clean large redesign

Cons:

- too much scope for one milestone
- leaves the main product gap open longer than necessary
- increases coordination risk because messaging, execution, and workspace changes all move at once

Reject.

## Recommended Design

### 1. New Dispatch Service

Add a new orchestration layer in `services/message_dispatch.py`.

Suggested responsibilities:

- accept one `UnifiedMessage`
- resolve the execution target (`group_folder`, effective `chat_jid`, dispatch channel)
- persist the inbound message
- trigger one runtime run using the existing `trigger_agent_execution()` helper
- collect final runtime output for non-WebSocket channels
- build one outbound `UnifiedMessage`
- route that outbound message to the correct channel handler
- persist the outbound reply

Suggested public API:

- `class MessageDispatchError(RuntimeError)`
- `@dataclass class ResolvedMessageTarget`
- `class MessageDispatchService`
- `async def dispatch_inbound_message(message: UnifiedMessage) -> DispatchResult`

### 2. Temporary Target Resolver Boundary

`M7.1` should not invent the final workspace model. Instead, add a minimal, explicit resolver boundary.

Suggested behavior:

- if `UnifiedMessage.group_folder` is already present, use it
- otherwise derive a deterministic temporary folder from `chat_jid`
- keep this logic isolated behind a resolver helper or injected dependency
- document clearly that `M7.3` can later replace this without rewriting the dispatch service

This keeps `M7.1` honest: the runtime chain closes, but the final workspace model is still deferred.

### 3. Runtime Reply Collector

The current `trigger_agent_execution()` helper assumes a broadcaster that consumes serialized runtime events.

Add a minimal non-WebSocket broadcaster implementation that:

- captures `run.started`
- captures `run.completed` final output
- captures `run.failed`
- captures `run.timeout`
- exposes a structured result back to the dispatch service

This allows IM-originated runs to reuse the same runtime helper without forcing `M7.1` to solve `M7.2`.

### 4. Real Outbound Handlers

Keep `MessageRouter`, but stop treating it as a purely theoretical selector.

For `M7.1`, wire it to real handlers:

- Feishu handler -> existing Feishu send API
- Telegram handler -> new Telegram outbound text send helper
- Web handler -> existing WebSocket/room broadcast path or a narrow adapter around it

The router remains thin; the change is that the handlers become real.

### 5. Minimal Channel Ingestion Adapters

Add application entrypoints for the currently supported IM channels.

Recommended minimal surface:

- one Feishu webhook route
- one Telegram update-ingest route suitable for app-level dispatch testing

This does not need to become a production polling daemon in `M7.1`. The point is to close the runtime chain through app-owned adapters, not to finish all delivery infrastructure.

### 6. Minimal Persistence

`M7.1` only needs enough persistence to observe the chain.

Persist:

- inbound message record
- outbound reply record
- run correlation identifiers

Do not expand this into a full audit or analytics subsystem yet.

## Data Flow

For Feishu / Telegram:

1. Channel-specific payload enters a minimal app adapter
2. Existing client parser normalizes it into `FeishuMessageEvent` / `TelegramMessageEvent`
3. Event converts to `UnifiedMessage`
4. Dispatch service resolves the target and stores the inbound message
5. Dispatch service runs the agent using the existing runtime helper plus a collector broadcaster
6. Dispatch service turns the final runtime result into an outbound `UnifiedMessage`
7. `MessageRouter` selects the real channel handler
8. Outbound handler sends the reply and the service stores the outbound message

For the existing browser flow:

- leave the current WebSocket path intact in `M7.1`
- optionally reuse pieces of the dispatch service only if that can be done without widening scope

## Testing Strategy

### Service-Level

Add focused tests for:

- target resolution with and without `group_folder`
- inbound message persistence
- successful runtime completion -> outbound reply dispatch
- runtime failure / timeout -> no false success reply
- correct channel handler selection
- correlation metadata propagation

### Route-Level

Add focused tests for:

- `/messages` no longer behaving like a pure placeholder
- Feishu webhook route dispatching supported message events
- Telegram update route dispatching supported message updates

### Integration

Add at least one integration slice that proves:

- normalized inbound channel payload
- dispatch service
- fake runtime completion
- outbound handler invocation

all connect correctly in one flow.

## Risks And Boundaries

- The temporary target resolver may later be replaced by `M7.3`; keep it isolated on purpose.
- The current runtime helper was built around broadcasting serialized events; the reply collector must stay minimal and not mutate the WebSocket path accidentally.
- Telegram outbound support should be added in the narrowest possible way; avoid redesigning the whole Telegram client in this milestone.
- Do not quietly smuggle queue/executor lifecycle changes into `M7.1`; if execution coordination grows beyond this design, stop and move it to `M7.2`.

## Expected Deliverables

- `docs/plans/2026-03-11-m7-1-main-runtime-chain-parity-design.md`
- `docs/plans/2026-03-11-m7-1-main-runtime-chain-parity.md`
- a new dispatch service design boundary
- minimal app-level Feishu/Telegram ingestion adapters
- real outbound handlers for the currently supported channels
- focused tests and at least one end-to-end integration slice
