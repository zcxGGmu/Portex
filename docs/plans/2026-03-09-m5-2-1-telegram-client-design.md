# M5.2.1 Telegram Client Design

## Goal

Complete `M5.2.1` by replacing the Telegram placeholder with a minimal async Bot API client that can long-poll updates through `getUpdates`.

## Scope

- Extend `infra/im/telegram.py`
- Add focused Telegram client tests
- Record the milestone in `docs/progress.md`
- Keep the implementation aligned with the existing Feishu client style where practical

## Out of Scope

- Do not implement `handle_update`
- Do not implement Markdown to HTML conversion
- Do not implement Telegram message sending, reply routing, long-message splitting, retries, or rate limiting
- Do not expand the generic IM abstraction beyond what this milestone needs

## Options Considered

### Option A: Minimal async HTTP client with injected transport

- Add `TelegramClientError`
- Add `TelegramClient` fields for `bot_token`, `base_url`, and injectable `http_client`
- Implement `async get_updates(...)`
- Validate Bot API response shape and raise domain error on failure

Recommendation: use this option. It matches the current Feishu testability pattern, keeps the milestone small, and leaves `M5.2.2` / `M5.2.3` room to grow without rework.

### Option B: Keep the current placeholder protocol and add one-off helper functions

- Smallest diff, but it would keep Telegram inconsistent with Feishu
- Harder to test cleanly once update normalization and reply flow arrive

Reject: too disposable for the next milestone.

### Option C: Jump directly to a fuller Telegram adapter

- Could include send/reply helpers, parse modes, update normalization, and markdown conversion

Reject: violates `docs/progress.md` for `M5.2.1`, which explicitly says to focus on the HTTP client skeleton and minimal update pull only.

## Recommended Design

Implement:

- `class TelegramClientError(RuntimeError)`
- `@dataclass(slots=True) class TelegramClient`
- `async get_updates(self, offset: int = 0, timeout: int = 60, allowed_updates: list[str] | None = None) -> list[dict[str, object]]`

### Request behavior

- Call `GET {base_url}/bot{bot_token}/getUpdates`
- Pass query params:
  - `offset`
  - `timeout`
  - `allowed_updates` only when provided
- Reuse an injected async HTTP client when supplied; otherwise create and close a temporary `httpx.AsyncClient`

### Response behavior

- Expect Telegram Bot API payload with:
  - `ok: true`
  - `result: list`
- Return the raw `result` list for now
- Raise `TelegramClientError` when:
  - `ok` is false
  - `result` is missing or not a list
  - Telegram returns a descriptive error message

This keeps `M5.2.1` focused on transport and error normalization. Update parsing belongs to `M5.2.2`.

## Testing Strategy

Add `tests/infra/im/test_telegram.py` covering:

- successful `get_updates()` request shape and returned list
- forwarding of `offset`, `timeout`, and `allowed_updates`
- Telegram error payload mapped to `TelegramClientError`
- malformed payload without a list `result` mapped to `TelegramClientError`

## Files

- Modify: `infra/im/telegram.py`
- Add: `tests/infra/im/test_telegram.py`
- Modify: `docs/progress.md`
