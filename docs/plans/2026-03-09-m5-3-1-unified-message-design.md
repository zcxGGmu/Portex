# M5.3.1 Unified Message Design

## Goal

Complete `M5.3.1` by introducing a minimal cross-channel message DTO that Feishu and Telegram events can convert into without pulling routing or sending logic into scope.

## Scope

- Extend `domain/schemas.py` with `UnifiedMessage`
- Extend Feishu and Telegram message event objects with `to_unified_message()`
- Add focused schema and IM conversion tests
- Update handoff docs after verification

## Out of Scope

- Do not implement message routing
- Do not wire `UnifiedMessage` into `services/message_service.py`
- Do not refactor `/messages` or WebSocket routes
- Do not add persistent `chat_jid -> group_folder` mapping
- Do not add attachments, sender names, or rich message payload abstractions

## Options Considered

### Option A: Follow the TODO snippet literally

- `channel`
- `sender_id`
- `group_folder`
- `content`
- `message_id`
- `timestamp`

Pros:
- Smallest visible schema

Cons:
- Missing a routeable conversation key for later reply routing
- Forces `M5.3.2` to re-open the DTO immediately

### Option B: Minimal routeable DTO

- `channel`
- `chat_jid`
- `sender_id`
- `group_folder | None`
- `content`
- `message_id`
- `timestamp`

Recommendation: choose this option. It stays very close to the TODO contract but preserves the key piece needed for future routing: the original channel-scoped conversation identifier.

### Option C: Full shared event abstraction

- Add `message_type`, `raw_event`, `sender_name`, attachments, and more

Reject: this expands beyond `M5.3.1` and would duplicate the information already preserved in the channel-specific event objects.

## Recommended Design

### UnifiedMessage schema

Add a new schema in `domain/schemas.py`:

- `channel: Literal["web", "feishu", "telegram"]`
- `chat_jid: str`
- `sender_id: str`
- `group_folder: str | None = None`
- `content: str`
- `message_id: str`
- `timestamp: datetime`

`timestamp` should normalize to UTC like other schema datetime fields.

### Channel conversion helpers

Keep `FeishuMessageEvent` and `TelegramMessageEvent` as the source-of-truth event contracts, but add:

- `to_unified_message(self, group_folder: str | None = None) -> UnifiedMessage`

Mapping rules:

- Feishu
  - `channel="feishu"`
  - `chat_jid=f"feishu:{chat_id}"`
  - `content=text or ""`
- Telegram
  - `channel="telegram"`
  - `chat_jid=f"telegram:{chat_id}"`
  - `content=text or ""`

### Timestamp handling

- `UnifiedMessage` requires `timestamp`
- Feishu and Telegram event objects should expose a `timestamp` field
- When source payloads provide platform timestamps, parse them into UTC datetimes
- When current minimal test payloads omit those fields, fall back to current UTC time so the DTO remains usable without expanding older fixtures

This keeps `M5.3.1` focused on a stable DTO and thin adapters rather than on platform ingestion completeness.

## Testing Strategy

Add tests covering:

- `UnifiedMessage` accepts text and non-text content shapes (`content=""`, `group_folder=None`)
- Feishu text event converts to `UnifiedMessage`
- Feishu non-text event converts with empty `content`
- Telegram text event converts to `UnifiedMessage`
- Telegram non-text event converts with empty `content`
- Source timestamp extraction works when the platform payload includes a real timestamp

## Files

- Modify: `domain/schemas.py`
- Modify: `infra/im/feishu.py`
- Modify: `infra/im/telegram.py`
- Add: `tests/domain/test_schemas.py`
- Modify: `tests/infra/im/test_feishu.py`
- Modify: `tests/infra/im/test_telegram.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
