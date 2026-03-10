# M6.2.2 API Docs Design

## Goal

Complete `M6.2.2` by making the existing FastAPI-generated `/docs` and `/openapi.json` useful for the current HTTP API surface without expanding into a separate API portal or a standalone Markdown reference.

## Scope

- enrich FastAPI app-level OpenAPI metadata
- add route-level summaries, descriptions, and documented error responses for the current HTTP routes
- add field descriptions and examples to the most important request and response schemas
- improve the documented response contract for group-member deletion
- verify the generated OpenAPI schema through tests

## Out of Scope

- do not create a separate API documentation site
- do not add a dedicated Markdown API manual
- do not document the WebSocket contract as part of the OpenAPI schema
- do not change business behavior, status-code semantics, or route shapes just to make the docs prettier
- do not start `M6.2.3` deployment documentation work

## Design Constraints

- keep `/docs` as the primary API documentation entrypoint
- keep all wording aligned with the current implementation and boundary notes in `docs/progress.md`
- avoid overstating runtime maturity, Docker verification, or IM delivery completeness
- keep the change minimal and documentation-focused

## Options Considered

### Option A: Pure app-level metadata only

- add `description` and `openapi_tags` on the FastAPI app

Pros:
- smallest code diff

Cons:
- endpoint-level docs remain thin
- important `400/401/403/404/409` contracts stay undocumented
- request semantics still require reading source

### Option B: FastAPI metadata plus route/schema enrichment

- add app-level metadata
- add route summaries, descriptions, and error responses
- add schema field descriptions/examples

Pros:
- keeps `/docs` as the single source of truth
- documents the current API surface with minimal scope creep
- matches the TODO wording and progress guidance

Cons:
- touches several route/schema files

### Option C: FastAPI metadata plus separate Markdown API guide

- enrich `/docs`
- add a hand-written `docs/api.md`

Pros:
- can explain WebSocket and operational notes

Cons:
- expands scope beyond the TODO wording
- duplicates information already available from OpenAPI
- starts drifting toward a docs portal

## Recommended Design

Choose **Option B**.

## Proposed Changes

### App-level OpenAPI metadata

- add a concise API description to `app/main.py`
- define `openapi_tags` so `/docs` shows stable grouped sections for `health`, `auth`, `users`, `admin`, `groups`, `messages`, and `tasks`
- explicitly state in the description that the current WebSocket entrypoint is not represented in OpenAPI

### Route-level documentation

- document request purpose and current boundaries on the main HTTP routes:
  - `app/routes/auth.py`
  - `app/routes/users.py`
  - `app/routes/groups.py`
  - `app/routes/messages.py`
  - `app/routes/tasks.py`
- add explicit `responses` metadata for the error codes already enforced by the implementation and tests
- avoid changing success status codes in this milestone

### Schema-level documentation

- add `description` and `examples` to the most important API DTO fields in `domain/schemas.py`
- focus on request models and the primary response shapes that benefit `/docs` the most
- add a small explicit response schema for group-member deletion so Swagger stops showing a generic object

## Testing Strategy

- add OpenAPI-focused tests against `/openapi.json`
- verify:
  - app description and tags are present
  - key routes expose documented error responses
  - key schemas expose field descriptions/examples
  - group-member deletion has a concrete response model
- then run focused API-route tests, full backend regression, `ruff`, and frontend `lint/build`

## Expected Deliverables

- `/docs` becomes a practical HTTP API entrypoint for the current Portex backend
- key route and schema semantics are visible without reading source code
- `docs/progress.md` and `tasks/todo.md` advance from `M6.2.2` to `M6.2.3`
