# M7.4.4 Skills Management Surface Design

## Goal

Add a user-facing skills-management surface (API + web page) so users can manage their own skills files under `data/skills/{user_id}` instead of having skills remain an implicit runner-only mount.

## Scope

- add a dedicated `/skills` API family
- add a dedicated `/skills` web page and nav entry
- support user-owned skill list/detail/create-update/enable-disable/delete
- keep storage rooted at `data/skills/{user_id}`
- enforce strict path-safety and file-size limits

## Out Of Scope

- no skills marketplace, install/reinstall, or remote search
- no host-skill sync flow
- no project-wide shared skills governance
- no runtime dynamic tool loading in this slice
- no runner protocol/schema changes

## Current Gap

Portex already mounts `data/skills/{user_id}` into container runs (`/workspace/skills`), but it has no product surface for users to inspect or manage those skills. `services/skills.py` is a placeholder and there is no `/skills` route or page.

## Options Considered

### Option A: Full HappyClaw-like skills center

Pros:
- closest feature parity to HappyClaw

Cons:
- very large scope (store/sync/install/detail/search flows)
- introduces external integration and process execution complexity
- not aligned with the current incremental M7.4 strategy

Reject.

### Option B: Minimal user-owned skills file management (recommended)

Pros:
- closes the immediate product gap with limited risk
- reuses existing `data/skills/{user_id}` storage boundary
- keeps security/audit scope small

Cons:
- does not include marketplace/installation workflows

Choose this option.

### Option C: Runtime-first dynamic tool registry only

Pros:
- directly touches execution behavior

Cons:
- no operator surface parity by itself
- high regression risk in execution plane

Reject for `M7.4.4`.

## Recommended Design

### 1. Skills Storage Model

Use user-local filesystem storage:

- root: `data/skills/{user_id}/`
- one skill per directory: `{skill_id}/`
- enabled file: `SKILL.md`
- disabled file: `SKILL.md.disabled`

`skill_id` is a safe segment (`[A-Za-z0-9][A-Za-z0-9._-]*`).

### 2. Service Boundary

Implement `SkillsService` with:

- `list_user_skills(user_id)`
- `get_user_skill(user_id, skill_id)`
- `upsert_user_skill(user_id, skill_id, content)`
- `set_user_skill_enabled(user_id, skill_id, enabled)`
- `delete_user_skill(user_id, skill_id)`

Safety rules:

- all paths must remain inside `data/skills/{user_id}`
- reject traversal and symlink escape
- reject oversized content/files using a conservative limit

### 3. API Surface

Add `/skills` routes (authenticated user scope only):

- `GET /skills`
- `GET /skills/{skill_id}`
- `PUT /skills/{skill_id}`
- `PATCH /skills/{skill_id}/state`
- `DELETE /skills/{skill_id}`

Users only manage their own skills. Cross-user access is not exposed.

### 4. Web Surface

Add a `/skills` page with:

- skill list (enabled/disabled state + update time)
- selected skill content editor
- create/update action
- enable/disable toggle
- delete action

Keep UI intentionally simple and aligned with existing Files/Memory pages.

### 5. OpenAPI + DTO

Add `skills` tag and DTOs for:

- list summary
- detail
- update request
- state change request
- delete response

## Testing Strategy

- service tests for file model + safety guards
- route tests for auth, ownership isolation, CRUD/state operations
- OpenAPI contract updates in existing API schema tests
- frontend verification via lint/build (existing repo standard)

## Acceptance

`M7.4.4` is complete when:

- `/skills` API routes are available and covered by tests
- `/skills` page is reachable from nav and operational
- focused tests + full regression + lint/build all pass
- `docs/progress.md` records completion and next entrypoint (`M7.4.5`)
