# M4.2.3 Group Member Management Design

## Goal

Complete `M4.2.3` by introducing the minimal group-member contract needed for RBAC-aware group collaboration: a formal `GroupMember` model, a lightweight member-management service, and the smallest API surface that proves the contract end-to-end.

## Scope

- Add `domain/models/group_member.py` with `group_members` persistence contract
- Extend `domain/schemas.py` with member request/response payloads
- Add a lightweight `services/group_member_service.py` for in-memory member management
- Add `GET /groups/{group_id}/members`
- Add `POST /groups/{group_id}/members`
- Add `DELETE /groups/{group_id}/members/{user_id}`
- Reuse the current static permission templates with `require_permission("groups", "...")`
- Add focused domain / service / route tests

## Out of Scope

- Do not migrate groups or users to a DB-backed source of truth
- Do not add owner transfer, invitations, or approval workflows
- Do not expand the RBAC model beyond the existing `groups` resource
- Do not introduce frontend UI changes
- Do not unify every existing `group_id` / `group_jid` naming seam in the repository
- Do not enable `user.permissions` overrides or DB-backed permission resolution

## Design Constraints

- Current authenticated users still come from the in-memory `AuthService`
- Current `/groups` listing is still a minimal stub returning `group-demo`
- `M4.2.3` should add only the minimum behavior needed to model and manage members
- System-level user roles and group-level member roles must stay separate

## Design Options

### Option A: Model only

- Add `GroupMember` SQLAlchemy model and related schemas
- Leave runtime behavior unchanged

Pros:
- Lowest implementation risk

Cons:
- No service or API behavior to prove the contract works
- Leaves `M4.2.3` under-delivered for actual member management

### Option B: Full DB-backed member management

- Add `GroupMember` model plus DB repository/service/routes immediately
- Use DB as the runtime source of truth for memberships

Pros:
- Closer to the future target architecture

Cons:
- Conflicts with the current in-memory auth/user source
- Forces broader persistence decisions not yet scheduled

### Option C: Hybrid minimal delivery

- Add `GroupMember` SQLAlchemy model as the formal contract
- Add an in-memory group member service for current runtime behavior
- Add a minimal `/groups/{group_id}/members` API surface

Pros:
- Proves the contract end-to-end now
- Fits the current in-memory user baseline
- Keeps future DB migration possible without blocking `M4.2.3`

Cons:
- Runtime membership state remains transient for now

## Recommended Design

Choose **Option C**.

This keeps the milestone small and testable while respecting the current architecture. The SQLAlchemy model establishes the intended persistence shape, while the in-memory service avoids premature DB migration and integrates cleanly with the existing auth flow.

## Data Contract

### Model

Add `domain/models/group_member.py`:

- `group_jid: str` — composite primary key
- `user_id: str` — composite primary key
- `role: str` — one of `owner`, `admin`, `member`
- `joined_at: datetime` — defaults to `datetime.utcnow`

`group_jid` intentionally follows the TODO example and current chat/group naming convention. Route and schema payloads may continue using `group_id` while mapping directly to the same underlying value.

### Schemas

Add to `domain/schemas.py`:

- `CreateGroupMemberRequest`
  - `user_id: str`
  - `role: str = "member"`
- `GroupMemberResponse`
  - `group_id: str`
  - `user_id: str`
  - `role: str`
  - `joined_at: datetime`
- `GroupMemberListResponse`
  - `members: list[GroupMemberResponse]`

## Service Contract

Add `services/group_member_service.py` with a singleton service that stores memberships in memory.

### Public methods

- `list_members(group_id: str) -> list[GroupMember]`
- `add_member(group_id: str, user_id: str, role: str) -> GroupMember`
- `remove_member(group_id: str, user_id: str) -> bool`
- `get_member(group_id: str, user_id: str) -> GroupMember | None`
- `get_member_role(group_id: str, user_id: str) -> str | None`
- `reset() -> None`

### Runtime rules

- Role must be one of `owner`, `admin`, `member`
- Re-adding an existing member updates the stored role and preserves the original `joined_at`
- Removing a missing member returns `False`
- Returned member lists are deterministically sorted by `user_id`

## API Behavior

Add the following under `app/routes/groups.py`:

- `GET /groups/{group_id}/members`
- `POST /groups/{group_id}/members`
- `DELETE /groups/{group_id}/members/{user_id}`

### Authorization

- `GET` depends on `require_permission("groups", "read")`
- `POST` depends on `require_permission("groups", "write")`
- `DELETE` depends on `require_permission("groups", "write")`

### Membership rules

- `GET`: caller must also already be a member of the target group
- `POST`: caller must be the `owner` member of the target group
- `DELETE`: caller must be the `owner` member of the target group
- Group-level `admin` is stored as data but does not gain special management powers in this milestone
- Owners cannot remove themselves in this milestone; keep the only owner stable

### Error behavior

- Non-members attempting `GET` receive `403`
- Non-owners attempting `POST` / `DELETE` receive `403`
- Invalid role payload receives `400`
- Removing a missing member receives `404`
- Preventing owner self-removal receives `400`

## Testing Strategy

### Domain model tests

- `group_members` table is registered in shared metadata
- Composite primary key fields exist
- `role` and `joined_at` columns have the expected nullability/default contract

### Service tests

- Add member with default role
- Update existing member role without changing `joined_at`
- List members in stable order
- Reject unsupported roles
- Remove member and report missing member accurately
- Resolve group member role for authorization checks

### API tests

- Auth is still required
- A group member can list members
- Non-member cannot list members
- Group owner can add member
- Group owner can remove member
- Group admin/member cannot manage members
- Invalid role and missing member cases are surfaced correctly

## Files

- Create: `domain/models/group_member.py`
- Modify: `domain/models/__init__.py`
- Modify: `domain/schemas.py`
- Create: `services/group_member_service.py`
- Modify: `app/routes/groups.py`
- Modify: `tests/domain/models/test_models.py`
- Create: `tests/services/test_group_member_service.py`
- Modify: `tests/app/routes/test_api_routes.py`
- Modify: `docs/progress.md`
- Modify: `docs/TODO.md`
