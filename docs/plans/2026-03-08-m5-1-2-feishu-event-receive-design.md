# M5.1.2 Feishu Event Receive Design

## Goal

Complete `M5.1.2` by extending the Feishu client foundation so it can accept a Feishu callback payload, handle encrypted bodies, recognize message events, and return a normalized message structure for later Portex integration.

## Scope

- Extend `infra/im/feishu.py`
- Add a normalized Feishu message event structure
- Implement a minimal event receive / parse helper that:
  - accepts plaintext or encrypted callback payloads
  - recognizes `im.message.receive_v1`
  - extracts the minimal message fields Portex needs next
- Add focused Feishu event tests
- Update `docs/progress.md` and `docs/TODO.md`

## Out of Scope

- Do not add FastAPI webhook routes yet
- Do not dispatch events into the current Portex message pipeline yet
- Do not implement Feishu send-message product logic
- Do not start Telegram work

## Design Constraints

- Build directly on the current Feishu auth/signature/decryption foundation
- Keep event handling minimal and deterministic
- Avoid overfitting to one Feishu payload variant when a tolerant parser is easy

## Recommended Design

- Add `FeishuMessageEvent` dataclass with:
  - `event_type`
  - `chat_id`
  - `message_id`
  - `sender_id`
  - `message_type`
  - `text`
  - `raw_event`
- Add `handle_webhook_event(payload: dict[str, object]) -> FeishuMessageEvent | None`

### Parsing rules

- If payload has `encrypt`, decrypt first
- Support both:
  - modern style: `{"header": {"event_type": ...}, "event": {...}}`
  - minimal style: `{"type": "...", "message": {...}}`
- Only normalize `im.message.receive_v1`
- For `message.content`, if it is a JSON string with a `text` field, extract that field
- Return `None` for unsupported event types

## Testing Strategy

Add to `tests/infra/im/test_feishu.py`:

- plaintext `im.message.receive_v1` is normalized correctly
- encrypted `im.message.receive_v1` is normalized correctly
- unsupported event returns `None`
- non-text or malformed content yields `text=None` but still keeps core ids

## Files

- Modify: `infra/im/feishu.py`
- Modify: `tests/infra/im/test_feishu.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
