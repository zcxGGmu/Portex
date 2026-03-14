# M7.4.2 Workspace File Management Design

## Goal

Complete the next operator-surface slice after `M7.4.1` by adding workspace file-management APIs and a matching minimal web UI for browsing, uploading, downloading, previewing, editing, and deleting files with the same path-safety rigor as the current execution security boundary.

## Scope

- add one workspace file service rooted at `data/groups/{workspace_folder}`
- add authenticated workspace file APIs under `/groups/{group_id}`
- add a minimal `/files` web page with workspace selection and file operations
- enforce path traversal and symlink escape protection
- keep file access aligned with current workspace membership semantics

## Out Of Scope

- do not add rename
- do not add create-directory
- do not add batch operations
- do not add desktop “open local directory”
- do not add drag-and-drop trees or full IDE UX
- do not couple the feature into the current `ChatPanel`
- do not add new persistence tables for file metadata

## Current Gap

Portex now has:

- canonical workspaces and membership
- path-safety helpers used by execution infrastructure
- a monitor/operator surface and a basic web app shell

Portex still lacks:

- any authenticated file-management API
- any file-management page in the web app
- any reusable service layer for safe workspace-relative file operations

Today workspace files exist only as implicit directories under `data/groups/*`, with no product surface on top.

## Parity Signal From HappyClaw

The useful parity signal is still narrow:

- users can see files inside one workspace
- users can upload and download files safely
- users can preview safe file types and edit plain text files
- file operations respect workspace access and path-safety boundaries

HappyClaw also includes richer file tree interactions, directory creation, rename flows, and deeper workspace shell integration. Those remain later work.

## Options Considered

### Option A: Attach files directly to `ChatPanel`

- add file sidebar and upload controls inside the existing chat view

Pros:

- feels closer to the final product

Cons:

- current chat routing is still fixed to `group-demo`
- mixes this slice with later `M7.5` workspace-shell work
- makes file-management verification depend on unrelated chat UX decisions

Reject.

### Option B: Add a dedicated `/files` page plus workspace-scoped APIs

- add a standalone files page
- use the existing `/groups` list as the workspace selector
- keep file operations under the current workspace route family

Pros:

- closes the parity gap without dragging in `M7.5`
- reuses current workspace access control cleanly
- keeps backend and frontend scope understandable

Cons:

- separate page is less integrated than the final product shell

Recommendation: choose this option.

### Option C: Backend-only file APIs

- ship the routes and defer UI

Pros:

- smallest backend delta

Cons:

- does not satisfy the API/UI nature of `M7.4.2`
- postpones the operator-facing value again

Reject.

## Recommended Design

### 1. Add One Dedicated Workspace File Service

Create a backend service responsible for safe file operations under one workspace root:

- root: `data/groups/{workspace_folder}`

This service should centralize:

- path normalization
- root containment
- symlink escape checks
- directory listing
- upload target resolution
- preview/content access rules
- destructive-operation guards

Routes should call this service instead of re-implementing filesystem checks inline.

### 2. Keep File Access Tied To Workspace Access

Use the current workspace access model:

- any user who can access the workspace can read file state
- only users with `groups.write` authority should modify file state

Practical read permissions:

- list files
- download file
- preview file
- read text file content

Practical write permissions:

- upload file
- save text file content
- delete file or directory

This avoids turning shared workspace files into a fully writable member surface too early.

### 3. Use Workspace-Scoped Routes Under `/groups/{group_id}`

Add:

- `GET /groups/{group_id}/files?path=`
- `POST /groups/{group_id}/files`
- `GET /groups/{group_id}/files/download/{file_path:path}`
- `GET /groups/{group_id}/files/preview/{file_path:path}`
- `GET /groups/{group_id}/files/content/{file_path:path}`
- `PUT /groups/{group_id}/files/content/{file_path:path}`
- `DELETE /groups/{group_id}/files/{file_path:path}`

This keeps file operations aligned with the rest of the current workspace API surface.

### 4. Enforce The Same Safety Principles As Execution Paths

The file service must reject:

