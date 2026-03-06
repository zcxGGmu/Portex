# M2.5.3 Cancel Button Design

## Background

`M2.5.1` added runtime-side cancel support and `M2.5.2` added service-side timeout orchestration. The remaining gap in `M2.5.3` is the actual user-facing cancel path: the frontend needs a running-state-aware cancel button, and the WebSocket route needs to understand both message sends and cancel control frames.

Current state:
- `web/src/components/chat/ChatPanel.tsx` still sends plain text and assumes the WebSocket route is an echo endpoint.
- `app/routes/websocket.py` still echoes incoming text to the room and does not call `trigger_agent_execution()`.
- `web/src/stores/chat.ts` has no `isRunning` or `activeRunId`.

## Goals

- Keep normal chat send behavior simple: user messages continue to go over WebSocket as raw text.
- Add a structured cancel control frame over the same WebSocket connection.
- Restrict the first version to “the page that started the run can cancel its own active run”.
- Surface running state in the chat store so the UI can disable send and enable cancel deterministically.

## Non-Goals

- No HTTP cancel endpoint in this phase.
- No cross-tab or cross-connection shared cancel state.
- No new `run.cancelled` contract in this phase.
- No refactor of `services/agent_trigger.py` or `infra/runtime/openai.py` beyond reuse.

## Protocol

### Outbound send

Normal user messages remain raw text:

```text
hello
```

### Outbound cancel

Cancellation uses a JSON control frame:

```json
{
  "type": "cancel",
  "run_id": "abc123"
}
```

The backend treats any non-JSON text frame as a user message and only interprets a parsed JSON object with `type === "cancel"` as a control frame.

## Backend Design

### WebSocket route responsibilities

`app/routes/websocket.py` becomes the orchestration boundary for one WebSocket connection:

- create one `OpenAIAgentsRuntime` instance per connection
- keep `active_run_id` and `active_task` in endpoint-local state
- on raw text: generate a `request_id`, launch `trigger_agent_execution(...)` in a background task, and keep the loop free to receive cancel frames
- on cancel control frame: if the requested `run_id` matches the connection's active run, call `runtime.cancel(run_id)`

### Cleanup

On disconnect:
- disconnect the socket from `ConnectionManager`
- if there is an active run, call `runtime.cancel(active_run_id)`
- if there is an active background task, cancel/await it to avoid leaks

## Frontend Design

### Store changes

`web/src/stores/chat.ts` will add:
- `isRunning: boolean`
- `activeRunId: string | null`
- `clearRunState(): void`

`addStreamEvent()` becomes the single event-state reducer:
- `run.started` → set running state
- `run.completed` / `run.failed` / `run.timeout` → clear running state

`clearMessages()` also clears running state.

### UI changes

`web/src/components/chat/ChatPanel.tsx` will:
- read `isRunning` and `activeRunId` from the store
- block duplicate sends while a run is active
- add `handleCancel()` that sends the JSON control frame over the same socket
- clear local run state immediately after sending cancel so the button state resets even though there is no dedicated `run.cancelled` event yet
- continue mapping `run.completed`, `run.failed`, and `run.timeout` to assistant-visible status messages

## Testing Strategy

### Backend

Replace the old echo-oriented route test with:
- one route test that proves a raw text frame launches `trigger_agent_execution()` instead of echoing the text
- one route test that proves a cancel control frame calls `runtime.cancel()` for the active run on the same socket

### Frontend

Keep frontend verification lightweight:
- `npm run lint`
- `npm run build`

The store/UI changes are small and there is no existing dedicated frontend test harness to extend.

## Risks

- Because cancel is connection-local, a second browser tab in the same room cannot cancel the first tab’s active run. This is intentional scope control for `M2.5.3`.
- Clearing local run state immediately after sending cancel is a pragmatic workaround until a first-class `run.cancelled` event exists.

## Recommended Next Step

After `M2.5.3`, the next high-value cleanup would be to add an explicit `run.cancelled` event so manual cancellation and timeout can both be modeled as terminal backend-driven states.
