# M6.4.1 Security Scanning Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete `M6.4.1` by adding a repository-local security scan command that runs in the current environment, passes on the current runtime codebase, and is wired into CI and handoff docs.

**Architecture:** Add a small Python wrapper under `scripts/` that runs Ruff's `S` rules against the repository's runtime-oriented Python directories. Keep dependency auditing out of this milestone, fix the two real runtime findings in `domain/schemas.py`, and use one narrow inline suppression for the `EventType.TOKEN_DELTA` false positive.

**Tech Stack:** Python 3.11+, Ruff, pytest, GitHub Actions

---

### Task 1: Lock the scan entrypoint contract with failing tests

**Files:**
- Create: `tests/scripts/test_security_scan.py`
- Reference: `scripts/security_scan.py`

**Step 1: Write the failing test**

Add tests that prove:
- the script builds `python -m ruff check --select S ...` with the expected target directories
- `main()` returns the subprocess exit code unchanged

Example test shape:

```python
def test_build_security_scan_command_uses_expected_targets() -> None:
    command = build_security_scan_command()
    assert command[:5] == [sys.executable, "-m", "ruff", "check", "--select"]
    assert command[5] == "S"
    assert command[6:] == list(SECURITY_SCAN_TARGETS)
```

**Step 2: Run test to verify it fails**

Run:
- `.venv/bin/pytest tests/scripts/test_security_scan.py -q`

Expected: FAIL because `scripts/security_scan.py` does not exist yet.

### Task 2: Implement the scan entrypoint

**Files:**
- Create: `scripts/security_scan.py`

**Step 1: Write minimal implementation**

Add:
- `SECURITY_SCAN_TARGETS` as a tuple of repository-relative runtime paths
- `build_security_scan_command()` returning the Ruff CLI command
- `main()` calling `subprocess.run(...).returncode`

Example implementation shape:

```python
SECURITY_SCAN_TARGETS = ("app", "domain", "infra", "services")

def build_security_scan_command() -> list[str]:
    return [sys.executable, "-m", "ruff", "check", "--select", "S", *SECURITY_SCAN_TARGETS]
```

**Step 2: Run test to verify it passes**

Run:
- `.venv/bin/pytest tests/scripts/test_security_scan.py -q`

Expected: PASS

### Task 3: Make the current runtime scan pass

**Files:**
- Modify: `domain/schemas.py`
- Modify: `portex/contracts/events.py`

**Step 1: Replace the `assert`-based checks**

Turn the two validator assertions into explicit checks that raise a concrete exception if normalization unexpectedly returns `None`.

**Step 2: Add the narrow false-positive suppression**

Keep the `TOKEN_DELTA` event contract unchanged and add an inline Ruff suppression on that enum value only.

**Step 3: Run the real scan**

Run:
- `.venv/bin/python scripts/security_scan.py`

Expected: PASS

### Task 4: Wire the command into CI and repo-facing docs

**Files:**
- Modify: `.github/workflows/test.yml`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Step 1: Update CI**

Add a backend step:

```yaml
- name: Run backend security scan
  run: python scripts/security_scan.py
```

**Step 2: Update docs**

Add the new local command to the development command sections and refresh any stale milestone wording that still points at `M6.3`.

**Step 3: Sanity-check doc references**

Run:
- `git diff --check`

Expected: PASS

### Task 5: Run milestone verification and update handoff

**Files:**
- Modify: `docs/progress.md`
- Modify: `tasks/todo.md`

**Step 1: Run verification**

Run:
- `.venv/bin/pytest tests/scripts/test_security_scan.py -q`
- `.venv/bin/python scripts/security_scan.py`
- `.venv/bin/pytest -o addopts='' -q`
- `.venv/bin/ruff check .`
- `cd web && npm run lint`
- `cd web && npm run build`

Expected: PASS

**Step 2: Update restart-oriented docs**

Record:
- `M6.4.1` completion summary
- exact verification evidence
- the boundary that this milestone is static code scanning only
- the next starting point `M6.4.2`

### Task 6: Commit the milestone

**Files:**
- Commit all approved `M6.4.1` changes

**Step 1: Commit**

Prepare a focused commit such as:
- `build(security): complete M6.4.1 security scan`
