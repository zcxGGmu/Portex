# M6.4.2 Dependency Audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M6.4.2` by adding a repository-local `pip-audit` command, wiring it into backend CI, and documenting the new dependency-audit step without broadening the milestone beyond Python dependency auditing.

**Architecture:** Add a small Python wrapper in `scripts/` that runs `python -m pip_audit .` from the repo root. Add `pip-audit` to `.[dev]`, verify the wrapper with focused tests, then plug the command into the current backend workflow alongside the existing static security scan.

**Tech Stack:** Python 3.11+, pip-audit, pytest, GitHub Actions

---

### Task 1: Lock the dependency-audit entrypoint contract with failing tests

**Files:**
- Create: `tests/scripts/test_dependency_audit.py`
- Reference: `scripts/dependency_audit.py`

**Step 1: Write the failing test**

Add tests that prove:
- the script builds `python -m pip_audit .`
- `main()` returns the subprocess exit code unchanged

**Step 2: Run test to verify it fails**

Run:
- `.venv/bin/pytest tests/scripts/test_dependency_audit.py -q`

Expected: FAIL because `scripts/dependency_audit.py` does not exist yet.

### Task 2: Implement the minimal dependency-audit script

**Files:**
- Create: `scripts/dependency_audit.py`

**Step 1: Write minimal implementation**

Add:
- `PROJECT_ROOT`
- `build_dependency_audit_command()`
- `main()` that runs the command with `subprocess.run(..., check=False)` and returns the subprocess exit code

**Step 2: Run test to verify it passes**

Run:
- `.venv/bin/pytest tests/scripts/test_dependency_audit.py -q`

Expected: PASS

### Task 3: Add the tool to dev dependencies and run the real audit

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add dependency**

Add `pip-audit` to `[project.optional-dependencies].dev`.

**Step 2: Refresh local dev environment**

Run:
- `.venv/bin/python -m pip install -e ".[dev]"`

Expected: PASS

**Step 3: Run the real audit**

Run:
- `.venv/bin/python scripts/dependency_audit.py`

Expected:
- PASS if the current dependency graph is clean
- otherwise FAIL with concrete vulnerability evidence that must be addressed before the milestone is closed

### Task 4: Wire the audit into CI and repo-facing docs

**Files:**
- Modify: `.github/workflows/test.yml`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Step 1: Update CI**

Add:

```yaml
- name: Run backend dependency audit
  run: python scripts/dependency_audit.py
```

**Step 2: Update docs**

Add the local dependency-audit command near the existing `security_scan.py` command.

### Task 5: Run milestone verification and update handoff

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest tests/scripts/test_dependency_audit.py -q`
- `.venv/bin/python scripts/dependency_audit.py`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/pytest tests/ -v --cov`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

Expected: PASS

**Step 2: Update restart-oriented docs**

Record:
- `M6.4.2` completion summary
- exact audit evidence
- the boundary that this milestone covers Python dependency auditing only
- the next starting point `M6.4.3`

### Task 6: Commit the milestone

**Files:**
- Commit all approved `M6.4.2` changes

**Step 1: Commit**

Prepare a focused commit such as:
- `build(security): complete M6.4.2 dependency audit`
