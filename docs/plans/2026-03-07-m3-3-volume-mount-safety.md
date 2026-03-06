# M3.3 Volume Mount Safety Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M3.3.1` ~ `M3.3.3` by adding a deterministic Docker volume builder, path allowlist validation, and explicit read-only mount helpers for the execution layer.

**Architecture:** Keep mount orchestration inside `infra/exec/docker.py`, but move generic path validation into `infra/exec/security.py` so later container mode and host mode can reuse the same safety primitive. Build volumes from a repo-local `data/` root, validate every resolved path stays under its allowed root, and expose a small `build_readonly_volume()` helper so sensitive mounts like skills/config can default to `ro` without duplicating Docker SDK dict syntax.

**Tech Stack:** Python 3.11, pathlib, pytest, monkeypatch

---

### Task 1: Define mount and security behavior with failing tests

**Files:**
- Modify: `tests/infra/exec/test_docker.py`
- Create: `tests/infra/exec/test_security.py`
- Reference: `infra/exec/docker.py`
- Reference: `infra/exec/security.py`

**Step 1: Write failing tests**

Cover:
- `validate_path()` accepting nested paths under allowed roots and rejecting escapes
- `build_readonly_volume()` emitting Docker SDK mount syntax with `mode="ro"`
- `build_volumes()` creating sessions / memory / ipc / group / skills mounts under `data/`
- `build_volumes()` forcing skills to read-only by default
- `build_volumes()` rejecting traversal attempts in `group_folder` / `user_id`
- optional read-only overrides for other mount groups

**Step 2: Run focused tests to verify RED**

Run: `.venv/bin/pytest tests/infra/exec/test_docker.py tests/infra/exec/test_security.py -q`
Expected: FAIL because the current execution layer has no mount builder or security module.

### Task 2: Implement path validation and volume helpers

**Files:**
- Create: `infra/exec/security.py`
- Modify: `infra/exec/docker.py`
- Modify: `infra/exec/__init__.py`

**Step 1: Add security primitives**

Implement a small `validate_path()` helper that resolves symlinks and checks containment within allowed roots.

**Step 2: Add mount builders**

Implement:
- `build_volume()`
- `build_readonly_volume()`
- `build_volumes()`

Ensure the builder creates repo-local directories as needed and validates each resolved host path before emitting Docker SDK volume mappings.

**Step 3: Run focused tests to verify GREEN**

Run: `.venv/bin/pytest tests/infra/exec/test_docker.py tests/infra/exec/test_security.py -q`
Expected: PASS.

### Task 3: Regressions, docs, and commit

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/progress.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest tests/infra/exec/test_docker.py tests/infra/exec/test_security.py -q`
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

**Step 2: Update docs**

Record `M3.3` completion, exact verification evidence, and the next start point.

**Step 3: Commit**

Commit with a focused `feat(exec): ...` message after the workspace is cleanly verified.
