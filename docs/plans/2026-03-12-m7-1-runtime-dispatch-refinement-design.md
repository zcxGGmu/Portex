# M7.1 Runtime Dispatch Refinement Design

## Goal

Refine `M7.1` into the smallest honest implementation path that closes the current IM inbound -> runtime -> outbound gap without dragging browser WebSocket execution or execution-plane lifecycle redesign into scope.

## Scope

- keep the existing browser WebSocket happy path unchanged for this phase
- add a structured runtime-result path that can be consumed outside WebSocket broadcasting
- introduce a thin dispatch service for normalized inbound messages
- replace the `/messages` placeholder with real dispatch behavior
- add minimal app-level Feishu and Telegram ingestion routes
- add outbound Telegram text reply support and reuse the existing Feishu send path
- persist enough inbound/outbound metadata to correlate one inbound message, one run, and one outbound reply
- add focused tests plus one integration slice for the end-to-end runtime chain

## Out Of Scope

- do not fold the browser WebSocket flow into the new dispatch service
- do not redesign queueing, runtime selection, or lifecycle management; that remains `M7.2`
- do not finalize the long-term workspace/group mapping model; that remains `M7.3`
- do not add file panels, monitor pages, MCP management, or broader operator surfaces
- do not add non-text Telegram outbound delivery, retries, or production-grade delivery guarantees

## Current Constraints

- [app/routes/messages.py](/home/zq/work-space/repo/ai-projs/posp/Portex/app/routes/messages.py) is still a queued placeholder
- [services/message_service.py](/home/zq/work-space/repo/ai-projs/posp/Portex/services/message_service.py) only persists `chat_jid/sender/content/is_from_me/timestamp`
- [services/agent_trigger.py](/home/zq/work-space/repo/ai-projs/posp/Portex/services/agent_trigger.py) only streams serialized runtime events to a broadcaster and returns `run_id`
- [infra/runtime/mapper.py](/home/zq/work-space/repo/ai-projs/posp/Portex/infra/runtime/mapper.py) emits `run.completed`, but no app-facing service currently consumes it as a structured final result
- [infra/im/feishu.py](/home/zq/work-space/repo/ai-projs/posp/Portex/infra/im/feishu.py) already supports inbound normalization and outbound sending
- [infra/im/telegram.py](/home/zq/work-space/repo/ai-projs/posp/Portex/infra/im/telegram.py) supports inbound normalization but outbound sending is still explicitly unimplemented

## Options Considered

### Option A: Build dispatch directly on top of the current string-broadcast trigger helper

Pros:

- smallest diff around the current runtime trigger code

Cons:

- couples IM dispatch to the WebSocket serialization contract
- forces the dispatch service to parse broadcasted strings just to recover final status/output
- likely to be rewritten during `M7.2`

Reject.

### Option B: Add a structured runtime-result path first, then layer dispatch and IM adapters on top

Pros:

- keeps runtime concerns separate from transport concerns
- lets IM dispatch reuse the existing execution path without depending on WebSocket-specific broadcasting
- keeps `M7.1` narrow while making `M7.2` easier later

Cons:

- first implementation step is not a route change; it is a runtime-contract refinement

Recommendation: choose this option.

### Option C: Keep Web on `run_streamed`, but create a separate IM-only runtime invocation path

Pros:

- could make IM final-output handling simpler in the short term

Cons:

- introduces two runtime semantics in one repository
- expands scope and increases long-term maintenance cost

Reject.

## Recommended Design

### 1. Structured Runtime Result Boundary

Refine [services/agent_trigger.py](/home/zq/work-space/repo/ai-projs/posp/Portex/services/agent_trigger.py) so it can do both:

- keep streaming events to a broadcaster for the current WebSocket flow
- return a structured runtime result for non-WebSocket callers

Add a narrow collector abstraction that consumes `RunEvent` objects directly and records:

