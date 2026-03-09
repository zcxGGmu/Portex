# M5.2.2 Telegram Message Handling Design

## Goal

Complete `M5.2.2` by adding minimal Telegram update normalization on top of the existing polling client.

## Scope

- Extend `infra/im/telegram.py`
- Add a Telegram message event dataclass
- Implement `handle_update()` as a pure normalization helper
- Add focused Telegram message handling tests
- Update handoff docs after verification

## Out of Scope

- Do not implement Markdown to HTML conversion
- Do not implement Telegram message sending
- Do not implement callback query, edited message, or channel post handling
- Do not add unified cross-channel message routing
- Do not add retries, deduplication, pairing, file download, or media processing

## Options Considered

### Option A: Text-only normalization

- Normalize only `message.text`
- Return `None` for every non-text message

Pros:
- Smallest possible change

Cons:
- Forces a follow-up event shape change as soon as non-text Telegram messages matter

### Option B: Normalize `message` updates with a stable event shape

- Support only top-level `message` updates for now
- Return a `TelegramMessageEvent` for text and non-text messages
- Keep `text=None` for non-text messages
- Return `None` for unsupported update families such as `edited_message` and `callback_query`

Recommendation: choose this option. It mirrors the current Feishu event style, keeps `M5.2.2` small, and avoids near-term refactoring when richer Telegram message types arrive.

### Option C: Normalize multiple Telegram update families immediately

- Handle `message`, `edited_message`, `callback_query`, `channel_post`, and more

Reject: this pushes `M5.2.2` into routing semantics that are not yet designed in Portex.

## Recommended Design

Add:

- `@dataclass(slots=True) class TelegramMessageEvent`
- `def handle_update(self, update: dict[str, object]) -> TelegramMessageEvent | None`

`TelegramMessageEvent` fields:

- `event_type: str`
- `chat_id: str`
- `message_id: str`
- `sender_id: str`
- `message_type: str`
- `text: str | None`
- `raw_event: dict[str, object]`

### Event handling rules

- If `update` contains no top-level `message` dict, return `None`
- If `message` exists but required structural fields are missing or malformed, raise `TelegramClientError`
- For text messages:
  - `message_type="text"`
  - `text=<message.text>` only when it is a non-empty string
- For non-text `message` updates:
  - infer `message_type` from known Telegram keys such as `photo`, `document`, `voice`, `sticker`, `video`
  - set `text=None`
- Save the inner `message` dict as `raw_event`, matching the current Feishu pattern of storing the normalized event payload rather than the outer transport envelope

### Validation rules

Required fields for supported `message` updates:

- `message.chat.id`
- `message.message_id`
- `message.from.id`

These can be numeric in Telegram payloads and should be normalized to strings in the returned event.

## Testing Strategy

Add tests covering:

- text message update normalization
- unsupported update family returns `None`
- non-text message preserves IDs and returns `text=None`
- malformed supported message payload raises `TelegramClientError`

## Files

- Modify: `infra/im/telegram.py`
- Modify: `tests/infra/im/test_telegram.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
