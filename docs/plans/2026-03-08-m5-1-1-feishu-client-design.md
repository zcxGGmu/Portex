# M5.1.1 Feishu Client Design

## Goal

Complete `M5.1.1` by replacing the Feishu IM placeholder with a minimal but usable client skeleton that supports tenant access token retrieval plus the signature/decryption primitives needed for future webhook event handling.

## Scope

- Replace `infra/im/feishu.py` placeholder
- Implement:
  - async tenant access token retrieval
  - request signature verification helper
  - encrypted event payload decryption helper
- Add focused tests for auth, signature verification, and decryption
- Update `docs/progress.md` and `docs/TODO.md`

## Out of Scope

- Do not add FastAPI routes for Feishu callbacks yet
- Do not implement full event dispatch / websocket handling
- Do not finish Feishu send-message product logic
- Do not start Telegram work

## Design Constraints

- Keep the client focused on bootstrap capabilities for later stages
- Avoid expanding the generic `IMClient` protocol to fit Feishu-only behaviors
- Reuse existing project dependencies where possible (`httpx`, `cryptography`)

## Design Options

### Option A: Token only

- Add only `tenant_access_token` retrieval

Pros:
- Smallest implementation

Cons:
- Leaves event verification/decryption for later
- Conflicts with the requested scope

### Option B: Token + signature + decryption foundation

- Add token retrieval
- Add signature verification helper
- Add encrypted payload decryption helper

Pros:
- Best base for `M5.1.2`
- Still small and testable

Cons:
- Slightly more crypto code

### Option C: Full callback handling now

- Add client, callback parser, router glue, and event handler dispatch

Pros:
- Closer to end-state Feishu integration

Cons:
- Exceeds `M5.1.1`

## Recommended Design

Choose **Option B**.

## Client Contract

Implement `FeishuClient` in `infra/im/feishu.py` with:

- `app_id`
- `app_secret`
- `encrypt_key: str | None = None`
- `verification_token: str | None = None`
- `base_url: str = "https://open.feishu.cn"`
- injectable `http_client: httpx.AsyncClient | None = None`

### Public methods

- `async get_access_token() -> str`
- `verify_signature(timestamp: str, nonce: str, body: str, signature: str) -> bool`
- `decrypt_event(encrypt: str) -> dict[str, object]`

### Behavior

- token retrieval calls the Feishu tenant access token endpoint and raises a client error on non-zero codes or missing token
- signature verification computes the Feishu-style sha256 digest over `timestamp + nonce + verification_token + body`
- decryption uses AES-CBC with the decoded `encrypt_key`, strips PKCS7 padding, parses the length-prefixed JSON payload, and returns the decoded event dict

## Testing Strategy

Add `tests/infra/im/test_feishu.py` covering:

- token retrieval success and failure paths
- valid and invalid signatures
- successful decrypt round-trip from a helper-generated encrypted payload
- decrypt errors when `encrypt_key` is missing

## Files

- Modify: `infra/im/feishu.py`
- Create: `tests/infra/im/test_feishu.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
