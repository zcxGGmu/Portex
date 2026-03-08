# M5.1.3 Feishu Send Message Design

## Goal

Complete `M5.1.3` by extending the Feishu client with the smallest useful message send capability on top of the existing token/signature/decryption/event foundation.

## Scope

- Extend `infra/im/feishu.py`
- Implement async message sending against the Feishu message send endpoint
- Add focused tests for request shape and error handling
- Update `docs/progress.md` and `docs/TODO.md`

## Out of Scope

- Do not add FastAPI routes
- Do not implement retries, rate limiting, or idempotency
- Do not add Telegram send support
- Do not add rich card builders or message formatting abstractions

## Design Constraints

- Build on current `FeishuClient.get_access_token()`
- Keep the method small and testable with an injected async HTTP client
- Avoid expanding the generic IM abstraction more than necessary

## Recommended Design

Implement:

- `async send_message(self, receive_id: str, content: dict[str, object], receive_id_type: str = "chat_id") -> dict[str, object]`

### Request behavior

- Fetch tenant access token first
- POST to:
  - `/open-apis/im/v1/messages?receive_id_type=<...>`
- Send JSON body:
  - `receive_id`
  - `msg_type`
  - `content`

For the minimal contract, require `content` to include:
- `msg_type: str`
- `content: str | dict[str, object]`

If `content["content"]` is a dict, JSON-serialize it before sending, because Feishu expects a stringified content body.

### Response behavior

- On `code == 0`, return the response payload
- On non-zero code or malformed response, raise `FeishuClientError`

## Testing Strategy

Add to `tests/infra/im/test_feishu.py`:

- successful send uses the expected URL, auth header, and JSON body
- dict `content` is serialized to JSON string
- Feishu error code raises `FeishuClientError`

## Files

- Modify: `infra/im/feishu.py`
- Modify: `tests/infra/im/test_feishu.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
