# M6.5.3 Release Artifacts Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Advance `M6.5.3` by adding a repository-root Docker release-image build path, preserving the existing frontend production artifact flow, and documenting any remaining environment blocker around real Docker execution.

**Architecture:** Add a root backend runtime `Dockerfile` plus `.dockerignore`, and replace the placeholder `scripts/build_docker.py` with a thin command wrapper that defaults to `docker build -t portex:v1.0.0 .` while still supporting the runner image via explicit `--file/--context` overrides. Verify the new artifact path with static tests and real frontend builds; if the environment still lacks Docker, record that limitation explicitly instead of fabricating a successful image build.

**Tech Stack:** Dockerfile, Python 3.11, argparse, subprocess, pytest, npm/Vite

---

### Task 1: Lock the release-artifact contract with tests

**Files:**
- Create: `tests/scripts/test_build_docker.py`
- Modify: `tests/container/agent_runner/test_container_files.py`
- Reference: `scripts/build_docker.py`

**Step 1: Write the failing tests**

Add tests that prove:
- `scripts/build_docker.py` builds the default command `docker build -t portex:v1.0.0 .`
- the script supports explicit `--file` and `--context` overrides for the runner image path
- the root `Dockerfile` contains the required backend-runtime scaffold
- `.dockerignore` excludes common heavyweight or local-only paths

**Step 2: Run tests to verify they fail**

Run:
- `.venv/bin/pytest tests/scripts/test_build_docker.py tests/container/agent_runner/test_container_files.py -q`

Expected: FAIL because the wrapper is still a placeholder and the root Docker build files do not exist yet.

### Task 2: Implement the root Docker artifact path

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Modify: `scripts/build_docker.py`
- Modify: `Makefile`

**Step 1: Write minimal implementation**

Add:
- a root backend runtime Dockerfile
- a `.dockerignore` for `.git`, `.venv`, `web/node_modules`, `web/dist`, `data`, and other local-only artifacts
- a real `scripts/build_docker.py` with command builder + subprocess execution
- a `Makefile` target for the release image while preserving the runner-image path through explicit overrides

**Step 2: Run tests to verify they pass**

Run:
- `.venv/bin/pytest tests/scripts/test_build_docker.py tests/container/agent_runner/test_container_files.py -q`

Expected: PASS

### Task 3: Update docs for the new artifact path

**Files:**
- Modify: `README.md`
- Modify: `docs/deployment.md`
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Update operator docs**

Record:
- the new root image build entrypoint
- the separate frontend `web/dist/` artifact
- the fact that local Docker-runtime verification still depends on a machine with `docker`

### Task 4: Run milestone verification

**Files:**
- Verify repository state only; no additional source files expected

**Step 1: Run static and regression verification**

Run:
- `git diff --check`
- `.venv/bin/pytest tests/scripts/test_build_docker.py tests/container/agent_runner/test_container_files.py -q`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`
- `test -f web/dist/index.html`

Expected: PASS

**Step 2: Attempt real Docker verification**

Run:
- `docker version --format '{{.Client.Version}}|{{.Server.Version}}'`
- `docker build -t portex:v1.0.0 .`
- `docker image inspect portex:v1.0.0 --format '{{.Id}}'`

Expected:
- if Docker is available, PASS and record image evidence
- if Docker is unavailable, record the exact blocker output and stop short of claiming full runtime-verified completion

### Task 5: Commit the phase result

**Files:**
- Commit all approved `M6.5.3` changes

**Step 1: Commit**

Prepare a focused commit such as:
- `build(release): add root artifact build path`
