# M5.3.2 Message Routing Design

## Goal

Complete `M5.3.2` by introducing a minimal routing layer that dispatches `UnifiedMessage` objects to channel-specific handlers without pulling real send logic into scope.

## Scope

- Add a routing service in `services/message_router.py`
- Route `UnifiedMessage` by `channel`
- Support handler injection for Feishu, Telegram, and Web
- Add focused routing tests

## Out of Scope

- Do not implement real Feishu or Telegram reply sending
- Do not modify `/messages` routes or WebSocket routes
- Do not add retries, rate limiting, or logging
- Do not add database lookups or `group_folder` resolution
- Do not change the `UnifiedMessage` schema

## Options Considered

### Option A: Global function with hard-coded channel clients

- `async def route_message(message: UnifiedMessage): ...`
- Internally reaches for global Feishu/Telegram/Web dependencies

Pros:
- Smallest surface

Cons:
- Hard to test cleanly
- Couples routing to unfinished send infrastructure

### Option B: Thin router object with injected handlers

- `MessageRouter(feishu_handler=..., telegram_handler=..., web_handler=...)`
- `async route_message(message: UnifiedMessage) -> None`

Recommendation: choose this option. It keeps `M5.3.2` at the orchestration boundary, makes routing behavior trivial to test, and avoids prematurely binding the router to still-evolving channel send implementations.

### Option C: Full routing manager with retries and delivery policies

- Add routing policies, error recording, retries, and fallback behavior

Reject: this is far beyond the TODO for `M5.3.2`.

## Recommended Design

Add:

- `class MessageRouterError(RuntimeError)`
- `class MessageRouter`

`MessageRouter` constructor:

- `feishu_handler: Callable[[UnifiedMessage], Awaitable[None]]`
- `telegram_handler: Callable[[UnifiedMessage], Awaitable[None]]`
- `web_handler: Callable[[UnifiedMessage], Awaitable[None]]`

Public API:

- `async def route_message(self, message: UnifiedMessage) -> None`

### Routing rules

- `message.channel == "feishu"` -> call `feishu_handler(message)`
- `message.channel == "telegram"` -> call `telegram_handler(message)`
- `message.channel == "web"` -> call `web_handler(message)`
- Any other `channel` -> raise `MessageRouterError`

### Error handling

- Unknown channel raises `MessageRouterError`
- Downstream handler errors are not swallowed; they propagate to the caller unchanged
- Missing handlers are prevented by constructor requirements, not delayed until runtime

## Testing Strategy

Add tests covering:

- Feishu message is dispatched to Feishu handler
- Telegram message is dispatched to Telegram handler
- Web message is dispatched to Web handler
- Unknown channel raises `MessageRouterError`
- Downstream handler exceptions are propagated

## Files

- Add: `services/message_router.py`
- Add: `tests/services/test_message_router.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
