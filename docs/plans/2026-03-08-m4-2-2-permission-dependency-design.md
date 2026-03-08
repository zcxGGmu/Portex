# M4.2.2 Permission Dependency Design

## Goal

Complete `M4.2.2` by adding a reusable FastAPI permission dependency that evaluates the current user's `role` against `domain/permissions.py` static templates.

## Scope

- Add `require_permission(resource, action)` in `app/middleware/auth.py`
- Reuse `get_current_user()` for authentication
- Reuse `domain.permissions.has_permission()` for authorization
- Migrate current user-management admin routes in `app/routes/users.py` from role equality checks to permission checks
- Add focused middleware and API tests proving the new behavior

## Out of Scope

- Do not enable `user.permissions` custom overrides
- Do not add DB-backed permission lookup
- Do not expand invite codes into permission carriers
- Do not introduce new resources such as `invites`
- Do not change disabled/deleted user auth behavior in this step

## Design Options

### Option A: Add dependency only
- Add `require_permission()` and test it directly
- Leave existing `/admin/*` routes on `require_role("admin")`
- Lowest risk, but the feature is not exercised by real API wiring

### Option B: Add dependency and migrate current admin user routes
- Add `require_permission()` and migrate the existing `/admin/users` and `/admin/invites` routes
- Map current route needs onto the existing `users` resource:
  - `GET /admin/users` -> `users:read`
  - `PATCH /admin/users/{user_id}` -> `users:write`
  - `GET /admin/invites` -> `users:read`
  - `POST /admin/invites` -> `users:write`
- Keeps the change within the current permission template contract while proving the dependency works end-to-end

### Option C: Expand permission model now
- Introduce an `invites` resource or custom permission overrides immediately
- Better semantic granularity, but exceeds the agreed `M4.2.2` boundary

## Recommended Design

Choose **Option B**.

It keeps the implementation within the existing `owner/admin/member` static template model, avoids premature RBAC expansion, and produces visible API-level behavior changes that distinguish permission checks from the old `role == "admin"` guard.

## Data Flow

1. Route depends on `require_permission(resource, action)`
2. `require_permission()` resolves `current_user` through `get_current_user()`
3. The dependency checks `has_permission(current_user.role, resource, action)`
4. If denied, it raises `HTTPException(status_code=403, detail="permission denied")`
5. If allowed, it returns the authenticated `AuthUser`

## Route Mapping

- `GET /users/me`: unchanged, still uses `get_current_user`
- `GET /admin/users`: `users/read`
- `PATCH /admin/users/{user_id}`: `users/write`
- `GET /admin/invites`: `users/read`
- `POST /admin/invites`: `users/write`

## Compatibility Notes

- This intentionally widens access from only `admin` to any role whose template allows the target action; currently that means `owner` gains access to these routes
- Unknown roles still deny by default because `domain/permissions.py` returns no permissions
- Invite `permission_template` remains metadata only and does not affect authorization in this milestone

## Testing Strategy

### Middleware tests
- Allow `admin` for `users/read`
- Allow `owner` for `users/write`
- Deny `member` for `users/read`
- Deny unknown role for `users/read`

### API tests
- Existing unauthenticated and member-forbidden tests should still pass
- Add `owner` success coverage for at least one `/admin/*` route to prove the new dependency is wired
- Add unknown-role forbidden coverage for one `/admin/*` route to prove default deny behavior

## Files

- Modify `app/middleware/auth.py`
- Modify `app/middleware/__init__.py`
- Modify `app/routes/users.py`
- Modify `tests/app/middleware/test_auth_middleware.py`
- Modify `tests/app/routes/test_api_routes.py`
- Modify `docs/progress.md`
