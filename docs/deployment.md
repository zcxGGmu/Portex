# Deployment Guide

This guide documents the current Portex deployment story as it exists today:

- a verified local process setup for the FastAPI backend, SQLite database, and Vite-built frontend
- a Docker Compose draft that is useful as a starting point, but is not verified in the current environment

Portex is still in a milestone-driven refactor stage. Treat this document as an operator runbook for the current repository, not as a production-hardening manual.

## What This Guide Covers

- prerequisites and required local tooling
- runtime environment variables
- verified local process deployment steps
- basic post-start verification
- current data and persistence locations
- an unverified Docker Compose draft
- current deployment boundaries

## Prerequisites

- Linux or macOS shell environment with a writable checkout of this repository
- Python `3.11`
- Node.js `20+`
- `npm`
- a writable `data/` directory under the repository root

Optional:

- OpenAI-compatible provider credentials when you want to run real provider checks or provider-backed PoCs
- Docker daemon access if you want to experiment with the draft Compose section

## Environment Variables

### Core Runtime

- `DATABASE_URL`
  - Optional.
  - Default: `sqlite+aiosqlite:///./data/portex.db`
  - Override this when you want the backend to use a different SQLite file.
- `PORTEX_AUTH_SECRET`
  - Optional but strongly recommended outside local development.
  - Default: `portex-dev-secret`
  - Controls JWT signing for the current in-memory auth service.
- `PORTEX_AUTH_ALGORITHM`
  - Optional.
  - Default: `HS256`
- `PORTEX_AUTH_ACCESS_TOKEN_EXPIRE_HOURS`
  - Optional.
  - Default: `24`

### Optional OpenAI-Compatible Provider

These are not required just to boot the backend and frontend. Use them only when you need real provider-backed checks.

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_DEFAULT_MODEL`
  - The repository guidance currently assumes `gpt-5.1` for the tested compatible-provider setup.
- `OPENAI_AGENTS_DISABLE_TRACING`
  - The current docs use `1` in local provider sanity checks.

## Local Process Deployment (Verified)

### 1. Prepare the backend environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Initialize the database

```bash
.venv/bin/python scripts/init_db.py
```

This creates the current SQLAlchemy metadata in the configured database. With the default `DATABASE_URL`, the SQLite file lives at `./data/portex.db`.

### 3. Start the backend

```bash
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Notes:

- `uvicorn.ini` also records the default app target and port.
- The current verified flow is a single-process `uvicorn` run. Process supervisors, reverse proxies, and TLS termination are outside the current milestone scope.

### 4. Build and start the frontend

Install dependencies:

```bash
cd web
npm ci
```

Build static assets:

```bash
npm run build
```

For a minimal local full-stack run, start Vite preview:

```bash
npm run preview -- --host 0.0.0.0 --port 4173
```

Notes:

- `npm run preview` is the simplest repository-local way to serve the built frontend, but it is not a production-grade static hosting recommendation.
- If you already have your own static hosting or reverse proxy layer, serve `web/dist/` there instead.

### 5. Default URLs

- Backend HTTP API: `http://127.0.0.1:8000`
- FastAPI Swagger UI: `http://127.0.0.1:8000/docs`
- Frontend preview: `http://127.0.0.1:4173`

## Basic Verification

After starting the backend and frontend:

1. Check backend health:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","version":"0.1.0"}
```

2. Open `http://127.0.0.1:8000/docs` and confirm the HTTP API reference loads.
3. Open `http://127.0.0.1:4173` and confirm the frontend loads.
4. Optional repo-level verification:

```bash
.venv/bin/pytest -o addopts='' -q
.venv/bin/ruff check .
cd web && npm run lint
cd web && npm run build
```

## Data and Persistence Notes

Current runtime data lives under `data/`:

- `data/portex.db`
  - Default SQLite database file
- `data/memory/`
  - File-backed user and group memory
- `data/ipc/`
  - IPC directories used by the current runner flow
- `data/sessions/`
  - Session-related runtime data

Important current boundaries:

- Several user, task, log, and memory capabilities still rely on in-memory or file-backed minimal implementations.
- Task execution state and logs do not yet provide durable process-restart recovery.
- The IM delivery chain and WebSocket run flow are still intentionally incremental.

## Docker Release Image And Compose Draft (Not Yet Verified)

The repository now includes a root-level release-image build path:

```bash
.venv/bin/python scripts/build_docker.py --tag portex:v1.0.0
```

This wraps the same root build intent as:

```bash
docker build -t portex:v1.0.0 .
```

Current boundaries still matter:

- the current environment does not have Docker daemon verification evidence
- the root `Dockerfile` covers the backend runtime image only
- the frontend production artifact is still produced separately via `cd web && npm run build`
- `container/agent-runner/Dockerfile` remains the runner-specific image definition, not the full release image

Use the following Compose file as a draft starting point only:

```yaml
services:
  backend:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - .:/app
    environment:
      DATABASE_URL: sqlite+aiosqlite:///./data/portex.db
      PORTEX_AUTH_SECRET: change-me
    command: >
      sh -lc "pip install -e '.[dev]' &&
              python scripts/init_db.py &&
              uvicorn app.main:app --host 0.0.0.0 --port 8000"
    ports:
      - "8000:8000"

  frontend:
    image: node:20
    working_dir: /app/web
    volumes:
      - .:/app
    command: >
      sh -lc "npm ci &&
              npm run build &&
              npm run preview -- --host 0.0.0.0 --port 4173"
    ports:
      - "4173:4173"
    depends_on:
      - backend
```

Treat this as a draft to adapt, not as a copy-paste production recipe.

## Current Deployment Boundaries

- No verified Docker or Docker Compose smoke test exists in the current environment.
- No documented reverse proxy, TLS, systemd, or container-orchestration setup exists yet.
- The GitHub Actions workflow has been validated with local equivalent commands, but remote runner execution evidence is still absent from this environment.
- FastAPI `/docs` now covers the HTTP API only; the WebSocket contract is still outside OpenAPI and must be understood from code/tests for now.
- Real provider-backed runtime validation still depends on external credentials and a compatible model endpoint.
