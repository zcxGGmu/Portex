# M7.4.3 Memory Management Surface Design

## Goal

Complete the next operator-surface slice after `M7.4.2` by adding memory-management APIs and a matching web UI on top of the current file-backed `MemoryService`, instead of leaving memory as a backend/runner-only primitive.

## Scope

- add one dedicated `/memory` API surface
- add one dedicated `/memory` web page
- expose user-global `AGENTS.md` read/write
- expose workspace-scoped markdown memory file list/read/write
- expose workspace-scoped memory search
- keep the implementation aligned with the current `MemoryService` boundary

## Out Of Scope

- do not expose arbitrary files from `data/groups` or `data/sessions`
- do not add global cross-workspace search
- do not add session-memory management
- do not add markdown rendering, rich text editing, version history, or diff UI
- do not merge memory management into `Settings` or `ChatPanel`
- do not redesign runner-side memory tools in this slice

## Current Gap

Portex now has:

- a file-backed `MemoryService`
- user-global memory in `data/memory/user-global/{user_id}/AGENTS.md`
- workspace daily memory append/search in `data/memory/{group_folder}/`
- runner-side memory tools that already operate against mounted workspace memory
- no authenticated API or web UI for normal users to inspect and edit that memory directly

Portex still lacks:

- any route for global memory read/write
- any route for workspace memory list/read/write
- any route for workspace memory search
- any page that exposes these capabilities in the product

Today memory exists as a backend primitive, but not as a user-facing feature.

## Parity Signal From HappyClaw

The useful parity signal is narrow:

- memory is a product surface, not only a tool/runtime primitive
- users can inspect and edit their global memory
- users can inspect and edit workspace memory files
- search exists at the memory-management layer

HappyClaw also includes a broader “memory sources” model spanning group files, session files, and multiple scopes. Portex should not swallow that whole surface yet because its current `MemoryService` is still intentionally smaller.

## Options Considered

### Option A: Global memory only

- expose only the current user’s `AGENTS.md`

Pros:

- smallest implementation

Cons:

- ignores the already-existing workspace daily memory and search capability
- does not close the actual product gap around workspace memory

Reject.

### Option B: Memory management on top of the current `MemoryService`

- expose user-global memory
- expose workspace markdown memory files
- expose workspace search
- keep routes/files limited to `data/memory/...`

Pros:

- matches the current backend truth instead of inventing a larger memory system
- closes the real operator/product gap cleanly
- avoids overlap with the new generic workspace file-management surface

Cons:

- still narrower than HappyClaw’s full “memory center”

Recommendation: choose this option.

### Option C: Full memory center with all candidate files

- expose user-global, workspace files, session files, and generic memory-source discovery together

Pros:

- superficially closer to HappyClaw

Cons:

- exceeds the current `MemoryService` boundary
- overlaps with `M7.4.2` file management
- creates a much larger security and product-scope decision than needed

Reject.

## Recommended Design

### 1. Add One Dedicated `/memory` Surface

Introduce a dedicated memory route family instead of nesting memory under `/groups` or hiding it inside `Settings`.

Recommended routes:

- `GET /memory/global`
- `PUT /memory/global`
- `GET /memory/workspaces/{group_id}/files`
- `GET /memory/workspaces/{group_id}/file?path=...`
- `PUT /memory/workspaces/{group_id}/file`
- `GET /memory/workspaces/{group_id}/search?q=...`

This keeps memory as its own operator/product concept without turning it into a generic workspace file browser.

### 2. Keep Global Memory Scoped To The Current User

The global memory API should operate only on:

- `data/memory/user-global/{user_id}/AGENTS.md`

Rules:

- authenticated user reads only their own global memory
- authenticated user writes only their own global memory
- no cross-user access surface

This preserves the current `MemoryService` mental model.

### 3. Keep Workspace Memory Scoped To `data/memory/{group_folder}`

Workspace memory should remain a markdown-only surface under:

- `data/memory/{group_folder}`

In this slice, the API should manage only markdown memory files inside that root.

Do not expose:

- `data/groups/...`
- `data/sessions/...`
- arbitrary memory “candidate files”

That broader model belongs to a later explicit scope decision if Portex wants it.

### 4. Reuse Workspace Access Control

Workspace memory should follow workspace access:

- any user who can access the workspace can read/search/write its memory files

