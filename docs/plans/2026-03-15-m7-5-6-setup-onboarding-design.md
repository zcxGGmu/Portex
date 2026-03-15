# M7.5.6 Setup/Onboarding Pages Design

## Goal

Complete `M7.5.6` by adding a minimal multi-step setup/onboarding page so first-run users are guided through core configuration instead of landing directly in chat without setup cues.

## Scope

- add a dedicated protected `/setup` page in web app
- provide a multi-step onboarding flow using existing settings APIs
- include step actions for provider/channel/system baseline configuration
- add first-run redirect from login to setup (with skip/finish path to chat)
- keep backend contracts unchanged

## Out Of Scope

- no backend onboarding state model or migrations
- no terminal panel work (`M7.5.5` already deferred)
- no mobile/PWA work (`M7.5.7`)
- no redesign of existing `/settings` page

## Current Gap

Portex now has runtime/chat/operator surfaces, but onboarding is still missing. New users can authenticate and enter chat, yet there is no guided first-run sequence to configure provider/channel/system essentials.

## Options Considered

### Option A: Keep onboarding absent and rely on `/settings`

Pros:

- zero implementation work

Cons:

- does not satisfy `M7.5.6`
- weak first-run guidance compared with HappyClaw setup flow

Reject.

### Option B: Add minimal `/setup` multi-step wizard on top of current APIs (recommended)

Pros:

- satisfies milestone with small, low-risk frontend-only delta
- reuses existing stable settings APIs and permission boundaries
- keeps chat/runtime protocols unchanged

Cons:

- onboarding completion state is local (browser) in this slice

Recommendation: choose this option.

### Option C: Implement server-side onboarding state and enforcement

Pros:

- stronger cross-device first-run consistency

Cons:

- scope expansion into backend/state model
- unnecessary for current milestone

Reject.

## Recommended Design

### 1. Route And Navigation

- add protected route: `/setup`
- add `Setup` nav entry in app header
- login default target changes from `/chat` to `/setup` for first run (local marker not set)

### 2. First-Run Marker

- use browser local storage key: `portex.setup.completed`
- setup page `Skip` and `Finish` both mark completion and redirect to `/chat`
- if marker exists, login default target remains `/chat`

This keeps the milestone frontend-only and avoids backend schema changes.

### 3. Multi-Step Flow

- Step 1: Provider setup (`enabled/base_url/default_model/api_key`)
- Step 2: Channel setup (Feishu + Telegram toggles and secrets)
- Step 3: System setup for owner (`default_execution_mode/allow_host_execution`) with non-owner read-only hint
- Step 4: Completion summary with quick links to `Chat` and `Settings`

All writes use existing endpoints already exposed in `apiClient`.

### 4. Permission Boundary

- provider/channels are user-scoped and available to authenticated users
- system step write is owner-only (reuse backend `settings.write` gate)
- non-owner users still complete onboarding and can continue to chat

### 5. UX Boundary

- onboarding is additive; `/settings` remains the full configuration surface
- setup flow is minimal guidance, not a full replacement for settings management

## Verification Plan

- red evidence:
  - reference new `Setup` route in `App.tsx` before page exists
  - run `cd web && npm run build` expecting failure
- green:
  - `cd web && npm run lint`
  - `cd web && npm run build`
- regression:
  - `.venv/bin/pytest -o addopts='' -q`
  - `.venv/bin/ruff check .`
  - `git diff --check`

## Completion Signal

`M7.5.6` is complete when:

- `/setup` multi-step onboarding page is available
- login first-run default target can enter setup flow
- setup can be skipped/finished and route to chat
- verification passes and progress entrypoint advances to `M7.5.7`
