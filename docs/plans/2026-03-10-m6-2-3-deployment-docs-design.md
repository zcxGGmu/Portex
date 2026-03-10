# M6.2.3 Deployment Docs Design

## Goal

Complete `M6.2.3` by adding a practical deployment guide that documents the currently verified local process deployment path, plus a clearly marked Docker Compose draft, without overstating the repository's current runtime maturity.

## Scope

- add a dedicated deployment guide in Markdown
- document the currently verified local process deployment path for backend, frontend, and SQLite
- include the required runtime prerequisites, environment variables, startup commands, verification steps, and persistence notes
- include a clearly labeled Docker Compose draft section that is not presented as verified
- fix the newly discovered `invite.expires_at` API-doc wording mismatch before using the docs as deployment reference material
- fix `scripts/init_db.py` so the documented direct execution command actually works from the repository root

## Out of Scope

- do not implement real Docker Compose files or deployment automation
- do not claim validated Docker deployment evidence
- do not add Kubernetes, systemd, Nginx, TLS, reverse-proxy, or production hardening playbooks
- do not expand into a full operator handbook or documentation site
- do not change runtime architecture, CI scope, or IM delivery behavior

## Design Constraints

- the mainline deployment path must be limited to commands already supported by the repository
- wording must stay aligned with `docs/progress.md`, especially around Docker, CI, WebSocket coverage, and IM/runtime boundaries
- Compose content must be useful as a starting point but explicitly marked as unverified in the current environment
- deployment guidance should fit the existing docs layering:
  - `README.md`: repository entrypoint
  - FastAPI `/docs`: HTTP API reference
  - deployment guide: operator-oriented setup and startup steps

## Options Considered

### Option A: Local process deployment only

- document Python backend + Vite frontend + SQLite
- omit Docker entirely

Pros:
- fully aligned with current verified evidence

Cons:
- diverges from the TODO direction that already sketches Docker Compose
- leaves container-oriented operators without even a draft starting point

### Option B: Verified local deployment plus unverified Compose draft

- lead with local process deployment
- add a separate "draft / not yet verified" Compose section

Pros:
- matches what is actually validated today
- still satisfies the TODO's deployment-doc intent
- keeps risk visible instead of hiding it

Cons:
- requires careful wording to avoid sounding production-ready

### Option C: Docker-first deployment guide

- center the guide on Docker Compose
- mention local process deployment as fallback

Pros:
- looks closer to a future productized deployment story

Cons:
- not supportable with current evidence
- would overstate Docker readiness because the daemon is unavailable in the current environment

## Recommended Design

Choose **Option B**.

## Proposed Structure

### `# Deployment Guide`

- one-paragraph scope and current maturity note

### `## What This Guide Covers`

- verified local deployment
- unverified Compose draft
- current limitations

### `## Prerequisites`

- Python 3.11
- Node.js 20+
- npm
- writable `data/` directory
- optional OpenAI-compatible provider environment variables

### `## Environment Variables`

- `DATABASE_URL`
- `PORTEX_AUTH_SECRET`
- optional OpenAI-compatible provider variables
- optional auth token lifetime knobs if already supported

### `## Local Process Deployment (Verified)`

- create virtualenv
- install backend deps
- initialize DB
- run backend with `uvicorn`
- install frontend deps
- run or build frontend
- explain default URLs and persistence path

### `## Basic Verification`

- health check
- open `/docs`
- open frontend
- run a minimal backend/frontend verification command set

### `## Data and Persistence Notes`

- SQLite path
- `data/` directories
- current in-memory/file-backed boundaries

### `## Docker Compose Draft (Not Yet Verified)`

- clearly marked warning
- minimal sample Compose YAML
- note that root service image/build flow is not yet validated in this repo
- point out that `container/agent-runner/Dockerfile` exists but full system Compose is still draft-only

### `## Current Deployment Boundaries`

- Docker daemon unverified
- no reverse proxy / TLS / supervisor guidance
- no remote GitHub Actions proof
- WebSocket/API runtime chain and IM chain remain incremental

## Precondition Fix

Before publishing the deployment guide:

- correct the inaccurate API-doc claim that invite `expires_at` is always returned in UTC; the current service preserves provided offsets, so the schema wording must describe timezone-aware datetimes without promising UTC normalization
- make `scripts/init_db.py` runnable via the documented direct command from the repository root, because the current deployment instructions depend on it

## Testing Strategy

- add or extend tests for the invite `expires_at` documentation contract so the wording fix is locked
- add or extend tests for `scripts/init_db.py` direct execution so the deployment command is real, not aspirational
- verify deployment-doc text against current commands and environment variables in the repository
- run focused tests for the corrected API-doc slice
- run full backend regression, `ruff`, and frontend `lint/build`

## Expected Deliverables

- a new deployment guide that an operator can follow for the currently supported local setup
- explicit documentation of what is draft-only versus verified
- corrected invite `expires_at` API-doc wording
- updated `README.md`, `docs/progress.md`, and `tasks/todo.md` pointing to the deployment guide and the next milestone
