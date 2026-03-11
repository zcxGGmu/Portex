# Portex

Portex is a multi-user remote AI agent service built with Python and the OpenAI Agents SDK.

## Current Status

Portex has completed `M0` through `M5`, plus `M6.1.1` unit tests, `M6.1.2` integration tests, `M6.1.3` CI workflow setup, `M6.2.1` README work, `M6.2.2` API documentation, `M6.2.3` deployment documentation, `M6.3.1` database indexes, `M6.3.2` connection pooling, `M6.3.3` user-memory caching, `M6.4.1` security scanning, `M6.4.2` dependency audit, `M6.4.3` security headers, and `M6.5.1` version planning. The current next step is `M6.5.2` release tag creation.

Implemented and verified slices include:

- FastAPI backend and React/Vite frontend skeleton
- streamed run / cancel flow over WebSocket
- OpenAI Agents runtime integration and agent-runner container slices
- container and host execution mode selection
- multi-user auth, RBAC, invite codes, group membership
- task scheduling, task CRUD, and in-memory task run logs
- file-backed memory management and runner memory tools
- Feishu and Telegram client foundations
- unified message schema and minimal message router
- repository-local backend security scan wired into CI
- repository-local backend dependency audit wired into CI
- minimal HTTP security headers on API responses and CORS preflight responses
- unit, integration, backend regression, frontend build/lint, and local CI workflow commands

## Features

- Web and WebSocket entrypoints for agent interaction
- OpenAI Agents SDK-based runtime integration
- Container and host execution modes
- Multi-user auth and RBAC
- Task scheduling and execution logging
- User-global and group-scoped memory files
- Feishu and Telegram integration foundations
- Unified message format and minimal cross-channel routing
- GitHub Actions test workflow for backend and frontend verification

## Quick Start

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
.venv/bin/python scripts/init_db.py
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend

```bash
cd web
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

After startup:

- backend: `http://127.0.0.1:8000`
- frontend: `http://127.0.0.1:5173`

## Development

Common commands:

```bash
# full backend regression
.venv/bin/pytest -o addopts='' -q

# focused unit suite
.venv/bin/pytest tests/unit/ -v

# focused integration suite
.venv/bin/pytest -o addopts='' tests/integration/test_api.py tests/integration/test_websocket.py -q

# backend security scan
.venv/bin/python scripts/security_scan.py

# backend dependency audit
.venv/bin/python scripts/dependency_audit.py

# backend lint
.venv/bin/ruff check .

# frontend lint and build
cd web && npm run lint
cd web && npm run build
```

Real provider sanity check for OpenAI-compatible endpoints:

```bash
OPENAI_API_KEY=... \
OPENAI_BASE_URL=... \
OPENAI_DEFAULT_MODEL=gpt-5.1 \
OPENAI_AGENTS_DISABLE_TRACING=1 \
.venv/bin/python pocs/streaming/main.py --input "请只回复：测试通过"
```

## Project Structure

- `app/`: FastAPI app, routes, middleware, WebSocket entrypoints
- `domain/`: schemas, permissions, and SQLAlchemy models
- `infra/`: database, runtime adapters, execution backends, IM clients
- `services/`: auth, scheduling, memory, routing, and orchestration services
- `container/agent-runner/`: runner-side execution and tool wrappers
- `web/`: React + Vite frontend
- `tests/`: app, domain, service, unit, integration, and runner tests
- `docs/`: plans, TODOs, progress, and restart handoff notes
- `scripts/`: helper scripts such as DB initialization and commit flow

## Architecture

At a high level, Portex is split into a FastAPI backend, a React frontend, and a Python agent-runner container slice. The backend handles HTTP/WebSocket traffic, user/auth flows, task and memory orchestration, and IM/web routing boundaries. The runner and execution layers host the actual agent tooling and isolate execution via container or host-mode adapters.

The current message and runtime flow is intentionally incremental:

- WebSocket requests enter through `app/routes/websocket.py`
- runtime events are forwarded through `services/agent_trigger.py`
- Feishu and Telegram currently normalize platform payloads into shared DTOs
- `UnifiedMessage` and `MessageRouter` provide a minimal routing boundary, not a complete production delivery chain

## Current Boundaries

Portex is not yet a full production-ready system. Important current boundaries:

- many user, task, log, and memory capabilities still use in-memory or file-backed minimal implementations
- Feishu and Telegram slices cover auth/parsing/conversion/minimal send contracts, but the full production IM runtime chain is not yet wired end-to-end
- `app/routes/messages.py` and the WebSocket message flow do not yet represent a fully connected cross-platform delivery pipeline
- Docker lifecycle code exists, but the current local environment has not provided Docker daemon smoke-test evidence
- the Python dependency audit currently ignores `CVE-2024-23342` for `ecdsa` because `0.19.1` is still the newest published version; that exception must be revisited when the dependency graph or upstream releases change
- the current security-header layer is intentionally minimal and stops before CSP, HSTS, TLS, or reverse-proxy hardening
- the planned first formal release is `v1.0.0`, but the repository/package/runtime version strings still remain `0.1.0` until the later tag/release execution phases
- the GitHub Actions workflow has been configured and validated with local equivalent commands, but not observed running on a remote GitHub-hosted runner from this environment

## Documents

- [`docs/TODO.md`](docs/TODO.md): task-by-task implementation checklist
- [`docs/progress.md`](docs/progress.md): restart-oriented current status and next step
- [`docs/PORTEX_PLAN.md`](docs/PORTEX_PLAN.md): broader project planning context
- [`docs/deployment.md`](docs/deployment.md): current deployment guide for verified local process setup plus draft Compose notes
- [`AGENTS.md`](AGENTS.md): repository workflow and operator constraints for Codex sessions