- `run.started`
- `run.completed`
- `run.failed`
- `run.timeout`
- `final_output` when present

This must remain transport-agnostic. The collector should not parse JSON strings or depend on room broadcasting.

### 2. Thin Dispatch Service

Add [services/message_dispatch.py](/home/zq/work-space/repo/ai-projs/posp/Portex/services/message_dispatch.py) as the orchestration boundary for normalized inbound messages.

Responsibilities:

- accept a `UnifiedMessage`
- reject non-text / empty-content IM payloads with an explicit dispatch error or benign no-op result
- resolve the effective `group_folder`
- persist the inbound message plus correlation metadata
- invoke the runtime through the new structured-result path
- build an outbound `UnifiedMessage` from the final runtime output
- route the outbound message to the real channel handler
- persist the outbound reply

This service must not own queueing, executor selection, or workspace lifecycle.

### 3. Temporary Target Resolution

Keep the `M7.3` boundary explicit by isolating a temporary resolver rule:

- if `UnifiedMessage.group_folder` is present, use it
- otherwise derive a stable temporary folder from `chat_jid`

This rule should be injected or isolated in one helper so `M7.3` can replace it cleanly later.

### 4. Minimal Persistence Expansion

Do not create a new audit subsystem. Extend existing message persistence just enough to support `M7.1` correlation:

- direction (`inbound` / `outbound`) can continue to map to `is_from_me`
- store `run_id`
- store channel
- store `group_folder`
- optionally store external `message_id`

The current `messages` table is already the smallest plausible place for this metadata.

### 5. Real Outbound Channel Handlers

Keep [services/message_router.py](/home/zq/work-space/repo/ai-projs/posp/Portex/services/message_router.py) thin, but wire it to real handlers:

- Feishu -> existing `send_message()`
- Telegram -> new minimal outbound text helper
- Web -> keep existing WebSocket path unchanged for now; no need to route browser flow through dispatch in `M7.1`

### 6. Minimal App-Level IM Adapters

Add one FastAPI route module for IM ingestion:

- Feishu webhook endpoint
- Telegram update-ingest endpoint

Both routes should:

- normalize provider payloads via the existing client helpers
- no-op benign unsupported update families
- hand normalized messages to the dispatch service

They do not need to become a production polling or bot-management subsystem in this phase.

### 7. `/messages` Stops Being a Placeholder

Update [app/routes/messages.py](/home/zq/work-space/repo/ai-projs/posp/Portex/app/routes/messages.py) to dispatch through the real service instead of returning a synthetic queued acknowledgement.

For `M7.1`, `/messages` can remain a thin authenticated HTTP entrypoint over the same dispatch boundary used by IM adapters.

## Data Flow

1. Feishu / Telegram payload enters an app-owned adapter route
2. Existing provider helper normalizes it to `FeishuMessageEvent` / `TelegramMessageEvent`
3. Event converts to `UnifiedMessage`
4. Dispatch service resolves target and stores inbound metadata
5. Dispatch service invokes the current runtime through the structured collector path
6. Final runtime result becomes an outbound `UnifiedMessage`
7. `MessageRouter` selects the real provider send handler
8. Dispatch service stores outbound metadata

The current browser WebSocket flow remains unchanged in `M7.1`.

## Risks And Boundaries

- If the dispatch service starts coordinating follow-up turns, queueing, or workspace lifecycle, the work has crossed into `M7.2` / `M7.3`
- The runtime result contract should stay minimal: status, run_id, final_output, and error/timeout detail are enough for this phase
- Telegram outbound support should remain text-only and narrow
- Non-text inbound IM payloads should not silently become empty runtime prompts

## Expected Deliverables

- a refined runtime-result contract in `services/agent_trigger.py`
- a new `services/message_dispatch.py`
- expanded message persistence metadata
- real `/messages` dispatch
- app-level Feishu and Telegram ingest routes
- minimal Telegram outbound text sending
- focused tests plus one integration flow
