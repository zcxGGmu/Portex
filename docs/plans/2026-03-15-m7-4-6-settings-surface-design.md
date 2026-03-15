# M7.4.6 Settings And Configuration Surface Design

## Goal

Expand Portex settings beyond the current account summary by adding a real settings API + UI flow for provider config, channel config, registration policy, appearance, and system settings, with minimal-risk behavior integration.

## Scope

- add a dedicated `/settings` API family
- expand `/settings` web page from account summary to editable config sections
- add user-owned provider config and channel config persistence
- add system-owned registration policy, appearance, and system settings persistence
- enforce registration policy on `/auth/register`

## Out Of Scope

- no runtime-side provider injection into OpenAI execution backend in this slice
- no IM runtime live reconfiguration/auto-reconnect in this slice
- no multi-tenant org-level settings model
- no secrets encryption layer in this slice (file permissions + masked UI values only)
- no setup wizard/onboarding workflow (`M7.5.6`)

## Current Gap

Portex already has dedicated operator pages for monitor/files/memory/skills/mcp, but settings remain a static account summary. There is no persisted configuration surface for provider/channel/system policy, and registration behavior cannot be controlled via UI/API.

## Options Considered

### Option A: Full parity in one pass (runtime wiring + settings + onboarding)

Pros:
- closest to full HappyClaw settings behavior
- fewer future migrations

Cons:
- too broad for one `M7.4.x` slice
- high risk across execution and IM boundaries

Reject.

### Option B: Minimal settings surface with selective behavior wiring (recommended)

Pros:
- closes `M7.4.6` visible gap with controlled risk
- keeps the same incremental rhythm as `M7.4.1` ~ `M7.4.5`
- delivers one real behavior impact (`registration policy`) now

Cons:
- provider/channel settings are stored and manageable but not fully runtime-applied yet

Choose this option.

### Option C: Read-only settings aggregation page

Pros:
- very low risk

Cons:
- does not satisfy "expand configuration flows"
- weak parity value

Reject.

## Recommended Design

### 1. Storage Model

Use filesystem JSON under `data/settings`:

- user scope: `data/settings/users/{user_id}/provider.json`
- user scope: `data/settings/users/{user_id}/channels.json`
- system scope: `data/settings/global/registration.json`
- system scope: `data/settings/global/appearance.json`
- system scope: `data/settings/global/system.json`

Safety rules:

- validate `user_id` as safe segment
- enforce root containment and symlink escape checks
- enforce conservative max JSON file size
- atomic write via temp file + rename

### 2. Service Boundary

Add `SettingsService` with explicit methods:

- user scope:
  - `get_provider_config(user_id)` / `update_provider_config(user_id, ...)`
  - `get_channel_config(user_id)` / `update_channel_config(user_id, ...)`
- system scope:
  - `get_registration_policy()` / `update_registration_policy(...)`
  - `get_appearance_config()` / `update_appearance_config(...)`
  - `get_system_settings()` / `update_system_settings(...)`

Defaults preserve current behavior:

- registration: `allow_registration=true`, `require_invite_code=false`

### 3. API Surface

Add authenticated `/settings` routes:

- user-owned sections (any authenticated user):
  - `GET/PUT /settings/provider`
  - `GET/PUT /settings/channels`
- system sections:
  - read: `GET /settings/registration`, `GET /settings/appearance`, `GET /settings/system` requires `settings:read`
  - write: `PUT /settings/registration`, `PUT /settings/appearance`, `PUT /settings/system` requires `settings:write`

### 4. Behavior Wiring

Wire registration policy into `POST /auth/register`:

- if `allow_registration=false` -> `403`
- if `require_invite_code=true` and request has no `invite_code` -> `400`
- existing invite validation and user creation flow stays unchanged

### 5. Web Surface

Expand `/settings` page sections:

- account summary (existing)
- provider config form (base URL, model, API key, enabled)
- channel config form (Feishu + Telegram fields)
- registration policy section (owner editable, admin read-only)
- appearance section (owner editable, admin read-only)
- system settings section (owner editable, admin read-only)

UI behavior:

- mask secrets on load (show placeholder only)
- empty secret field means "keep existing"
- show explicit permission/read-only state for non-owner users

### 6. OpenAPI + DTO

Add `settings` tag and DTO contracts for all five sections in `domain/schemas.py`, including request/response models and route summary/description.

## Testing Strategy

- service tests for defaults, update persistence, user isolation, and path safety
- route tests for auth requirements, permission boundaries, CRUD behavior, and policy-enforced register flow
- OpenAPI schema assertions for new tag/paths/schemas
- frontend lint/build verification

## Acceptance

`M7.4.6` is complete when:

- `/settings` API family is implemented with focused backend tests
- `/settings` UI exposes all five configuration sections
- registration policy is enforced by `/auth/register`
- focused tests + full regression + lint/build pass
- `docs/progress.md` updates next entrypoint to `M7.4.7`
