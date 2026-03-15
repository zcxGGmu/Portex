# M7.5.7 Mobile/PWA Design

## Goal

Complete `M7.5.7` by making the current web app installable as a minimal PWA and materially more usable on mobile screens, without changing backend APIs or chat/runtime behavior.

## Scope

- add installable PWA plumbing to the Vite frontend
- add a minimal app manifest, service-worker registration, and app icons
- expose a lightweight install/update surface in the UI
- make the authenticated shell substantially easier to use on small screens
- preserve all current routes and permission boundaries

## Out Of Scope

- no offline chat queue, offline message cache, or background sync
- no push notifications
- no native-app packaging
- no terminal panel work
- no backend/mobile API changes
- no `M7.6` channel/ecosystem decisions

## Current Gap

Portex has reached functional chat/operator parity for the current web surface, but it is still missing the mobile/PWA layer called out by the parity backlog. The frontend does not ship a manifest, service worker, install entrypoint, mobile-safe spacing, or a compact authenticated navigation pattern for narrow viewports.

## Options Considered

### Option A: Add only responsive CSS tweaks

Pros:

- smallest implementation delta

Cons:

- does not satisfy the PWA half of `M7.5.7`
- still leaves install flow absent

Reject.

### Option B: Add minimal installable PWA plus responsive authenticated shell (recommended)

Pros:

- satisfies the milestone with bounded frontend-only work
- keeps runtime/chat contracts unchanged
- improves real mobile usability without committing to offline semantics

Cons:

- install experience is still intentionally thin
- service worker remains app-shell oriented, not data/offline oriented

Recommendation: choose this option.

### Option C: Attempt full offline-first mobile experience

Pros:

- strongest mobile story

Cons:

- expands into caching/data-consistency decisions the project has not made
- high regression risk for chat/runtime surfaces

Reject.

## Recommended Design

### 1. PWA Build Plumbing

- add `vite-plugin-pwa` to the web app
- generate a minimal manifest with:
  - app name/short name: `Portex`
  - standalone display
  - `/chat` start URL
  - theme/background colors aligned with current shell
- precache only the built app shell/assets; do not add API runtime caching

This keeps the PWA layer safe and avoids stale chat/operator data semantics.

### 2. Runtime Registration Boundary

- register the service worker from `web/src/main.tsx`
- in dev mode, explicitly clear stale service workers/caches so local iteration does not get trapped behind old assets
- expose update availability through a tiny hook/component rather than pushing silent state into unrelated pages

### 3. Install UX

- add a small install affordance that listens to `beforeinstallprompt`
- show it in authenticated layout where it is globally available
- allow dismiss/install/update actions without blocking app usage
- detect standalone mode and suppress redundant install prompts when already installed

### 4. Mobile Shell

- keep desktop header navigation as-is conceptually
- for narrow screens, collapse authenticated navigation into a compact shell:
  - header remains lightweight
  - a fixed bottom quick-nav exposes the most-used destinations
  - a `More` overflow keeps secondary/operator routes reachable
- add safe-area padding so the shell remains usable in standalone mobile mode

### 5. Route Prioritization

Mobile quick-nav should prioritize:

- `Chat`
- `Files`
- `Memory`
- `Settings`
- `More`

The overflow menu holds:

- `Setup`
- `Skills`
- `MCP`
- operator-only routes already gated by role

This keeps the bottom bar small while preserving full route access.

### 6. Styling Boundary

- add mobile breakpoints only where the current shell is cramped:
  - app header/nav
  - main content padding
  - setup progress/actions
  - chat shell cards and subpanels
- add standalone-display safe-area handling for top/bottom padding

## Verification Plan

- red evidence:
  - reference new PWA/mobile entrypoints before they exist
  - run `cd web && npm run build` expecting failure
- green:
  - `cd web && npm run lint`
  - `cd web && npm run build`
- regression:
  - `.venv/bin/pytest -o addopts='' -q`
  - `.venv/bin/ruff check .`
  - `git diff --check`

## Completion Signal

`M7.5.7` is complete when:

- the web app builds with manifest + service worker support
- authenticated users can trigger install/update flows from the UI
- authenticated navigation is materially usable on mobile widths
- standalone/mobile safe-area styling is in place
- verification passes and progress entrypoint advances beyond `M7.5.7`