Do not require `groups.write` here.

Reasoning:

- memory is collaborative working context, not workspace administration
- users should be able to maintain memory in their accessible home/shared workspaces without needing admin-like write authority

This is intentionally different from `M7.4.2` files.

### 5. Extend `MemoryService` Minimally

Add only the methods needed for the approved surface:

- `list_group_memory_files(group_folder)`
- `get_group_memory_file(group_folder, relative_path)`
- `update_group_memory_file(group_folder, relative_path, content)`

Keep existing methods:

- `get_user_memory()`
- `update_user_memory()`
- `append_daily_memory()`
- `search_memory()`

Do not turn `MemoryService` into a generic file manager abstraction.

### 6. Enforce A Narrow Safety Boundary

Workspace memory file operations must:

- stay within `data/memory/{group_folder}`
- reject path traversal
- reject symlink escape
- require `.md`
- enforce a conservative content/file-size limit

If a requested file is valid but missing:

- `GET /memory/workspaces/{group_id}/file?path=...` should return empty content

This supports the intended UI flow of opening or creating a markdown memory note directly.

### 7. Keep Search Workspace-Scoped And Minimal

`GET /memory/workspaces/{group_id}/search?q=...` should:

- reuse the current `search_memory(group_folder, q)`
- return matching relative paths only

Do not add snippets, ranking, or cross-workspace aggregation in this slice.

### 8. Add A Dedicated `/memory` Page

The web app should add a dedicated `/memory` route and nav entry.

Recommended page structure:

- section 1: `My Global Memory`
- section 2: `Workspace Memory`

`Workspace Memory` should include:

- workspace selector using the existing `/groups` list
- file list for markdown files
- search input
- `Today` shortcut opening `YYYY-MM-DD.md`
- right-side or lower editor panel for the selected note

`My Global Memory` should include:

- one textarea editor
- save action

This keeps the UI clear and avoids over-coupling global and workspace memory.

## API Shape

### Global Memory

`GET /memory/global`

Returns:

- `content`
- `updated_at`
- `size`

`PUT /memory/global`

Body:

- `content`

### Workspace Memory Files

`GET /memory/workspaces/{group_id}/files`

Returns:

- `files[]`

Each file:

- `path`
- `name`
- `updated_at`
- `size`

### Workspace Memory File Read

`GET /memory/workspaces/{group_id}/file?path=...`

Returns:

- `path`
- `content`
- `updated_at`
- `size`

If missing but valid:

- return empty `content`
- `updated_at=null`
- `size=0`

### Workspace Memory File Write

`PUT /memory/workspaces/{group_id}/file`

Body:

- `path`
- `content`

### Workspace Memory Search

`GET /memory/workspaces/{group_id}/search?q=...`

Returns:

- `hits[]`

Each hit:

- `path`

## Data Flow

### Global Memory

1. authenticated user requests `/memory/global`
2. route resolves current user id
3. route calls `MemoryService.get_user_memory()`
4. route returns content metadata

Write path:

1. authenticated user submits content
2. route calls `MemoryService.update_user_memory()`
3. response returns updated metadata

### Workspace Memory

1. authenticated user selects a workspace from `/groups`
2. route resolves canonical workspace and access
3. route operates only on `data/memory/{group_folder}`
4. file list/read/write/search stay within markdown memory files only

## Testing Strategy

### Backend

Focused tests should cover:

- memory service group-memory file listing
- valid/missing group-memory file read behavior
- group-memory file write behavior
- traversal and extension guards
- `/memory` route auth and workspace access behavior
- OpenAPI docs for the new memory routes

### Frontend

For this slice:

- route wiring
- nav wiring
- global/workspace editors and search wiring
- `npm run lint`
- `npm run build`

Do not add a new frontend test harness in this step.

## Acceptance Criteria

This slice is complete when:

- Portex exposes authenticated APIs for user-global memory and workspace markdown memory management
- workspace memory uses workspace access control rather than `groups.write`
- path traversal and symlink escape are blocked inside `data/memory/{group_folder}`
- the web app exposes a dedicated `/memory` page with global memory editing, workspace memory file listing, workspace search, and note editing
- focused backend tests, full backend regression, frontend lint/build, and diff hygiene all pass
- handoff docs move the next real parity entrypoint to `M7.4.4`