- `..` traversal
- absolute-path escape
- symlink escape
- deleting the workspace root
- overwriting the workspace root

All user-facing paths should remain workspace-relative.

This should reuse the current `validate_path()` helper patterns where possible, but the file service should own the higher-level rules for files versus directories.

### 5. Keep Type Handling Conservative

For the first slice:

- text content read/write only for a small extension allowlist
- preview only for safe inline types:
  - images
  - plain text
  - PDF
- other file types should be downloadable but not rendered inline

Add file-size limits for:

- upload
- text read
- text write

This avoids turning preview/edit into a risky generic file browser.

### 6. Return File Entries As Deterministic Directory Listings

The list API should return:

- `current_path`
- `entries[]`

Each entry should include:

- `name`
- `path`
- `type`
- `size`
- `modified_at`

Directories should sort before files, then by name.

This is enough for the web page without creating extra metadata abstractions.

### 7. Add A Minimal `/files` Page

Add one authenticated page:

- route: `/files`

The page should include:

- workspace selector using current `/groups`
- current path breadcrumb / “up” action
- upload button
- file list
- preview/editor panel

Interaction model:

- click directory -> navigate into it
- click text file -> load `/content`, show editor
- click image/PDF -> load `/preview`
- click other file -> expose download action only

Keep the layout intentionally simple and operator/workspace focused.

### 8. Do Not Over-Couple To The Current Chat State

This slice should not depend on:

- websocket chat state
- current `group-demo` chat hardcoding
- monitor-page polling

The files page should stand on its own and prepare for later workspace-shell integration.

## API Shape

### List Files

`GET /groups/{group_id}/files?path=`

Returns:

- `current_path`
- `entries[]`

### Upload Files

`POST /groups/{group_id}/files`

`multipart/form-data` fields:

- `path`
- one or more `files`

Returns uploaded entry names/paths only.

### Download

`GET /groups/{group_id}/files/download/{file_path:path}`

Returns a streamed file download for files only.

### Preview

`GET /groups/{group_id}/files/preview/{file_path:path}`

Returns inline-safe content or a safe failure for unsupported targets.

### Text Content Read

`GET /groups/{group_id}/files/content/{file_path:path}`

Returns text content only for allowed text file types under the size limit.

### Text Content Write

`PUT /groups/{group_id}/files/content/{file_path:path}`

Accepts JSON:

- `content`

Writes text content atomically for allowed text file types only.

### Delete

`DELETE /groups/{group_id}/files/{file_path:path}`

Deletes one file or one directory under the workspace root, excluding root itself.

## Data Flow

### Backend

1. route resolves canonical workspace
2. route enforces read/write permission based on current user role and workspace access
3. route delegates path handling to the file service
4. file service resolves one safe absolute path under `data/groups/{workspace_folder}`
5. route maps result into DTO or streaming response

### Frontend

1. `/files` loads accessible workspaces from `/groups`
2. user selects workspace
3. page requests directory listing for the current path
4. clicking files either opens preview/editor or triggers download
5. write actions refresh the current listing after success

## Testing Strategy

### Backend

Focused tests should cover:

- file service path traversal rejection
- symlink escape rejection
- root delete/overwrite guard
- directory listing ordering
- upload path validation and size limits
- text file content read/write restrictions
- preview behavior for supported vs unsupported types
- route `401/403/404/400/200` behavior
- OpenAPI docs for the new file routes

### Frontend

For this slice:

- typed API wiring
- `/files` route and nav entry wiring
- lint/build verification

Do not add a new frontend test harness just for this step.

## Acceptance Criteria

This slice is complete when:

- Portex exposes authenticated workspace file-management APIs for browse/upload/download/preview/edit/delete
- path traversal and symlink escape attempts are blocked
- file read/write permissions follow current workspace access and write-role boundaries
- the web app exposes a working `/files` page with workspace selection and minimal file operations
- focused backend tests, broad backend regression, frontend lint/build, and diff hygiene all pass
- handoff docs move the next real parity entrypoint to `M7.4.3`
