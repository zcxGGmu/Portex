# M3.1 Docker SDK Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M3.1` by replacing the placeholder Docker executor with a tested Docker SDK wrapper that exposes the minimum container lifecycle operations Portex needs for upcoming runner containerization work.

**Architecture:** Keep the `infra/exec/docker.py` boundary intentionally thin: one config object, one exception type, and a small wrapper around a Docker SDK client factory. The wrapper should support environment-derived clients, list/get/run/stop/wait/logs/remove operations, and normalize Docker SDK errors into deterministic Portex-level failures so later service layers can choose container or host execution cleanly.

**Tech Stack:** Python 3.11, Docker SDK for Python, pytest, monkeypatch/mocks

---

### Task 1: Add failing tests for the Docker execution boundary

**Files:**
- Create: `tests/infra/exec/test_docker.py`
- Reference: `infra/exec/docker.py`
- Reference: `docs/TODO.md`

**Step 1: Write failing tests**

Add tests that cover:
- default client construction via `docker.from_env()`
- `list_containers()` forwarding `all` filter
- `get_container()` forwarding names and wrapping not-found/API errors
- `run_container()` forwarding image, command, volumes, environment, name, detach/remove and optional working dir
- `stop_container()`, `wait_container()`, `get_logs()`, `remove_container()` behavior and error wrapping
- config-driven constructor behavior when a custom client factory is injected

**Step 2: Run the focused test file and confirm RED**

Run: `.venv/bin/pytest tests/infra/exec/test_docker.py -q`
Expected: fail because current implementation is only a placeholder.

**Step 3: Commit**

No commit yet; combine with implementation once green.

### Task 2: Implement the Docker SDK wrapper

**Files:**
- Modify: `infra/exec/docker.py`
- Modify: `infra/exec/__init__.py`

**Step 1: Write minimal implementation**

Implement:
- `DockerExecutionError`
- `DockerExecutorConfig`
- `DockerExecutor` with a lazily initialized client and methods:
  - `list_containers(all: bool = False)`
  - `get_container(name: str)`
  - `run_container(...)`
  - `stop_container(name: str, timeout: int | None = None)`
  - `wait_container(name: str)`
  - `get_logs(name: str, stdout: bool = True, stderr: bool = True, tail: str | int = "all")`
  - `remove_container(name: str, force: bool = False)`
- private error helper that converts Docker SDK exceptions into readable `DockerExecutionError`

**Step 2: Run the focused test file and confirm GREEN**

Run: `.venv/bin/pytest tests/infra/exec/test_docker.py -q`
Expected: all tests pass.

**Step 3: Refactor only if needed**

Keep the wrapper thin and explicit; avoid adding M3.2+ concerns such as image builds, mount validation, or mode selection.

### Task 3: Verify, document progress, and commit the phase task

**Files:**
- Modify: `docs/progress.md`

**Step 1: Run verification commands**

Run:
- `.venv/bin/pytest tests/infra/exec/test_docker.py -q`
- `.venv/bin/pytest tests/services/test_message_service.py tests/services/test_agent_trigger.py -q`
- `.venv/bin/pytest tests/app/routes/test_websocket_routes.py -q`
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check .`

**Step 2: Update restart notes**

Record:
- `M3.1` completion status and `M3.2` as the next start point
- exact verification evidence
- any environment caveat about real Docker daemon availability if tests stay mocked

**Step 3: Commit**

```bash
git add infra/exec/docker.py infra/exec/__init__.py tests/infra/exec/test_docker.py docs/progress.md docs/plans/2026-03-07-m3-1-docker-sdk-integration.md
git commit -m "feat(exec): complete M3.1 docker sdk wrapper"
```
