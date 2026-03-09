# M5.2.3 Telegram Markdown Conversion Design

## Goal

Complete `M5.2.3` by adding a minimal Markdown-to-Telegram-HTML conversion helper for outbound Telegram text formatting.

## Scope

- Extend `infra/im/telegram.py`
- Add a pure `markdown_to_html()` helper on `TelegramClient`
- Add focused Telegram markdown conversion tests
- Update handoff docs after verification

## Out of Scope

- Do not implement Telegram message sending
- Do not implement `parse_mode`, retry, or fallback send logic
- Do not implement long-message splitting
- Do not implement typing indicators
- Do not implement links, headings, lists, blockquotes, or full Markdown parsing
- Do not add a shared cross-channel formatting layer

## Options Considered

### Option A: Literal TODO sample only

- Convert only `**`, `*`, and `` ` `` with simple replacements

Pros:
- Smallest possible diff

Cons:
- Incorrect for opening/closing tags
- Unsafe without HTML escaping
- Misses fenced code blocks, which are high-frequency in Portex output

### Option B: Minimal safe Telegram HTML conversion

- Escape raw `&`, `<`, and `>`
- Convert fenced code blocks first
- Convert inline code
- Convert bold and italic
- Leave all unsupported Markdown untouched

Recommendation: choose this option. It provides the smallest useful and safe formatter for Telegram HTML while keeping `M5.2.3` strictly below a full Markdown engine.

### Option C: Richer Markdown support

- Add links, headings, strikethrough, more syntax, and parser-like behavior

Reject: this grows formatting complexity too early and drifts toward the later send/render pipeline.

## Recommended Design

Add:

- `def markdown_to_html(self, text: str) -> str`

Behavior:

- Keep it synchronous and side-effect free
- Treat the input as best-effort Markdown
- Return a Telegram-safe HTML string

### Conversion order

1. Extract fenced code blocks and replace them with placeholders
2. Escape the remaining raw text for Telegram HTML safety
3. Convert inline code spans
4. Convert bold and italic markers
5. Restore fenced code blocks as `<pre><code>...</code></pre>` with escaped inner text

### Supported syntax

- ````` ```code``` ````` -> `<pre><code>code</code></pre>`
- `` `code` `` -> `<code>code</code>`
- `**bold**` -> `<b>bold</b>`
- `*italic*` -> `<i>italic</i>`

### Unsupported syntax

- Links such as `[text](url)`
- Headings
- Lists
- Blockquotes
- Nested or cross-overlapping styles

Unsupported syntax should remain as escaped plain text rather than raising errors.

## Testing Strategy

Add tests covering:

- plain text is preserved but HTML-escaped
- mixed bold, italic, and inline code are converted
- fenced code blocks render to `<pre><code>` and do not get re-formatted internally
- incomplete markdown markers do not raise and remain plain text
- unsupported syntax such as Markdown links remains unchanged except for HTML escaping

## Files

- Modify: `infra/im/telegram.py`
- Modify: `tests/infra/im/test_telegram.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
