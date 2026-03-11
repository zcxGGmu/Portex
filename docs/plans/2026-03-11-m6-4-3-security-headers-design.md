# M6.4.3 Security Headers Design

## Goal

Complete `M6.4.3` by adding the smallest useful HTTP security-header middleware to the current FastAPI app without expanding into CSP or broader browser security policy work.

## Scope

- add `app/middleware/security.py`
- register the new middleware in `app/main.py`
- apply a minimal, low-risk set of security headers to HTTP responses
- keep WebSocket traffic untouched
- verify the headers through focused app-route and integration tests
- update restart-oriented docs after verification

## Out of Scope

- do not add Content-Security-Policy in this milestone
- do not add HSTS, HTTPS redirects, TLS termination, reverse-proxy config, or deployment hardening
- do not replace the existing `security_scan.py` or `dependency_audit.py` toolchains
- do not change auth flows, CORS policy, WebSocket behavior, or route logic beyond header decoration
- do not add frontend-specific browser policy negotiation or document-level CSP tuning

## Design Constraints

- `docs/TODO.md` points directly at `app/middleware/security.py`, but the snippet uses a non-existent `SecurityMiddleware`; the actual implementation must stay compatible with FastAPI/Starlette
- the repository now has explicit `M6.4.1` and `M6.4.2` security tooling, so `M6.4.3` should stay narrowly focused on runtime HTTP headers
- the chosen headers should be low-risk for the current API + Swagger UI + local frontend setup
- CORS preflight responses should receive the same security headers, so middleware ordering matters

## Options Considered

### Option A: Add a custom ASGI middleware for a minimal header set

Pros:
- small and explicit
- works with current FastAPI/Starlette stack
- can safely skip WebSocket traffic
- easy to verify with response-header tests

Cons:
- requires a small custom middleware implementation

### Option B: Introduce CSP now along with other headers

Pros:
- stronger browser-side policy surface

Cons:
- higher risk of breaking Swagger UI or the current frontend
- expands the milestone beyond the user-confirmed minimal boundary

### Option C: Use a third-party security middleware package

Pros:
- less custom code

Cons:
- new dependency for a very small behavior surface
- harder to keep the milestone minimal and explicit

## Recommended Design

Choose **Option A**.

## Proposed Changes

### Middleware behavior

- implement `SecurityHeadersMiddleware` as a lightweight ASGI middleware
- only intercept `http.response.start`
- use `MutableHeaders` to set default headers without overwriting route-specific values

### Minimal header set

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()`

This set keeps the milestone small, avoids CSP complexity, and does not depend on HTTPS-only deployment assumptions.

### App integration

- register the middleware in `app/main.py`
- place it so it wraps `CORSMiddleware`, allowing security headers to appear on preflight responses as well

### Testing strategy

- extend `tests/app/routes/test_api_routes.py` first to lock the expected header contract on `/health`
- add a second focused test proving CORS preflight responses also carry the security headers
- extend `tests/integration/test_api.py` with one lightweight integration assertion on `/health`

## Risks and Boundaries

- this milestone intentionally stops before CSP, so browser-side script policy remains unconstrained
- HSTS is omitted because the current verified deployment path still uses local plain HTTP
- if future routes need custom per-response header values, the middleware should continue using `setdefault`-style behavior rather than unconditional overwrite

## Expected Deliverables

- `app/middleware/security.py`
- middleware registration in `app/main.py`
- focused route/integration tests for the new headers
- updated `docs/progress.md` and `tasks/todo.md` moving the next step beyond `M6.4.3`
