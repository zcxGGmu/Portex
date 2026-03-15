# M7.4.5 MCP Server Management Surface Design

## Goal

Add a user-facing MCP server management surface (API + web page) so users can manage per-user MCP server configs under `data/mcp-servers/{user_id}` instead of treating MCP as a hidden or future-only runtime detail.

## Scope

- add a dedicated `/mcp-servers` API family
- add a dedicated `/mcp-servers` web page and nav entry
- support user-owned MCP server list/detail/create-update/enable-disable/delete
- store MCP server config in `data/mcp-servers/{user_id}/servers.json`
- validate transport config for `stdio` / `http` / `sse`

## Out Of Scope

- no host config sync (`sync-host`) in this slice
- no runtime-side MCP wiring to execution backends in this slice
- no cross-user or org-wide shared MCP registry
- no approval workflow or risk-tier policy for external MCP servers
- no settings-page integration; keep standalone page first

## Current Gap

Portex has already exposed monitor/files/memory/skills operator pages, but MCP server management is still missing. Compared with HappyClaw's user-managed MCP server surface, Portex currently has no API contract, no storage service, and no web entrypoint for user-side MCP server config lifecycle.

## Options Considered

### Option A: Full HappyClaw parity including host sync and runtime injection

Pros:
- closest parity with HappyClaw behavior
- immediately useful for runtime tool expansion

Cons:
- mixes three concerns at once (management + sync + runtime)
- higher regression risk in execution plane
- too large for one `M7.4.x` incremental slice

Reject.

### Option B: Minimal user-owned MCP server management surface (recommended)

Pros:
- closes the visible operator gap with low risk
- keeps security boundary local and auditable
- preserves room for later runtime integration without redoing storage contract

Cons:
- managed MCP servers are not yet consumed by runtime
- no admin sync from host-side config files

Choose this option.

### Option C: Runtime wiring first with no operator page

Pros:
- directly impacts execution behavior

Cons:
- does not close operator-surface parity
- poor manageability and low observability

Reject for `M7.4.5`.

## Recommended Design

### 1. Storage Model

Use per-user JSON storage:

- root: `data/mcp-servers/{user_id}/`
- file: `servers.json`
- object shape: `{ "servers": { "<server_id>": { ...entry } } }`

`server_id` uses a safe segment pattern: `[A-Za-z0-9][A-Za-z0-9._-]*`.

Each entry stores:

- `enabled` (bool)
- `transport` (`stdio` / `http` / `sse`)
- transport fields:
  - `stdio`: `command`, optional `args`, optional `env`
  - `http`/`sse`: `url`, optional `headers`
- optional `description`
- `created_at` / `updated_at`

### 2. Service Boundary

Implement `McpServersService` with:

- `list_user_servers(user_id)`
- `get_user_server(user_id, server_id)`
- `upsert_user_server(user_id, server_id, request)`
- `set_user_server_enabled(user_id, server_id, enabled)`
- `delete_user_server(user_id, server_id)`

Safety rules:

- keep all paths inside `data/mcp-servers/{user_id}`
- reject traversal/symlink escapes
- enforce conservative JSON file size limit
- validate transport-specific fields strictly

### 3. API Surface

Add authenticated `/mcp-servers` routes:

- `GET /mcp-servers`
- `GET /mcp-servers/{server_id}`
- `PUT /mcp-servers/{server_id}`
- `PATCH /mcp-servers/{server_id}/state`
- `DELETE /mcp-servers/{server_id}`

Only current-user scope is exposed; no cross-user operations.

### 4. Web Surface

Add `/mcp-servers` page with:

- server list (enabled state, transport, update time)
- selected server detail editor (transport fields + description)
- create/update action
- enable/disable toggle
- delete action

Keep UI consistent with current Files/Memory/Skills operator pages.

### 5. OpenAPI + DTO

Add `mcp_servers` tag and DTOs for:

- list summary
- detail
- upsert request
- state toggle request
- delete response

## Testing Strategy

- service tests for CRUD, transport validation, and path safety
- route tests for auth, user isolation, CRUD/state behavior
- OpenAPI schema assertions for new tag/path/schema
- frontend verification via existing lint/build commands

## Acceptance

`M7.4.5` is complete when:

- `/mcp-servers` APIs exist with focused coverage
- `/mcp-servers` page is reachable from nav and usable
- focused tests + full regression + lint/build pass
- `docs/progress.md` records completion and next entrypoint (`M7.4.6`)
