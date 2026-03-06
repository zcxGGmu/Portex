# M3.2 Agent Runner Containerization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M3.2.1` ~ `M3.2.3` by replacing the placeholder `container/agent-runner` package with a test-covered Docker image definition, JSON input/output protocol, and a real OpenAI Agents SDK runner entrypoint.

**Architecture:** Keep the container package self-contained: a `Dockerfile` prepares the runtime image, `src/types.py` defines the host/container protocol, and `src/runner.py` reads JSON from stdin, validates input, runs a minimal `Agent` via `Runner.run_sync`, and writes a structured JSON result to stdout. Use unit tests with monkeypatched `Agent`/`Runner` to avoid real model providers or network calls, and use static file assertions for the Dockerfile because the current environment has no Docker daemon.

**Tech Stack:** Python 3.11, Dockerfile, OpenAI Agents SDK, Pydantic v2, pytest, monkeypatch

---

### Task 1: Define the runner protocol with failing tests

**Files:**
- Create: `tests/container/agent_runner/test_runner.py`
- Create: `tests/container/agent_runner/test_container_files.py`
- Reference: `container/agent-runner/src/runner.py`
- Reference: `container/agent-runner/src/types.py`
- Reference: `container/agent-runner/Dockerfile`

**Step 1: Write failing tests**

Cover:
- `ContainerInput` / `ContainerOutput` defaults and validation
- `run_agent()` building an `Agent`, calling `Runner.run_sync`, and returning success output
- `run_agent()` converting runtime exceptions into error output
- `main()` reading stdin JSON and writing stdout JSON
- `Dockerfile` containing the required base image, system packages, non-root user, and runner entrypoint

**Step 2: Run focused tests to verify RED**

Run: `.venv/bin/pytest tests/container/agent_runner/test_runner.py tests/container/agent_runner/test_container_files.py -q`
Expected: FAIL because the current runner and Dockerfile are placeholders.

### Task 2: Implement the container protocol and runner entrypoint

**Files:**
- Create: `container/agent-runner/src/types.py`
- Modify: `container/agent-runner/src/runner.py`
- Modify: `container/agent-runner/src/__init__.py`
- Modify: `container/agent-runner/pyproject.toml`

**Step 1: Implement protocol models**

Add Pydantic models for the JSON boundary with explicit defaults and narrow status values.

**Step 2: Replace the placeholder runner**

Implement a testable runner flow that:
- reads stdin JSON
- validates it with `ContainerInput`
- builds a minimal `Agent`
- calls `Runner.run_sync`
- returns `ContainerOutput(status=\"success\", result=...)`
- converts exceptions into `ContainerOutput(status=\"error\", error=...)`

**Step 3: Run focused tests to verify GREEN**

Run: `.venv/bin/pytest tests/container/agent_runner/test_runner.py tests/container/agent_runner/test_container_files.py -q`
Expected: PASS.

### Task 3: Finalize Docker image scaffold, verify, and document

**Files:**
- Modify: `container/agent-runner/Dockerfile`
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`

**Step 1: Replace the Dockerfile placeholder**

Add:
- `python:3.11-slim`
- required system packages for `M3.2.1`
- package install for `container/agent-runner`
- non-root `portex` user
- `ENTRYPOINT ["python", "-m", "src.runner"]`

**Step 2: Run verification**

Run:
- `.venv/bin/pytest tests/container/agent_runner/test_runner.py tests/container/agent_runner/test_container_files.py -q`
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

If Docker remains unavailable locally, record that the image definition is verified statically rather than via `docker build`.

**Step 3: Update docs and commit**

Record `M3.2` completion in `docs/TODO.md` / `docs/progress.md`, then commit with a focused message.
